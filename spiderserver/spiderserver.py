from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import protocol, reactor, defer
from twisted.web import resource, static, server
from zope.interface import Interface, implements

import json
import redis
import uuid
import datetime
import base64
import boto
import optparse
import unicodedata


# AUTHENTICATION
##################
class PasswordChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, user_redis):
        """ dict like object mapping usernames to passwords """
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
    """ should have attributes username and nickname """

class NamedUserAvatar(object):
    implements(INamedUserAvatar)

    # username will be email (switch name to match)
    def __init__(self, username, nickname):
        self.username = username # login id (unique id used in system)
        self.nickname = nickname # nickname to display on welcome / forumn

class SpiderRealm(object):
    implements(portal.IRealm)

    def __init__(self, user_redis):
        self.user_redis = user_redis

    def requestAvatar(self, avatarId, mind, *interfaces):
        if INamedUserAvatar in interfaces:
            user_data = self.user_redis.get(avatarId + '_info')
            user_info = json.loads(user_data)
            nickname = user_info['nickname']
            # Must encode as string vice unicode, wtf!
            nickname = unicodedata.normalize('NFKD', nickname).encode('ascii','ignore')
            logout = lambda: None
            return (INamedUserAvatar, 
                    NamedUserAvatar(avatarId, nickname),
                    logout)
        else:
            raise KeyError("None of the requested interfaces are supported")

# RESOURCES
##################

class CheckUserCredentials(resource.Resource):
    """ Validate user's credentials for login """
    def __init__(self, portal, session_redis):
        self.portal = portal
        self.session_redis = session_redis
        self.request = ""

        # Expiration Info
        self.longExpire= (60 * 60 * 24) # 1 day
        self.shortExpire = (60 * 60) # 1 hour

    def render(self, request):
        self.request = request

        # Add headers prior to writing
        self.request.setHeader('Content-Type', 'application/json')

        # Set access control: CORS 

        # TODO: limit origins on live site?
        self.request.setHeader('Access-Control-Allow-Origin', '*')
        self.request.setHeader('Access-Control-Allow-Methods', 'POST')
        # Echo back all request headers
        access_headers = self.request.getHeader('Access-Control-Request-Headers')
        self.request.setHeader('Access-Control-Allow-Headers', access_headers)

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

        avatarInterface, avatar, logout = avatarInfo

        # Short session token - for crawl purchases and changing user info
        short_session = uuid.uuid4().bytes.encode("base64")[:21]
        self.session_redis.set(short_session, 'ps_shortsession') #any info in value?
        self.session_redis.expire(short_session, self.shortExpire)

        # Long session token - for user info and data analysis
        u = uuid.uuid4().bytes.encode("base64")[:4]
        # Place nickname so can reload from cookie, and date for logging
        v = base64.b64encode(avatar.nickname + '///' + avatar.username + '///'
                + str(datetime.datetime.now))
        long_session = v + u
        self.session_redis.set(long_session, 'ps_longsession') #any info in value?
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

        # TODO: set both Session and Purchase cookie in Browser and Redis
        # TODO: retrieve user info from Database?
        # TODO: retrieve Analyses folder information - db or s3?
        # TODO: retrieve user info for account page, payment info?

    def _loginFailed(self, failure):
        self.request.write(""")]}',\n{"login": "fail"}""")
        #self.request.write(str(failure))
        self.request.finish()

class SignOut(resource.Resource):
    """ Log user out by destroying session tokents"""

    def __init__(self, session_redis):
        self.session_redis = session_redis

        self.request = ""

    def render(self, request):
   
        self.request = request

        # Add headers prior to writing
        self.request.setHeader('Content-Type', 'application/json')

        # Set access control: CORS 
        # TODO: refactor stuff out to function

        # TODO: limit origins on live site?
        self.request.setHeader('Access-Control-Allow-Origin', '*')
        self.request.setHeader('Access-Control-Allow-Methods', 'POST')
        # Echo back all request headers
        access_headers = self.request.getHeader('Access-Control-Request-Headers')
        self.request.setHeader('Access-Control-Allow-Headers', access_headers)

        # Return if preflight request
        if request.method == "OPTIONS":
            return ""

        data = json.loads(request.content.getvalue())

        short_session = data['shortSession'] 
        long_session = data['longSession']

        if self.session_redis.exists(long_session):
            self.session_redis.delete(long_session)

        if self.session_redis.exists(short_session):
            self.session_redis.delete(short_session)

        return """)]}',\n{"loggedOut": true}"""


#TODO: later
class AddNewUser(resource.Resource):
    """ Add a new user to the system """
    def render(self, request):
        return """
        <html>
        <head><title>testHome</title></head>
        <body><h1>New user added.</h1></body>
        </html>
        """

#TODO: later
class PasswordReminder(resource.Resource):
    """ Send an email reminder of a password to a user """
    def render(self, request):

        # TODO: check XSRF header

        return """
        <html>
        <head><title>testHome</title></head>
        <body><h1>Email sent.</h1></body>
        </html>
        """

class InitiateCrawl(resource.Resource):
    """ Initiate a crawl and return the crawl id """

    def __init__(self, central_redis, session_redis):
        self.central_redis = central_redis
        self.session_redis = session_redis

        # Expiration Info TODO: factor out so don't repeat
        self.longExpire= (60 * 60 * 24) # 1 day
        self.shortExpire = (60 * 60) # 1 hour

    def render(self, request):

        self.request = request

        # TODO: check XSRF header

        # Add headers prior to writing
        self.request.setHeader('Content-Type', 'application/json')

        # Set access control: CORS 
        # TODO: refactor stuff out to function

        # TODO: limit origins on live site?
        self.request.setHeader('Access-Control-Allow-Origin', '*')
        self.request.setHeader('Access-Control-Allow-Methods', 'POST')
        # Echo back all request headers
        access_headers = self.request.getHeader('Access-Control-Request-Headers')
        self.request.setHeader('Access-Control-Allow-Headers', access_headers)

        # Return if preflight request
        if request.method == "OPTIONS":
            return ""

        crawl_json = request.content.getvalue()
        data = json.loads(crawl_json)

        short_session = data['shortSession'] 
        long_session = data['longSession']

        if self.session_redis.exists(short_session):

            # set new expirations
            self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)
    
            # Create crawl id (username, crawlname, date, random)
            crawl = data['crawl']
            user = base64.b64encode(data['userName'])
            name = base64.b64encode(crawl['name'])
            time = base64.b64encode(crawl['time'])
            rand = uuid.uuid4().bytes.encode("base64")[:4]

            crawl_id = user + "-" + name + "-" + time + "-" + rand

            # Set crawl info into Redis
            self.central_redis.set(crawl_id, crawl_json)
            self.central_redis.expire(crawl_id, (60*60))

            # Set crawl count into Redis
            self.central_redis.set(crawl_id + "_count", -1)
            self.central_redis.expire(crawl_id + "_count", (60*60))

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

    def __init__(self, central_redis, session_redis):
        self.central_redis = central_redis
        self.session_redis = session_redis

        # Expiration Info
        self.longExpire= (60 * 60 * 24) # 1 day
        self.shortExpire = (60 * 60) # 1 hour

        self.request = ""

    def render(self, request):

        self.request = request

        # Add headers prior to writing
        self.request.setHeader('Content-Type', 'application/json')

        # Set access control: CORS 
        # TODO: refactor stuff out to function

        # TODO: limit origins on live site?
        self.request.setHeader('Access-Control-Allow-Origin', '*')
        self.request.setHeader('Access-Control-Allow-Methods', 'POST')
        # Echo back all request headers
        access_headers = self.request.getHeader('Access-Control-Request-Headers')
        self.request.setHeader('Access-Control-Allow-Headers', access_headers)

        # Return if preflight request
        if request.method == "OPTIONS":
            return ""

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
            self.central_redis.expire(crawl_id + "_count", (60*60))

            return """)]}',\n{"count": %s}""" % count

        else:
          return """)]}',\n{"count": -99}"""


class GetS3Signature(resource.Resource):
    """ Sign a Url to retrieve objects from S3 """

    def __init__(self, session_redis):
        self.session_redis = session_redis

        # Expiration Info
        self.longExpire= (60 * 60 * 24) # 1 day
        self.shortExpire = (60 * 60) # 1 hour

        self.request = ""

    def render(self, request):
   
        self.request = request

        # Add headers prior to writing
        self.request.setHeader('Content-Type', 'application/json')

        # Set access control: CORS 
        # TODO: refactor stuff out to function

        # TODO: limit origins on live site?
        self.request.setHeader('Access-Control-Allow-Origin', '*')
        self.request.setHeader('Access-Control-Allow-Methods', 'POST')
        # Echo back all request headers
        access_headers = self.request.getHeader('Access-Control-Request-Headers')
        self.request.setHeader('Access-Control-Allow-Headers', access_headers)

        # Return if preflight request
        if request.method == "OPTIONS":
            return ""

        data = json.loads(request.content.getvalue())

        analysis_id = data['analysisId']
        short_session = data['shortSession'] 
        long_session = data['longSession']
        #print('here')
        if self.session_redis.exists(long_session):

            # set new expirations
            if self.session_redis.exists(short_session):
              self.session_redis.expire(short_session, self.shortExpire)
            self.session_redis.expire(long_session, self.longExpire)

            # Create S3 key with user's id and analysis id
            user_id = base64.b64decode(long_session).split("///")[1] 
            key = user_id + '/' + analysis_id + '.json'
            #print key
            # Sign url (assumes AWS keys are in .bashrc / env)

            
            s3conn = boto.connect_s3()
            url = s3conn.generate_url(30, 'GET', bucket='ps_users', key=key)
 
            # Temporarily overwrite url so don't continuously pull 10mb from AWS
            # TODO: make so disable/enable with mock backend
            mockS3 = True
            if mockS3:
                url = analysis_id + ".json"
                url = unicodedata.normalize('NFKD', url).encode('ascii','ignore')
            #url = 'results3SiteLinks.json'
            #print url

            return """)]}',\n{"url": "%s"}""" % url


        else:
            return """)]}',\n{"url": "error"}"""

class GetAnalysisFolders(resource.Resource):
    """ Retrieve analysis folders """

    def __init__(self, session_redis, user_redis):
        self.session_redis = session_redis
        self.user_redis = user_redis

        # Expiration Info
        self.longExpire= (60 * 60 * 24) # 1 day
        self.shortExpire = (60 * 60) # 1 hour

        self.request = ""

    def render(self, request):
   
        self.request = request

        # Add headers prior to writing
        self.request.setHeader('Content-Type', 'application/json')

        # Set access control: CORS 
        # TODO: refactor stuff out to function

        # TODO: limit origins on live site?
        self.request.setHeader('Access-Control-Allow-Origin', '*')
        self.request.setHeader('Access-Control-Allow-Methods', 'POST')
        # Echo back all request headers
        access_headers = self.request.getHeader('Access-Control-Request-Headers')
        self.request.setHeader('Access-Control-Allow-Headers', access_headers)

        # Return if preflight request
        if request.method == "OPTIONS":
            return ""

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
            user_id = base64.b64decode(long_session).split("///")[1] 

            # Retrieve user info from Redis
            folder_info = self.user_redis.get(user_id + "_folders")

            return ")]}',\n" + folder_info

        # Anonymous User so show samples
        else:

            return ")]}',\n" + folder_info

# Command Line Crap & Initialization
################################################################################

if __name__ == "__main__":

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

    # Set up site and resources
    root = resource.Resource()
    root.putChild('initiatecrawl', InitiateCrawl(c, s))
    root.putChild('checkcrawlstatus', CheckCrawlStatus(c, s))
    root.putChild('gets3signature', GetS3Signature(s))
    root.putChild('getAnalysisFolders', GetAnalysisFolders(s, u))
    root.putChild('addnewuser', AddNewUser())
    root.putChild('checkusercredentials', CheckUserCredentials(p, s))
    root.putChild('signout', SignOut(s))
    root.putChild('passwordreminder', PasswordReminder())
    site = server.Site(root)

    # Run the twisted server
    reactor.listenTCP(8000, site)
    reactor.run()


