from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import protocol, reactor, defer
from twisted.web import resource, static, server
from zope.interface import Interface, implements

import json


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
    def __init__(self, portal):
        self.portal = portal
        self.request = ""

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

        k = 'testCookie'
        v = 'yumyumcookies'
        self.request.addCookie(k, v, expires=None, domain=None, path=None, 
                                max_age=None, comment=None, secure=None)

        value = """)]}',\n{"login": "success", 
                            "name": "%s", 
                            "session_token": "ABC123"}""" % avatar.fullname

        #self.request.write(""")]}',\n{"login": "success", "session_token": "ABC123"}""")
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
        return """
        <html>
        <head><title>testHome</title></head>
        <body><h1>Email sent.</h1></body>
        </html>
        """

class InitiateCrawl(resource.Resource):
    """ Initiate a crawl and return the crawl id """
    def render(self, request):
        print('here')
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

        # TODO: Get purchase session key from Redis to make sure logged in

        value = """)]}',\n{"loggedIn": false}"""

        return value

class CheckCrawlStatus(resource.Resource):
    """ Check status of a crawl based upon an id """
    def render(self, request):
        return """
        <html>
        <head><title>testHome</title></head>
        <body><h1>CrawlInitiated</h1></body>
        </html>
        """

class CheckCrawlStatus(resource.Resource):
    """ Check status of a crawl based upon an id """
    def render(self, request):
        return """
        <html>
        <head><title>testHome</title></head>
        <body><h1>CrawlInitiated</h1></body>
        </html>
        """

class GetS3Signature(resource.Resource):
    """ Sign a Url to retrieve objects from S3 """
    def render(self, request):
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

    root = resource.Resource()
    root.putChild('', HomePage())
    root.putChild('initiatecrawl', InitiateCrawl())
    root.putChild('checkcrawlstatus', InitiateCrawl())
    root.putChild('gets3signature', GetS3Signature())
    root.putChild('addnewuser', AddNewUser())
    root.putChild('checkusercredentials', CheckUserCredentials(p))
    root.putChild('passwordreminder', PasswordReminder())
    site = server.Site(root)

    reactor.listenTCP(8000, site)
    reactor.run()


