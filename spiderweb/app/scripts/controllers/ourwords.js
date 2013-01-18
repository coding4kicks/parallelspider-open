'use strict';

spiderwebApp.controller('OurwordsCtrl', function($scope, $routeParams) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  // Open to directory traversal but it is all on the client anyway.
  // Should check to see if it is in a list of possibilities so can redirect on bad entry.
  if (typeof $routeParams['pageName'] === "undefined") {
    $scope.template = "views/ourwords/about.html";
  }
  else {
    $scope.template = "views/ourwords/" + $routeParams['pageName'] + ".html"; 
  };
});
