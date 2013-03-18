'use strict';

spiderwebApp.controller('SpiderdiariesCtrl', ['$scope', '$routeParams', function($scope, $routeParams) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  $scope.tutorials = ["tutorial1"];

  $scope.examples = ["testexample"];

  $scope.pageType = { examples: true,
                      tutorials: false };

  $scope.showLinks = function(pageType) {
    for (var type in $scope.pageType) {
      if (type === pageType) {
        $scope.pageType[type] = true;
      }
      else {
        $scope.pageType[type] = false;
      };  
    };
  };

  // Open to directory traversal but it is all on the client anyway.
  // Should check to see if it is in a list of possibilities so can redirect on bad entry.
  if (typeof $routeParams['pageType'] === "undefined") {
    $scope.template = "views/spiderdiaries/tutorials/tutorial1.html";
  }
  else {
    var pageType = $routeParams['pageType'];
    for (var type in $scope.pageType) {
      if (type === $routeParams['pageType']) {
        $scope.pageType[type] = true;
      }
      else {
        $scope.pageType[type] = false;
      };
    };
    if (typeof $routeParams['pageName'] === "undefined") {
      var pageName = $scope[pageType][0];
      $scope.template = "views/spiderdiaries/" + pageType + "/" + pageName + ".html";
    }
    else {
      $scope.template = "views/spiderdiaries/" + $routeParams['pageType'] + "/" + $routeParams['pageName'] + ".html"; 
    };
  };
}]);
