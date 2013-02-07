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
  $scope.commonWords = {};
  $scope.commonColors = [];
  $scope.results = 'internalResults'
  $scope.internal = true;
  $scope.external = false;

  $http.get('results2.json')
    .then(function(results){

        $scope.analysis = results.data;

        // Add property "include" for comparison & additionalInfo
        for (var i = 0; i < $scope.analysis.sites.length; i++) {

          // include is used in Common Ground to enable/disable site inclusion in comparison
          $scope.analysis.sites[i].include = true;

          // additional info is display boxes for each word, link, etc.'s additional info
          $scope.analysis.sites[i].additionalInfo = {word: "None Selected"};
          $scope.analysis.sites[i].additionalInfo.type = "";
          $scope.analysis.sites[i].additionalInfo.selected = false;
          $scope.analysis.sites[i].additionalInfo.pagesSel = true;
          $scope.analysis.sites[i].additionalInfo.tagsSel = false;
          $scope.analysis.sites[i].additionalInfo.wordsSel = false;
          $scope.analysis.sites[i].additionalInfo.linksSel = false;

        }

        // Perform initial comparison for all sites
        $scope.compareSites();

    });

  // Compare which words are common between sites
  $scope.compareSites = function() {

    // Function to compare for each result type
    var compare = function(resultType) {
      var wordsList = [],
          startList = {},
          tempList = {},
          words = [],
          sites = $scope.analysis.sites;
     
      for (var i = 0; i < sites.length; i++) {
        if (sites[i].include === true) {
          wordsList.push({'site': i + 1, 'words': sites[i][$scope.results][resultType].words});
        }
      }

      // Only process if there are lists to process
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

      // else return undefined, no sites chosen
    }

    // Compare all three formats
    $scope.commonWords['visibleText'] = compare('visibleText');
    $scope.commonWords['headlineText'] = compare('headlineText');
    $scope.commonWords['hiddenText'] = compare('hiddenText');

    // Set up common colors
    $scope.commonColors = [];
    var sites = $scope.analysis.sites;

    for (var i = 0; i < sites.length; i++) {
      if (sites[i].include === true) {
        $scope.commonColors.push((i + 1) % 5);
      }
    }

  }

  $scope.addInfo = function(word, site, type) {
    // TODO: refacctor so don't overrite additional info every time
    // and have to reset added parameters: selected, pagesSel, and tagsSel
    var tags = site.additionalInfo.tagsSel,
        pages = site.additionalInfo.pagesSel;

    
    if (site.additionalInfo === word) {
      site.additionalInfo = {word: "None Selected"};
      site.additionalInfo.type = "";
      site.additionalInfo.selected = false;
      site.additionalInfo.tagsSel = tags;
      site.additionalInfo.pagesSel = pages;
    }
    else {
      site.additionalInfo = word;
      site.additionalInfo.type = type;
      site.additionalInfo.selected = true;
      site.additionalInfo.tagsSel = tags;
      site.additionalInfo.pagesSel = pages;
    }
  }

  $scope.addInfoChoice = function(site, choice) {
    if (choice === 'pages') {
      site.additionalInfo.pagesSel = true;
      site.additionalInfo.tagsSel = false;
      site.additionalInfo.wordsSel = false;
      site.additionalInfo.linksSel = false;
    }
    if (choice === 'tags') {
      site.additionalInfo.tagsSel = true;
      site.additionalInfo.pagesSel = false;
    }
    if (choice === 'words') {
      site.additionalInfo.wordsSel = true;
      site.additionalInfo.pagesSel = false;
      site.additionalInfo.linksSel = false;
    }
    if (choice === 'links') {
      site.additionalInfo.linksSel = true;
      site.additionalInfo.pagesSel = false;
      site.additionalInfo.wordsSel = false;
    }

  }

  $scope.resultsChoice = function(type) {
    if (type === 'internal') {
      $scope.results = 'internalResults';
      $scope.internal = true;
      $scope.external = false;
    }
    if (type === 'external') {
      $scope.results = 'externalResults';
      $scope.external = true;
      $scope.internal = false;
    }
    $scope.compareSites();
  }
});
