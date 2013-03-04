from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import protocol, reactor, defer
from twisted.web import resource, static, server
from zope.interface import Interface, implements

import json
import redis
import uuid
import datetime
import base64


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

        data = json.loads(request.content.getvalue())

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

            # Set crawl info into Redis
            self.redis.set(crawl_id, crawl)
            self.redis.expire(crawl_id, (60*60))

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

        # TODO: check XSRF header
        print('here we are')

        return """)]}',\n{"count": 10}"""

class GetS3Signature(resource.Resource):
    """ Sign a Url to retrieve objects from S3 """

    def render(self, request):
   
        # TODO: check XSRF header

        return """
        <html>
        <head><title>testHome</title></head>
        <body><h1>CrawlInitiated</h1></body>
        </html>
        """

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

    p = portal.Portal(TestRealm(users))
    p.registerChecker(PasswordDictChecker(passwords))

    # hardcode for now
    redis_info = {'host': 'localhost', 'port': 6379}
    r = redis.StrictRedis(host=redis_info["host"],
                              port=int(redis_info["port"]), db=0)

    root = resource.Resource()
    root.putChild('', HomePage())
    root.putChild('initiatecrawl', InitiateCrawl(r))
    root.putChild('checkcrawlstatus', CheckCrawlStatus(r))
    root.putChild('gets3signature', GetS3Signature())
    root.putChild('addnewuser', AddNewUser())
    root.putChild('checkusercredentials', CheckUserCredentials(p,r))
    root.putChild('passwordreminder', PasswordReminder())
    site = server.Site(root)

    reactor.listenTCP(8000, site)
    reactor.run()


