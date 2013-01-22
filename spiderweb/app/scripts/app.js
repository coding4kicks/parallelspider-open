'use strict';

var spiderwebApp = angular.module('spiderwebApp', [])
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
      .when('/splashdown/result/:resultId', {
        templateUrl: 'views/splashdown.html',
        controller: 'SplashdownCtrl'
      })
      .when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl'
      })
      .when('/myaccount/accountId', {
        templateUrl: 'views/myaccount.html',
        controller: 'MyaccountCtrl'
      })
      .when('/signup', {
        templateUrl: 'views/signup.html',
        controller: 'SignupCtrl'
      })
      .otherwise({
        redirectTo: '/'
      });

    //$locationProvider.html5Mode(true);

  }])

  // Adjusts view size so footer is never higher up than bottom of page
  .directive('psFullscreen', function() {

    // TODO: possibly adjust for window resize;
    // http://www.javascripter.net/faq/browserw.htm
    // http://jsfiddle.net/ShadowBelmolve/c2B2z/13/
    return function(scope, element, attrs) {
      var height = window.innerHeight - 200;
      scope.minHeight = height + 'px';
    }  
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

