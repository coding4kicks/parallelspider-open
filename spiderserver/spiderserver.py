#!/usr/bin/env python

"""
    Spider Server - web server for Parallel Spider

    Authentication:
        Password Checker - Checks user provided password in Redis datastore
                         - TODO: need to hash and compare versus saved hashed
        Named User Avatar - Contains user name (possibly other user info)
        Spider Realm - a Twisted Realm

    Resources:
        CheckUserCredentials - Allows users to login and start sessions
        Sign Out - Removes session info from datastore
        Add New User -
        Password Reminder - 
        Initiate Crawl - Passes a crawl to the analysis engine
        Check Crawl Status - Monitors the progress of a crawl
        Get S3 Signature - Returns a signed S3 URL to access a crawl's results
        Get Analysis Folder - Returns the folders and analyses for a user

     TODO: Elaborate on failure codes
     TODO: Refactor analysis folder info to postgre 
        - so don't have to send entire datastructure accross wire on update

     Notes: All responses prefaced with:  )]}',\n
            Stripped by Angular and helps prevent CSRF
"""

import json
import uuid
import base64
import optparse
import datetime
import unicodedata

from twisted.web import resource, static, server
from zope.interface import Interface, implements
from twisted.internet import protocol, reactor, defer
from twisted.cred import portal, checkers, credentials, error as credError

import boto
import redis


# AUTHENTICATION
###############################################################################

class PasswordChecker(object):
    """Dict like object mapping usernames to passwords"""

    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, user_redis):
        """Only arg is Redis instance with user info."""

        self.user_redis = user_redis

    def requestAvatarId(self, credentials):
        username = credentials.username
        if self.user_redis.exists(username):
            if self.user_redis.get(username) == credentials.password:
                return defer.succeed(username)
            else:
                return defer.fail(
                    credError.UnauthorizedLogin("Bad password"))
        else:
            return defer.fail(
                credError.UnauthorizedLogin("No such user"))

class INamedUserAvatar(Interface):
    """ Should have attributes username and nickname """

class NamedUserAvatar(object):
    """User info"""

    implements(INamedUserAvatar)

    # username will be email (switch name to match)
    def __init__(self, username, nickname):
        self.username = username # login id (unique id used in system)
        self.nickname = nickname # nickname to display on welcome / forumn

class SpiderRealm(object):
    """
        Twisted Realm object

        Issue:
            For some reason must encode returned data as ascii string.
            Ramificatoins for Internationalization?
    """

    implements(portal.IRealm)

    def __init__(self, user_redis):
        """Only arg is Redis instance with user info."""

        self.user_redis = user_redis

    def requestAvatar(self, avatarId, mind, *interfaces):
        if INamedUserAvatar in interfaces:
            user_data = self.user_redis.get(avatarId + '_info')
            user_info = json.loads(user_data)
            nickname = user_info['nickname']
            # Must encode as string vice unicode, wtf!
            nickname = unicodedata.normalize('NFKD', nickname) \
                                  .encode('ascii','ignore')
            logout = lambda: None
            return (INamedUserAvatar, 
                    NamedUserAvatar(avatarId, nickname),
                    logout)
        else:
            raise KeyError("None of the requested interfaces are supported")


# RESOURCES
###############################################################################

class CheckUserCredentials(resource.Resource):
    """ Validate user's credentials for login """

    def __init__(self, portal, session_redis, expire):
        """Initialize Session Redis and Twisted Portal for Authentication"""
        self.portal = portal
        self.session_redis = session_redis
        self.longExpire = expire['longExpire']
        self.shortExpire = expire['shortExpire']

    def render(self, request):
        """
            Returns user id and session info if successful login
            
            Request:
                {'user': 'user id = email',
                 'password': 'users password'}
        """

        # Add headers to request prior to writing
        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS":
            return ""

        # Get json payload from post request
        data = json.loads(request.content.getvalue())

        creds = credentials.UsernamePassword(
                data['user'],
                data['password'])

        self.portal.login(creds, None, INamedUserAvatar).addCallback(
            self._loginSucceeded).addErrback(self._loginFailed)

        return server.NOT_DONE_YET
    
    def _loginSucceeded(self, avatarInfo):
        """
            Callback for successful login

            Generates, stores, and returns session tokens
        """

        avatarInterface, avatar, logout = avatarInfo

        # Short session token - for crawl purchases and changing user info
        short_session = uuid.uuid4().bytes.encode("base64")[:21]
        self.session_redis.set(short_session, 'ps_shortsession') 
        self.session_redis.expire(short_session, self.shortExpire)

        # Long session token - for user info and data analysis - longer expire
        u = uuid.uuid4().bytes.encode("base64")[:4]

        # Include nickname, id, and date for cookie reload and logging
        # TODO:  fix crawl id
        v = base64.b64encode(avatar.nickname + '///' + avatar.username + '///'
                + str(datetime.datetime.now))
        long_session = v + u
        self.session_redis.set(long_session, 'ps_longsession')
        self.session_redis.expire(long_session, self.longExpire)

    
        value = """)]}',\n{"login": "success", 
                            "name": "%s", 
                            "short_session": "%s", 
                            "long_session": "%s"}
                            """ % (avatar.nickname, 
                                   short_session,
                                   long_session)

        self.request.write(value)
        self.request.finish()


    def _loginFailed(self, failure):
        self.request.write(""")]}',\n{"login": "fail"}""")
        self.request.finish()


class SignOut(resource.Resource):
    """ Log user out by destroying session tokens"""

    def __init__(self, session_redis):
        """Only arg is session datastore"""

        self.session_redis = session_redis

    def render(self, request):
        """
            Removes tokens from Redis and returns logout success
            
            Request:
                {'shortSession': 'short session token',
                 'longSession': 'long session token'}
        """
   
        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS": return ""

        data = json.loads(request.content.getvalue())

        short_session = data['shortSession'] 
        long_session = data['longSession']

        # Remove session info from Redis
        if self.session_redis.exists(long_session):
            self.session_redis.delete(long_session)
        if self.session_redis.exists(short_session):
            self.session_redis.delete(short_session)

        return """)]}',\n{"loggedOut": true}"""


#TODO: later
class AddNewUser(resource.Resource):
    """ Add a new user to the system """
    def render(self, request):

        return """ """


#TODO: later
class PasswordReminder(resource.Resource):
    """ Send an email reminder of a password to a user """
    def render(self, request):

        return """ """


class InitiateCrawl(resource.Resource):
    """Initiate a crawl and return the crawl id"""

    def __init__(self, central_redis, session_redis, expire):
        """ 
            Args: 
                Central Redis - to communicate with analysis engine
                Session Redis - maintain session state
        """

        self.central_redis = central_redis
        self.session_redis = session_redis
        self.longExpire = expire['longExpire']
        self.shortExpire = expire['shortExpire']

    def render(self, request):
        """
            Construct Crawl ID, place into Redis and return to user

            Request:
                {'shortSession': 'short session token',
                 'longSession': 'long session token'}          
        """

        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS": return ""

        crawl_json = request.content.getvalue()
        data = json.loads(crawl_json)

        short_session = data['shortSession'] 
        long_session = data['longSession']

        if self.session_redis.exists(short_session):

            # set new expirations
            self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)
    
            # Create crawl id (user id, crawlname, date, random)
            # TODO: fix crawl id
            crawl = data['crawl']
            user_decoded = base64.b64decode(long_session).split("///")[1]
            user_id = base64.b64encode(user_decoded)
            name = base64.b64encode(crawl['name'])
            time = base64.b64encode(crawl['time'])
            rand = uuid.uuid4().bytes.encode("base64")[:4]

            crawl_id = user_id + "-" + name + "-" + time + "-" + rand

            # Set crawl info into Redis
            self.central_redis.set(crawl_id, crawl_json)
            self.central_redis.expire(crawl_id, self.shortExpire)

            # Set crawl count into Redis
            self.central_redis.set(crawl_id + "_count", -1)
            self.central_redis.expire(crawl_id + "_count", self.shortExpire)

            print ""
            print "Crawl ID"
            print crawl_id

            # Set crawl id into Redis crawl queue
            self.central_redis.rpush("crawl_queue", crawl_id)

            # return success
            value = """)]}',\n{"loggedIn": true, "crawlId": "%s"}
                      """ % (crawl_id)

        else:
            value = """)]}',\n{"loggedIn": false}"""

        return value


class CheckCrawlStatus(resource.Resource):
    """ Check status of a crawl based upon an id """

    def __init__(self, central_redis, session_redis, expire):
        """ 
            Args: 
                Central Redis - to communicate with analysis engine
                Session Redis - maintain session state
        """

        self.central_redis = central_redis
        self.session_redis = session_redis
        self.longExpire = expire['longExpire']
        self.shortExpire = expire['shortExpire']

    def render(self, request):
        """
            Check and return crawl status

            Request:
                {'shortSession': 'short session token',
                 'longSession': 'long session token',
                 'id': 'crawl id'}

            Return:
                positive int - page count
                -1 - initializing
                -2 - crawl complete
        """

        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS": return ""

        data = json.loads(request.content.getvalue())

        crawl_id = data['id']
        short_session = data['shortSession'] 
        long_session = data['longSession']

        if self.session_redis.exists(short_session):

            # set new expirations
            self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)

            # retrieve crawl status
            count = self.central_redis.get(crawl_id + "_count")
            self.central_redis.expire(crawl_id + "_count", self.shortExpire)

            return """)]}',\n{"count": %s}""" % count

        else:
          return """)]}',\n{"count": -99}"""


class GetS3Signature(resource.Resource):
    """ Sign a Url to retrieve objects from S3 """

    def __init__(self, session_redis, mock, expire):
        """ 
            Args: 
                Session Redis - maintain session state
                mock - if True to mock S3 backend
        """

        self.session_redis = session_redis
        self.mock = mock
        self.longExpire = expire['longExpire']
        self.shortExpire = expire['shortExpire']

    def render(self, request):
        """
            Generate signed URL to get requested analysis from S3
            
            Request:
                {'shortSession': 'short session token',
                 'longSession': 'long session token',
                 'analysisId': 'id of analysis to retrieve'}

            Return:
                Signed URL to access object on S3
            """
   
        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS": return ""

        data = json.loads(request.content.getvalue())

        analysis_id = data['analysisId']
        short_session = data['shortSession'] 
        long_session = data['longSession']

        # If logged in, retrieve analysis from users bucket
        if self.session_redis.exists(long_session):

            # set new expirations
            if self.session_redis.exists(short_session):
              self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)

            # Create S3 key with user's id and analysis id
            # TODO: fix crawl id
            user_id = base64.b64decode(long_session).split("///")[1] 
            key = user_id + '/' + analysis_id + '.json'
            
            # Sign URL (assumes AWS keys are in .bashrc / env)
            s3conn = boto.connect_s3()
            url = s3conn.generate_url(30, 'GET', bucket='ps_users', key=key)
 
            # Mock AWS S3 backend
            if self.mock:
                url = analysis_id + ".json"
                url = unicodedata.normalize('NFKD', url) \
                                 .encode('ascii','ignore')
            
            return """)]}',\n{"url": "%s"}""" % url

        # Otherwise, not logged in, so retrieve from anonymous bucket
        else:

            # Create S3 key with anonymous id and analysis id
            key = 'anonymous/' + analysis_id + '.json'
            
            # Sign url (assumes AWS keys are in .bashrc / env)
            s3conn = boto.connect_s3()
            url = s3conn.generate_url(30, 'GET', bucket='ps_users', key=key)
 
            # Mock AWS S3 backend
            if self.mock:
                url = analysis_id + ".json"
                url = unicodedata.normalize('NFKD', url) \
                                 .encode('ascii','ignore')

            return """)]}',\n{"url": "%s"}""" % url


class GetAnalysisFolders(resource.Resource):
    """ Retrieve users analysis folders """

    def __init__(self, session_redis, user_redis, expire):
        """ 
            Args: 
                Session Redis - maintain session state
                User Redis - contains user information
        """

        self.session_redis = session_redis
        self.user_redis = user_redis
        self.longExpire = expire['longExpire']
        self.shortExpire = expire['shortExpire']

    def render(self, request):
        """
            Return user's folders info

            Request:
                {'shortSession': 'short session token',
                 'longSession': 'long session token'}

            Return:
                FolderList = [folderInfo1, ...]
                FolderInfo =
                {'name': 'foldername', 'analysisList': [analysisInfo1, ...]}
                AnslysisInfo = 
                {'name': 'analysisname', 'data': 'data', 'id': 'id'}            
        """
   
        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS": return ""

        data = json.loads(request.content.getvalue())

        short_session = data['shortSession'] 
        long_session = data['longSession']

        # Logged in user
        if self.session_redis.exists(long_session):

            # set new expirations
            if self.session_redis.exists(short_session):
              self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)

            # Get user's id 
            # TODO:  fix crawl id
            user_id = base64.b64decode(long_session).split("///")[1] 

            # Retrieve user info from Redis
            folder_info = self.user_redis.get(user_id + "_folders")

            return ")]}',\n" + folder_info

        # Anonymous User so show samples
        else:

            # Retrieve user info from Redis
            folder_info = self.user_redis.get("sample_folders")

            return ")]}',\n" + folder_info


class UpdateAnalysisFolders(resource.Resource):
    """ Update user's analysis folders """

    def __init__(self, session_redis, user_redis, expire):
        """ 
            Args: 
                Session Redis - maintain session state
                User Redis - contains user information
        """

        self.session_redis = session_redis
        self.user_redis = user_redis
        self.longExpire = expire['longExpire']
        self.shortExpire = expire['shortExpire']

    def render(self, request):
        """
            Return user's folders info

            Request:
                {'shortSession': 'short session token',
                 'longSession': 'long session token',
                 'folderInfo': 'JSON folder info'}

            Return:
                FolderList = [folderInfo1, ...]
                FolderInfo =
                {'name': 'foldername', 'analysisList': [analysisInfo1, ...]}
                AnslysisInfo = 
                {'name': 'analysisname', 'data': 'data', 'id': 'id'}            
        """
   
        self.request = set_headers(request)

        # Return if preflight request
        if request.method == "OPTIONS": return ""

        data = json.loads(request.content.getvalue())

        folder_data = data['folderInfo']
        short_session = data['shortSession'] 
        long_session = data['longSession']

        # Logged in user
        if self.session_redis.exists(long_session):

            # set new expirations
            if self.session_redis.exists(short_session):
              self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)

            # Get user's id 
            # TODO:  fix crawl id
            user_id = base64.b64decode(long_session).split("///")[1] 

            # Turn folder info back into JSON
            folder_info = json.dumps(folder_data)
            
            # Set new user folder info into Redis
            self.user_redis.set(user_id + "_folders", folder_info)

            return """)]}',\n{"success": true}"""

        # Anonymous User so show samples
        else:

            # How to add anonymous users stuff to temp folder? 

            return """)]}',\n{"success": false}"""


# Helper Funcs
###############################################################################
def set_headers(request):
    """Set CORS info required on all headers"""

    # TODO: Limit origin and headers in production?

    # Content type is always json
    request.setHeader('Content-Type', 'application/json')

    # Access control: CORs
    request.setHeader('Access-Control-Allow-Origin', '*')
    request.setHeader('Access-Control-Allow-Methods', 'POST')

    # Echo back all request headers for CORs
    access_headers = request.getHeader('Access-Control-Request-Headers')
    request.setHeader('Access-Control-Allow-Headers', access_headers)

    return request


# Command Line Crap & Initialization
###############################################################################

if __name__ == "__main__":

    # TODO: Refactor so reads info from a config file
    # TODO: Add Config option for Expiration

    # Parse command line options and arguments.
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    # Central Redis host info - default is localhost
    parser.add_option(
            "-c", "-C", "--centralRedisHost", action="store", 
            default="localhost", dest="centralRedisHost", 
            help="Set Central Redis host information. [default: %default]")

    # Central Redis port info - default is 6379
    parser.add_option(
            "-p", "-P", "--centralRedisPort", action="store", 
            default="6379", dest="centralRedisPort", 
            help="Set Central Redis port information. [default: %default]")

    # User Redis host info - default is localhost
    parser.add_option(
            "-u", "-U", "--userRedisHost", action="store", 
            default="localhost", dest="userRedisHost", 
            help="Set User Redis host information. [default: %default]")

    # User Redis port info - default is 6378
    parser.add_option(
            "-q", "-Q", "--userRedisPort", action="store", 
            default="6378", dest="userRedisPort", 
            help="Set User Redis port information. [default: %default]")

    # Session Redis host info - default is localhost
    parser.add_option(
            "-s", "-S", "--sessionRedisHost", action="store", 
            default="localhost", dest="sessionRedisHost", 
            help="Set Session Redis host information. [default: %default]")

    # Session Redis port info - default is 6377
    parser.add_option(
            "-r", "-R", "--sessionRedisPort", action="store", 
            default="6377", dest="sessionRedisPort", 
            help="Set Session Redis port information. [default: %default]")

    # Mock AWS S3 Backend
    # Mock folder structure must match test S3 structure and vice versa
    # Files should be in the app directory on localhost
    parser.add_option(
            "-m", "-M", "--mock", action="store_true", 
            default="", dest="mock", 
            help="Mock S3 Backend. [default: False]")

    (options, args) = parser.parse_args()
    if int(options.centralRedisPort) < 1:
        parser.error("Central Redis port number must be greater than 0")
    if int(options.userRedisPort) < 1:
        parser.error("User Redis port number must be greater than 0")
    if int(options.sessionRedisPort) < 1:
        parser.error("User Redis port number must be greater than 0")

    # Initialize Central Redis connection to 
    c = redis.StrictRedis(host=options.centralRedisHost,
                              port=int(options.centralRedisPort), db=0)

    # Initialize User Redis connection to
    # Can refactor into pdiddy, user, folder (or go RDB? for all)
    u = redis.StrictRedis(host=options.userRedisHost,
                              port=int(options.userRedisPort), db=0)

    # Initialize Session Redis connection to 
    s = redis.StrictRedis(host=options.sessionRedisHost,
                              port=int(options.sessionRedisPort), db=0)

    # Credentials / Authentication info
    p = portal.Portal(SpiderRealm(u))
    p.registerChecker(PasswordChecker(u))

    m = options.mock

    # Redis Key Expiration Info
    e = {}
    e['longExpire'] = (60 * 60 * 24) # 1 day
    e['shortExpire'] = (60 * 60) # 1 hour
    
    # Set up site and resources
    root = resource.Resource()
    root.putChild('initiatecrawl', InitiateCrawl(c, s, e))
    root.putChild('checkcrawlstatus', CheckCrawlStatus(c, s, e))
    root.putChild('gets3signature', GetS3Signature(s, m, e))
    root.putChild('getanalysisfolders', GetAnalysisFolders(s, u, e))
    root.putChild('updateanalysisfolders', UpdateAnalysisFolders(s, u, e))
    root.putChild('addnewuser', AddNewUser())
    root.putChild('checkusercredentials', CheckUserCredentials(p, s, e))
    root.putChild('signout', SignOut(s))
    root.putChild('passwordreminder', PasswordReminder())
    site = server.Site(root)

    # Run the twisted server
    reactor.listenTCP(8000, site)
    reactor.run()


