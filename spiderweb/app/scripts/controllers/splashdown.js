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
  $scope.commonGround = true;
  $scope.commonWords = [];
  $scope.commonWords.push( [{'word': 'hope', 'count': 32, 'rank': 1},
                        {'word': 'hope', 'count': 32, 'rank': 1},
                        {'word': 'hope', 'count': 32, 'rank': 1}] );

  $scope.commonWords.push( [{'word': 'hope', 'count': 32, 'rank': 1},
                        {'word': 'hope', 'count': 32, 'rank': 1},
                        {'word': 'hope', 'count': 32, 'rank': 1}] );

  $scope.commonWords.push( [{'word': 'hope', 'count': 32, 'rank': 1},
                        {'word': 'hope', 'count': 32, 'rank': 1},
                        {'word': 'hope', 'count': 32, 'rank': 1}] );

  $scope.analysis.name = "hope to change";

  $http.get('results.json')
    .then(function(results){

        $scope.analysis = results.data;

        // Add property "include" for comparison
        for (var site in $scope.analysis.sites) {
          // Only add to real sites, not length attribute
          if ($scope.analysis.sites[site].url) {
            $scope.analysis.sites[site].include = true;
          }
        }
    });

  $scope.compareSites = function() {
    var wordsList = [],
        startList = {},
        tempList = {},
        sites = $scope.analysis.sites;

    for (var site in sites) {
      if (sites[site].include === true) {
        //wordsList.push({ 'site' :$scope.analysis.sites[site].words});
        wordsList.push({'howdy': sites[site].results[0].words});
      }
    }
    //if (wordsList.length > 1) {
    //  for (var word in wordsList[0]) {
    //    alert(word);
    //  }
    //}
    alert(wordsList[0]['howdy']);
  }

});
