'use strict';

/*
 * Spider Web Application
 *
 * Front End Angular application for Parallel Spider
 *
 * Controllers:
 *  Main - Handles the home page functionality
 *  Template - Login controls for every page
 *  Splashdown - Dsplays folders and results of crawls
 *  Spiderdiaries - Tutorial and example section
 *  Launchpad - Launches crawls (more detailed than main)
 *  Ourwords - Information about the site
 *
 * Services
 *  Config - provides one place for host and protocol configuration
 *  Results - retrieves the results of a crawl from S3
 *  Session - handles user session management
 *  Crawl - used to initiate a crawl
 *
 * Directives
 *  Fullscreen - determines screen height on page load
 *  Integer - integer validation
 *  Tooltip - from angularui-bootstrap
 *  Tabs - from angularui-bootstrap
 *  Transitions - from angularui-bootstrap
 *  Dialog/Message boxes - from angularui-bootstrap
 */
var spiderwebApp = angular.module('spiderwebApp', ['ngCookies'])
  .config(['$routeProvider','$locationProvider', function($routeProvider, $locationProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'views/main.html',
        controller: 'MainCtrl'
      })
      .when('/ourwords', {
        templateUrl: 'views/ourwords.html',
        controller: 'OurwordsCtrl'
      })
      .when('/ourwords/:pageName', {
        templateUrl: 'views/ourwords.html',
        controller: 'OurwordsCtrl'
      })
      .when('/launchpad', {
        templateUrl: 'views/launchpad.html',
        controller: 'LaunchpadCtrl'
      })
      .when('/spiderdiaries', {
        templateUrl: 'views/spiderdiaries.html',
        controller: 'SpiderdiariesCtrl'
      })
      .when('/spiderdiaries/:pageType/:pageName', {
        templateUrl: 'views/spiderdiaries.html',
        controller: 'SpiderdiariesCtrl'
      })
      .when('/splashdown', {
        templateUrl: 'views/splashdown.html',
        controller: 'SplashdownCtrl'
      })
      // MAY NEED TO SEPARATE FOLDER DISPLAY AND ANALYSIS DISPLAY FOR SPEED?
      // maybe also for the back button
      .when('/splashdown/:analysisId', {
        templateUrl: 'views/splashdown.html',
        controller: 'SplashdownCtrl'
      })
      .when('/myaccount/accountId', {
        templateUrl: 'views/myaccount.html',
        controller: 'MyaccountCtrl'
      })
      .when('/signup', {
        templateUrl: 'views/signup.html',
        controller: 'SignupCtrl'
      })
      .when('/crawling', {
        templateUrl: 'views/crawling.html',
        controller: 'CrawlingCtrl'
      })
      .otherwise({
        redirectTo: '/'
      });

    //$locationProvider.html5Mode(true);
    
  }])


  ////////////////////////////
  // SERVICES - Only Session since needed by run
  ////////////////////////////




  // Manage Session State
  .service('sessionService', function() {
    var longSession = "",  // General info and analysis access
        shortSession = "", // Purchase and change user info session
        userName = "";

    return {
      setShortSession:function (session) {
        shortSession = session;
        // set in cookie too?
      },
      getShortSession:function () {
        return shortSession;
      },
      setLongSession:function (session) {
        longSession = session;
        // set in cookie
      },
      getLongSession:function (session) {
        return longSession;
      },
      setUserName: function (name) {
        userName = name;
      },
      getUserName: function () {
        // try to get from cookie if empty
        return userName;
      }
    };
  })


  ////////////////////////////
  // Page Load Configuration
  ////////////////////////////

.run(function($cookieStore, sessionService) {
  // Check for session tokens and name in cookies, yum yum
  sessionService.setLongSession($cookieStore.get('ps_longsession'));
  sessionService.setShortSession($cookieStore.get('ps_shortsession'));
  sessionService.setUserName($cookieStore.get('ps_username'));    
});

  ////////////////////////////
  // HELPER FUNCS
  ////////////////////////////

// Array Remove - By John Resig (MIT Licensed)
Array.prototype.remove = function(from, to) {
  var rest = this.slice((to || from) + 1 || this.length);
  this.length = from < 0 ? this.length + from : from;
  return this.push.apply(this, rest);
};

function isEmpty(obj) {
    for(var prop in obj) {
        if(obj.hasOwnProperty(prop))
            return false;
    }
    return true;
}




