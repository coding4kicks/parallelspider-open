'use strict';

spiderwebApp.controller('SplashdownCtrl', function($scope, $http) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  $scope.analysisList = ['myFirstAnalysis'];
  $scope.currentAnalysis = {'name': 'myFirstAnalysis', 'date': '10/12/2030'};

  $scope.analysis = {};
  $scope.analysis.name = "hope to change";

  $http.get('results.json')
    .then(function(results){
        $scope.analysis = results.data;
    });
});
