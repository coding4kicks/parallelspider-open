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

  $http.get('results1.json')
    .then(function(results){

        $scope.analysis = results.data;

        // Add property "include" for comparison
        for (var i = 0; i < $scope.analysis.sites.length; i++) {
          $scope.analysis.sites[i].include = true;
        }
    });

  $scope.compareSites = function() {

    var compare = function(resNum) {
      var wordsList = [],
          startList = {},
          tempList = {},
          words = [],
          sites = $scope.analysis.sites;

      for (var i = 0; i < sites.length; i++) {
        if (sites[i].include === true) {
          wordsList.push({'site': i + 1, 'words': sites[i].results[resNum].words});
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
          
          // clear temp list
          tempList = {};

          // Check words in current list to see if they are in starting list
          words = wordsList[i].words
          for (var j = 0; j < words.length; j++) {

            // only add words from new list if in hash of starting list
            if (typeof startList[words[j].word] !== "undefined") {

              // set templist word rank = to rank of start list word
              // and push current list rank to list
              tempList[words[j].word] = startList[words[j].word];
              tempList[words[j].word].push(words[j].rank);
            }
          }

          // set new start list to current templist
          startList = tempList


        }

        // Common items are last start list
        var commonFormat = [];
        var obj = startList;
        for (var prop in obj) {
          if (obj.hasOwnProperty(prop)) { 
              commonFormat.push({'word':prop, 'rank':obj[prop]});
          }
        } 
        return commonFormat;

      }
      alert('howdy');
    }
    $scope.commonWords[0] = compare(0);
    $scope.commonWords[1] = compare(1);
    $scope.commonWords[2] = compare(2);
  }

});
