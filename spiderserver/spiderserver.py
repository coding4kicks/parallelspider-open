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


# AUTHENTICATION
##################
class PasswordDictChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, passwords):
        """ dict like object mapping usernames to passwords """
        self.passwords = passwords

    def requestAvatarId(self, credentials):
        username = credentials.username
        if self.passwords.has_key(username):
            if credentials.password == self.passwords[username]:
                return defer.succeed(username)
            else:
                return defer.fail(
                    credError.UnauthorizedLogin("Bad password"))
        else:
            return defer.fail(
                credError.UnauthorizedLogin("No such user"))

class INamedUserAvatar(Interface):
    """ should have attributes username and fullname """

class NamedUserAvatar(object):
    implements(INamedUserAvatar)
    def __init__(self, username, fullname):
        self.username = username
        self.fullname = fullname

class TestRealm(object):
    implements(portal.IRealm)

    def __init__(self, users):
        self.users = users

    def requestAvatar(self, avatarId, mind, *interfaces):
        if INamedUserAvatar in interfaces:
            fullname = self.users[avatarId]
            logout = lambda: None
            return (INamedUserAvatar, 
                    NamedUserAvatar(avatarId, fullname),
                    logout)
        else:
            raise KeyError("None of the requested interfaces are supported")

# RESOURCES
##################
class HomePage(resource.Resource):
    """TEST ONLY"""
    def render(self, request):
        request.setHeader('Content-Type', 'application/json')
        value = request.args['callback'][0]
        value += """({"found":12,"what":2});"""
        return value
       ## return """
       ## <html>
       ## <head><title>testHome</title></head>
       ## <body>
       ## <h1>HOME MO'FO</h1>
       ## <form name="input" action="checkusercredentials" method="get">
       ## Username: <input type="text" name="user"><br />
       ## Username: <input type="text" name="password">
       ## <input type="submit" value="Submit">
       ## </form>         
       ## </body>
       ## </html>
       ## """

class CheckUserCredentials(resource.Resource):
    """ Validate user's credentials for login """
    def __init__(self, portal, redis):
        self.portal = portal
        self.redis = redis
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
        self.redis.set(short_session, 'ps_shortsession') #any info in value?
        self.redis.expire(short_session, self.shortExpire)

        # Long session token - for user info and data analysis
        u = uuid.uuid4().bytes.encode("base64")[:8]
        # Place name so can reload from cookie, and date for logging
        v = base64.b64encode(avatar.fullname + '///' + 
                             str(datetime.datetime.now))
        long_session = v + u
        self.redis.set(long_session, 'ps_longsession') #any info in value?
        self.redis.expire(long_session, self.longExpire)

    
        value = """)]}',\n{"login": "success", 
                            "name": "%s", 
                            "short_session": "%s", 
                            "long_session": "%s"}
                            """ % (avatar.fullname, 
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

    def __init__(self, redis):
        self.redis = redis

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

        if self.redis.exists(short_session):

            # set new expirations
            self.redis.expire(short_session, self.shortExpire)
            self.redis.expire(long_session, self.longExpire)
    
            # Create crawl id (username, crawlname, date, random)
            crawl = data['crawl']
            user = base64.b64encode(data['userName'])
            name = base64.b64encode(crawl['name'])
            time = base64.b64encode(crawl['time'])
            rand = uuid.uuid4().bytes.encode("base64")[:4]

            crawl_id = user + "-" + name + "-" + time + "-" + rand

            # Set crawl json info into Redis
            self.redis.set(crawl_id, crawl_json)
            self.redis.expire(crawl_id, (60*60))

            # Set crawl count key into Redis
            self.redis.set(crawl_id + "_count", -1)
            self.redis.expire(crawl_id + "_count", (60*60))

            # Set crawl id into Redis crawl queue
            self.redis.rpush("crawl_queue", crawl_id)

            # return success
            value = """)]}',\n{"loggedIn": true, "crawlId": "%s"}
                      """ % (crawl_id)

        else:
            value = """)]}',\n{"loggedIn": false}"""

        return value

class CheckCrawlStatus(resource.Resource):
    """ Check status of a crawl based upon an id """

    def __init__(self, redis):
        self.redis = redis

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

        if self.redis.exists(short_session):

            # set new expirations
            self.redis.expire(short_session, self.shortExpire)
            self.redis.expire(long_session, self.longExpire)

            # retrieve crawl status
            count = self.redis.get(crawl_id + "_count")
            self.redis.expire(crawl_id + "_count", (60*60))

            return """)]}',\n{"count": %s}""" % count

        else:
          return """)]}',\n{"count": -99}"""


class GetS3Signature(resource.Resource):
    """ Sign a Url to retrieve objects from S3 """

    def __init__(self, redis):
        self.redis = redis

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

        userId = 'test' # get from longSession
        analysis_object = data['analysis']
        short_session = data['shortSession'] 
        long_session = data['longSession']

        if self.redis.exists(long_session):

            # set new expirations
            if self.redis.exists(short_session):
              self.redis.expire(short_session, self.shortExpire)
            self.redis.expire(long_session, self.longExpire)

            # sign url / assumes keys are in .bashrc
            s3conn = boto.connect_s3()
            url = s3conn.generate_url(30, 'GET', bucket='ps_users', key='test/results5.json')
 
            # Temporarily overwrite url so don't continuously pull 10mb from AWS
            url = "results5.json"

            return """)]}',\n{"url": "%s"}""" % url


        else:
            return """)]}',\n{"url": "error"}"""


users = {
    'a': 'super mo',
    'spidertester': 'me mo',
    'spideradmin': 'mo mo'
    }

passwords = {
    'a': 'b',
    'spidertester': 'abc',
    'spideradmin': '123'
    }


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

    (options, args) = parser.parse_args()
    central_redis_host = options.centralRedisHost
    central_redis_port = int(options.centralRedisPort)
    if central_redis_port < 1:
        parser.error("Central Redis port number must be greater than 0")

    # Credentials / Authentication info
    p = portal.Portal(TestRealm(users))
    p.registerChecker(PasswordDictChecker(passwords))

    # Initialize Central Redis connection to 
    redis_info = {'host': central_redis_host, 
                  'port': central_redis_port}
    r = redis.StrictRedis(host=redis_info["host"],
                              port=int(redis_info["port"]), db=0)

    # Set up site and resources
    root = resource.Resource()
    root.putChild('', HomePage())
    root.putChild('initiatecrawl', InitiateCrawl(r))
    root.putChild('checkcrawlstatus', CheckCrawlStatus(r))
    root.putChild('gets3signature', GetS3Signature(r))
    root.putChild('addnewuser', AddNewUser())
    root.putChild('checkusercredentials', CheckUserCredentials(p,r))
    root.putChild('passwordreminder', PasswordReminder())
    site = server.Site(root)

    # Run the twisted server
    reactor.listenTCP(8000, site)
    reactor.run()


