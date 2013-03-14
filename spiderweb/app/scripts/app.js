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
 *
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
  // SERVICES
  ////////////////////////////

  .service('configService', function() {
    // change4deployment
    var host = 'localhost:8000',
        protocol = 'http';

    return {
      setHost: function (configHost) {
        host = configHost;
      },
      getHost: function () {
        return host;
      },
      setProtocol: function (configProtocol) {
        protocol = configProtocol;
      },
      getProtocol: function () {
        return protocol;
      }

    };
  })

  .service('resultsService', function ($http, $q, sessionService, configService) {

    // Where am I setting this???
    // Either get the results passed, the current if one is set, or none
    var currentAnalysis = {};
    //var currentAnalysis = {'id': 'results1SiteSearchOnly'};
    
    return {
      getAnalysis:function (analysisId) {

        // set currentAnalysis
        currentAnalysis = {'id':analysisId};

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/gets3signature',
            data = {'analysisId': analysisId,
                    'shortSession': sessionService.getShortSession(),
                    'longSession': sessionService.getLongSession() },
            deferred = $q.defer();

        // QA data - since "" returned from session service will trigger undefined
        if (typeof data.shortSession === "undefined") {
          data.shortSession = "";
        }
        if (typeof data.longSession === "undefined") {
          data.longSession = "";
        }


        $http.post(url, data)
          .success(function(data, status, headers, config){
            console.log(data.url);
            if (data.url !== 'error') {
              $http.get(data.url)
                .success(function(data, status, headers, config){
                  deferred.resolve(data);
                })
                .error(function(data, status, headers, config){
                  console.log('error');
                });
            }
            else {
              console.log('error');
            }
          })
          .error(function(data, status, headers, config){
            console.log("error");
          });

        return deferred.promise;
        // Must later account for user ???
        //return currentAnalysis;
      },

      getCurrentAnalysis: function () {
        return currentAnalysis;
      },

      setCurrentAnalysis: function (analysisId) {
        currentAnalysis = {'id': analysisId};
      },

      listAnalyses:function () {
        // This function will take the "user"??? and list their analyses
        // later funcionality should also allow them to place analysis into folders like gmail
        // even later timeseries analysis should be enabled.
      }
    };
  })

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

  .service('crawlService', function ($http, $q, sessionService, configService) {
    var crawlId = "",
        maxPages = 0;
    
    return {
      getCrawlId:function () {
        return crawlId;
      },
      setCrawlId:function (id) {
        crawlId = id;
      },

      getMaxPages:function () {
        return maxPages;
      },

      setMaxPages:function (pages) {
        maxPages = pages;
      },

      getCrawlStatus:function () {

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/checkcrawlstatus',
            data = {'id': crawlId, 
                    'shortSession': sessionService.getShortSession(),
                    'longSession': sessionService.getLongSession() },
            deferred = $q.defer();


        $http.post(url, data)
          .success(function(data, status, headers, config){
            deferred.resolve(data);
          })
          .error(function(data, status, headers, config){
            console.log('error');
          });

        return deferred.promise;
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




