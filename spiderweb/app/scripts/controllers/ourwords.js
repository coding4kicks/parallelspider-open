'use strict';

spiderwebApp.controller('OurwordsCtrl', ['$scope', '$routeParams', function($scope, $routeParams) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];
 
  // Need to change to dictionary because Dev Team and devteam are different
  // one is the links name, the Other the path to the teamplate
  $scope.aboutPages = ['about', 'devteam', 'terms', 'contact', 'hatchery'];

  // Open to directory traversal but it is all on the client anyway.
  // Should check to see if it is in a list of possibilities so can redirect on bad entry.
  if (typeof $routeParams['pageName'] === "undefined") {
    $scope.template = "views/ourwords/about.html";
  }
  else {
    $scope.template = "views/ourwords/" + $routeParams['pageName'] + ".html"; 
  };
}]);
