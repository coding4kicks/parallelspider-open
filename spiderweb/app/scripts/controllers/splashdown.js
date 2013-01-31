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
        for (var i = 0; i < $scope.analysis.sites.length; i++) {
          $scope.analysis.sites[i].include = true;
        }
    });

  $scope.compareSites = function() {
    var wordsList = [],
        startList = {},
        tempList = {},
        words = [],
        sites = $scope.analysis.sites;

    for (var i = 0; i < sites.length; i++) {
      if (sites[i].include === true) {
        wordsList.push({'site': i + 1, 'words': sites[i].results[0].words});
      }
    }

    if (wordsList.length > 0) {

      // set up initial start list
      words = wordsList[0].words
      for (var i = 0; i < words.length; i++) {
        startList[words[i].word] = [words[i].rank];
      }

      // compare the other lists, skip the first
      for (var i = 1; i < wordsList.length; i++) {
        
        alert(i);
        //words = list.words
       // for (var word in words) {
       //   if (typeof startList[words[word].word] !== "undefined") {
       //     alert(words[word].word);
       //   }

       // }


      }
    }
    alert('howdy');
  }

});
