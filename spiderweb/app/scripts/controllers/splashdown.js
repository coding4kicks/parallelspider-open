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

  // additional info button types for each type of results
  $scope.buttonTypes = {};
  var wordButtons = [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'},
                     {'type': 'tags', 'active': false, 'label': 'Tags', 'itemType': 'tag'}];
  $scope.buttonTypes.visibleText = wordButtons;
  $scope.buttonTypes.headlineText = wordButtons;
  $scope.buttonTypes.hiddenText = wordButtons;
  $scope.buttonTypes.searchWords = wordButtons;
  $scope.buttonTypes.allLinks = [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'},
                                 {'type': 'words', 'active': false, 'label': 'Words', 'itemType': 'words'}];
  $scope.buttonTypes.externalDomains = [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'},
                                        {'type': 'words', 'active': false, 'label': 'Words', 'itemType': 'words'},
                                        {'type': 'links', 'active': false, 'label': 'Links', 'itemType': 'link'}];
  $scope.buttonTypes.linkText = [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'}];


  
  $http.get('results2.json')
    .then(function(results){

        $scope.analysis = results.data;

        // Add property "include" for comparison & additionalInfo
        for (var i = 0; i < $scope.analysis.sites.length; i++) {

          // include is used in Common Ground to enable/disable site inclusion in comparison
          $scope.analysis.sites[i].include = true;

          // Create additional info for each site and for each splashdown page type
          $scope.analysis.sites[i].additionalInfo = {};
          $scope.analysis.sites[i].additionalInfo.text = { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
                                                            'currentItem': {}, 'currentType': "", 'currentLabel': ""};;
          $scope.analysis.sites[i].additionalInfo.links = { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
                                                            'currentItem': {}, 'currentType': "", 'currentLabel': ""};
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
    
    // Set all additional info to null
    for (var i = 0; i < $scope.analysis.sites.length; i++) {
      var addInfo = $scope.analysis.sites[i].additionalInfo;
      addInfo.text.showing = false;
      addInfo.text.currentItem = {};
      addInfo.links.showing = false;
      addInfo.links.currentItem = {};
    }

    // Re-compare sites for common ground with current result type
    $scope.compareSites();
  }

  /*
   * showInfo - shows the additional information of a selected item
   *
   * args:
   *  site - the site to which the item belongs
   *  page - the page the item is on: text, links
   *  item - the itme itself: word, link, domain
   *  type - the item type as a text string: Word, Link, Domain
   *  label - the label for the category: Visible Text, All Links, etc.
   *  buttonType - the buttonType associated with the item: visibleText, allLinks, etc.
   */
  $scope.showInfo = function(site, page, item, type, label, buttonType) 
  {
    var addInfo = site.additionalInfo[page];

    // Allow ability to deselect item
    if (addInfo.currentItem == item) {
      addInfo.showing = false;
      addInfo.currentItem = {};
    }
    else {
      addInfo.showing = true;
      addInfo.currentItem = item;
      addInfo.currentType = type;
      addInfo.currentLabel = label;
      addInfo.buttonTypes = $scope.buttonTypes[buttonType];
      addInfo.currentButton.active = false;
      addInfo.currentButton = $scope.buttonTypes[buttonType][0];
      addInfo.currentButton.active = true;
    }
  }

  /*
   * switchInfoType - switches the additional information type displayed
   *
   * args:
   *  additionalInfo - the site and page info to switch
   *  button - the button/info to display
   */
  $scope.switchInfoType = function(additionalInfo, button) {
    additionalInfo.currentButton.active = false;
    button.active = true;
    additionalInfo.currentButton = button;
  }
});
