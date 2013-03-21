'use strict';

/*
 * Splashdown Controller 
 *
 * Handles display of the Splashdown Page data: Folder Lists & Analysis Results
 *
 * Functions:
 *  selectFolder - displays the analysis of the selected folder
 *  selectAnalysis - make analysis current and display results
 *  getFoldersOrAnalysis - display analysis if avilable or folders
 *  getAnalysis - retrieves crawl results from results service and performs initialization
 *  compareSites - Compare which words are common between sites
 *  resultsChoice - selects between internal and external results
 *  showInfo - shows the additional information of a selected item
 *  switchInfoType - switches the additional information type displayed
 *
 * TODO: implement min-width calculation for side scrolling
 * (min-width = number of analysis box elements)
 * ISSUES: 1) mac side scroll may go back a page; 2) difficulty of non-mac sidescroll?
 * $scope.minWidth = "{'min-width': '1400px'}";
 */
spiderwebApp.controller('SplashdownCtrl', ['$scope', '$http', 'resultsService', 'configService', 'sessionService', 'folderService', function($scope, $http, resultsService, configService, sessionService, folderService) {

  // TODO: A reminder to write some mother f'ing tests, dude!
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  // Show loading when downloading results
  $scope.loading = false;
  
  // Folder Information
  $scope.folderList = [];
  $scope.currentFolder = {}

  // Control whether internal or external results are shown
  $scope.results = 'internalResults';
  $scope.internal = true;
  $scope.external = false;

  // Summary information
  $scope.summary = {'totalPages': 0, 'totalWords': 0, 
                    'numberOfSites': 0, 'minutes': 0, 'seconds': 0}

  // Common Ground information
  $scope.commonGround = true;
  $scope.commonWords = {};
  $scope.commonColors = [];

  // Limit the number of results shown in each analysis box. TODO: allow user choose to choose
  $scope.limitTo = {'text': 50, 'links': 50, 'context': 50, 'synonyms': 50, 'selectors': 50}

  // Hides pointer if only one button
  $scope.soloResults = false;

  // Additional Info button settings for each type of result. TODO: refactor the smell
  $scope.buttonTypes = {};
  var wordButtons = 
    [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'},
     {'type': 'tags', 'active': false, 'label': 'Tags', 'itemType': 'tag'}];
  $scope.buttonTypes.visibleText = wordButtons;
  $scope.buttonTypes.headlineText = wordButtons;
  $scope.buttonTypes.hiddenText = wordButtons;
  $scope.buttonTypes.searchWords = wordButtons;
  $scope.buttonTypes.context = wordButtons;
  $scope.buttonTypes.synonymRings = wordButtons;
  $scope.buttonTypes.selectors = wordButtons;
  $scope.buttonTypes.allLinks = 
    [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'},
     {'type': 'words', 'active': false, 'label': 'Words', 'itemType': 'words'}];
  $scope.buttonTypes.externalDomains = 
    [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'},
     {'type': 'words', 'active': false, 'label': 'Words', 'itemType': 'words'},
     {'type': 'links', 'active': false, 'label': 'Links', 'itemType': 'link'}];
  $scope.buttonTypes.linkText = 
    [{'type': 'pages', 'active': true, 'label': 'Pages', 'itemType': 'page'}];

  // Fetch quotes from S3 - TODO: refactor to service here & crawling
  // also, add quote cycling for long loads (or speed up the load!)
  $scope.quoteList = [{"words":"a", "author":"b"}];
  $scope.quote = {};
  $http.get('quote-file.json')
    .then(function(results){
      $scope.quoteList = results.data; 
      $scope.quote = $scope.quoteList[Math.floor((Math.random()*$scope.quoteList.length))];
    });

  /*
   * selectFolder - displays the analysis of the selected folder
   *
   * args:
   *  folderName - name of the folder to make current and thus display
   */
  $scope.selectFolder = function(folderName) {
    resultsService.setCurrentAnalysis("");
    $scope.analysisAvailable = false;
    for (var i = 0; i < $scope.folderList.length; i++) {
      if (folderName === $scope.folderList[i].name) {
        $scope.currentFolder = $scope.folderList[i];
      }
    }
  }

  /*
   * selectAnalysis - make analysis current and display results
   *    
   * args:
   *  analysisId - key value for the analysis on S3
   */  
  $scope.selectAnalysis = function(analysisId) {
    resultsService.setCurrentAnalysis(analysisId);
    $scope.analysisAvailable = true;
    $scope.getAnalysis(analysisId);
  }


  /*
   * getFoldersOrAnalysis - display analysis if avilable or folders
   *    
   * args:
   *  currentAnalysis - analysis to display if available, if empty display folders
   */   
  $scope.getFoldlersOrAnalysis = function(currentAnalysis) {
 
    // If no current analysis display folders   
    if (isEmpty(currentAnalysis)) {

      $scope.analysisAvailable = false;

      folderService.getFolderList()
        .then(function(results) {
            $scope.folderList = results;
            $scope.currentFolder = $scope.folderList[0];
        }); 
    }

    // Analysis is current, so retrieve it
    else {

      $scope.analysisAvailable = true;
      $scope.getAnalysis(currentAnalysis.id);

      // still must get folders for display in side bar
      folderService.getFolderList()
        .then(function(results) {
            $scope.folderList = results;
            $scope.currentFolder = $scope.folderList[0];
        }); 
    }
  }


  /*
   * getAnalysis - retrieves crawl results from results service and performs initialization
   *
   * args:
   *  analysisId - key value for analysis on S3
   */
  $scope.getAnalysis = function(analysisId) { 

    // Initiate loading and grab a new quote
    $scope.loading = true;
    $scope.quote = $scope.quoteList[Math.floor((Math.random()*$scope.quoteList.length))];

    resultsService.getAnalysis(analysisId)
      .then(function(results){

        $scope.analysis = results;

        // Determine analysis time in minute and seconds
        $scope.summary.minutes = Math.floor($scope.analysis.time/60);
        $scope.summary.seconds = $scope.analysis.time%60;

        // Hide common ground if only 1 site
        if ($scope.analysis.sites.length < 2) {
          $scope.commonGround = false;
        }
        else {
          $scope.commonGround = true;
        }

        // Set per site information
        for (var i = 0; i < $scope.analysis.sites.length; i++) {

          // Set summary information
          $scope.summary.totalPages = $scope.summary.totalPages + 
                                      $scope.analysis.sites[i].internalResults.summary.pages.count;
          $scope.summary.totalPages = $scope.summary.totalPages + 
                                      $scope.analysis.sites[i].externalResults.summary.pages.count;
          $scope.summary.totalWords = $scope.summary.totalWords + 
                                      $scope.analysis.sites[i].internalResults.summary.words.count;
          $scope.summary.totalWords = $scope.summary.totalWords + 
                                      $scope.analysis.sites[i].externalResults.summary.words.count;
          $scope.summary.numberOfSites = $scope.summary.numberOfSites + 1;


          // Enable or Disable comparison in Common Ground
          $scope.analysis.sites[i].include = true;

          // AdditionalInfo box information for each splashdown page type
          $scope.analysis.sites[i].additionalInfo = {};
          $scope.analysis.sites[i].additionalInfo.text = 
            { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
              'currentItem': {}, 'currentType': "", 'currentLabel': ""};          
          $scope.analysis.sites[i].additionalInfo.links = 
            { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
              'currentItem': {}, 'currentType': "", 'currentLabel': ""};
          $scope.analysis.sites[i].additionalInfo.context = 
            { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
              'currentItem': {}, 'currentType': "", 'currentLabel': ""};
          $scope.analysis.sites[i].additionalInfo.synonyms = 
            { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
              'currentItem': {}, 'currentType': "", 'currentLabel': ""};
          $scope.analysis.sites[i].additionalInfo.selectors = 
            { 'showing': false, 'buttonTypes': [], 'currentButton': {}, 
              'currentItem': {}, 'currentType': "", 'currentLabel': ""};          
        }

        // Control the display of result types and internal/external buttons
        $scope.show = {'text': false, 'links': false, 'context': false, 'synonymRings': false, 
                       'selectors': false, 'internalButton': true, 'externalButton': false}

        // Show external results if no internal results and hide the internal button
        if (isEmpty($scope.analysis.sites[0].internalResults)) { 
          $scope.results = 'externalResults';
          $scope.external = true;
          $scope.show.internalButton = false;
        }

        // Show external button only if external results exist
        if (!isEmpty($scope.analysis.sites[0].externalResults)) { 
          $scope.show.externalButton = true;
        }

        // Don't show pointer if only one internal/external button exists
        if (isEmpty($scope.analysis.sites[0].internalResults) || 
            isEmpty($scope.analysis.sites[0].externalResults)) {
          $scope.soloResults = true;
        }

        // Only display text results pane if one type exists
        var textPage = ['visibleText', 'hiddenText', 'headlineText', 'searchWords'];
        for (var i = 0; i < textPage.length; i++) {
          if (!isEmpty( $scope.analysis.sites[0][$scope.results][textPage[i]])) {
            $scope.show.text = true;
          }
        }

        // Only display link results pane if one type exists
        var linkPage = ['allLinks', 'externalDomains', 'linkText'];      
        for (var i = 0; i < linkPage.length; i++) {
          if (!isEmpty( $scope.analysis.sites[0][$scope.results][linkPage[i]])) {
            $scope.show.links = true;
          }
        }
  
        // Only display other panes if results exist
        var pages = ['context', 'synonymRings', 'selectors'];
        for (var i = 0; i < pages.length; i++) {
          if (!isEmpty($scope.analysis.sites[0].internalResults[pages[i]]) || 
              !isEmpty($scope.analysis.sites[0].externalResults[pages[i]]) ) {
            $scope.show[pages[i]] = true;
          }
        }

        // Perform comparison for all sites
        $scope.compareSites();

        $scope.loading = false;
    });
  };


  /*
   * compareSites - Compare which words are common between sites
   *
   * wrapper function, inner compare function actual performs comparison
   */
  $scope.compareSites = function() {

    // Function to compare for each result type
    //
    // Essentially a set intersection of the selected sites, uses "hashing"
    // http://stackoverflow.com/questions/497338/efficient-set-intersection-algorithm
    //  Question is the efficiency of creating JS Objects?
    //  My be worth benchmarking against other methods?
    //  May be worth refactoring into helper function for JS Set Intersection 
    //
    // Args: result type - i.e. visibleText, allLinks, etc. (flag: context)
    //       itemType - i.e. word, link, domain
    //
    var compare = function(resultType, itemType) {
      var itemsList = [],
          startList = {},
          tempList = {},
          items = [],
          itemTypes = itemType + 's',
          sites = $scope.analysis.sites;
     
      // Create a list of "word lists" for each site
      for (var i = 0; i < sites.length; i++) {

        // Handle text and links
        if (sites[i].include === true && 
            resultType !== 'context' && 
            resultType !== 'synonymRings' &&
            resultType !== 'selectors') {
          itemsList.push({'site': i + 1, 
                          'items': sites[i][$scope.results][resultType][itemTypes]});
        }

        // Handle context
        if (sites[i].include === true && resultType === 'context')  { 
          itemsList.push({'site': i + 1, 
                          'items': sites[i][$scope.results].context.contextWords[itemType].words});
        }

        // Handle synonym rings
        if (sites[i].include === true && resultType === 'synonymRings')  { 
          itemsList.push({'site': i + 1, 
                          'items': sites[i][$scope.results].synonymRings.rings[itemType].words});
        }

        // Handle selectors
        if (sites[i].include === true && resultType === 'selectors')  { 
          itemsList.push({'site': i + 1, 
                          'items': sites[i][$scope.results].selectors[itemType].words});
        }

      }

      if (resultType === 'context' || 
          resultType === 'synonymRings' || 
          resultType === 'selectors') {
        itemType = 'word';
        itemTypes = 'words';
      }

      // Only process if there are lists to process
      if (itemsList.length > 0) {
        
        // set up initial start list
        items = itemsList[0].items
        for (var i = 0; i < items.length; i++) {
          startList[items[i][itemType]] = [items[i].rank];
        }

        // compare the other lists, skip the first
        for (var i = 1; i < itemsList.length; i++) {
          
          // clear temp list
          tempList = {};

          // Check items in current list to see if they are in starting list
          items = itemsList[i].items
          for (var j = 0; j < items.length; j++) {

            // only add items from new list if in hash of starting list
            if (typeof startList[items[j][itemType]] !== "undefined") {

              // set templist word rank = to rank of start list word
              // and push current list rank to list
              tempList[items[j][itemType]] = startList[items[j][itemType]];
              tempList[items[j][itemType]].push(items[j].rank);
            }
          }

          // set new start list to current templist
          startList = tempList;
        }

        // Common Items are in the last startlist
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

    // Compare all formats
    if (!isEmpty($scope.analysis.sites[0][$scope.results].visibleText)) {
      $scope.commonWords['visibleText'] = compare('visibleText', 'word');
    }
    if (!isEmpty($scope.analysis.sites[0][$scope.results].headlineText)) {
      $scope.commonWords['headlineText'] = compare('headlineText', 'word');
    }
    if (!isEmpty($scope.analysis.sites[0][$scope.results].hiddenText)) {
      $scope.commonWords['hiddenText'] = compare('hiddenText', 'word');
    }
      
    if (!isEmpty($scope.analysis.sites[0][$scope.results].allLinks)) {
      $scope.commonWords['allLinks'] = compare('allLinks', 'link');
    }
    if (!isEmpty($scope.analysis.sites[0][$scope.results].externalDomains)) {
      $scope.commonWords['externalDomains'] = compare('externalDomains', 'domain');
    }
    if (!isEmpty($scope.analysis.sites[0][$scope.results].linkText)) {
      $scope.commonWords['linkText'] = compare('linkText', 'word');
    }

    // Special handling for context synonymRings, selectors,
    // itemType is the incrementor for contextWord[i], rings[i], selectors[i]
    var contextWords = $scope.analysis.sites[0][$scope.results].context.contextWords || [];
    for (var i = 0; i < contextWords.length; i++) {
      $scope.commonWords[contextWords[i].word] = compare('context', i);
    }

    var synonymRings = $scope.analysis.sites[0][$scope.results].synonymRings.rings || [];
    for (var i = 0; i < synonymRings.length; i++) {
      $scope.commonWords[synonymRings[i].net] = compare('synonymRings', i);
    }

    var selectors = $scope.analysis.sites[0][$scope.results].selectors || [];
    for (var i = 0; i < selectors.length; i++) {
      $scope.commonWords[selectors[i].name] = compare('selectors', i);
    }

    // Set up common colors
    $scope.commonColors = [];
    var sites = $scope.analysis.sites;

    for (var i = 0; i < sites.length; i++) {
      if (sites[i].include === true) {
        $scope.commonColors.push((i + 1) % 5);
      }
    }
  }


  /*
   * resultsChoice - selects between internal and external results
   *
   * args:
   *  type - external or internal
   */
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
    if (addInfo.currentItem === item) {
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


  // Check if analysis available to display on page load
  var currentAnalysis = resultsService.getCurrentAnalysis();

  // Then display analysis or folders
  $scope.getFoldlersOrAnalysis(currentAnalysis);

}]);
