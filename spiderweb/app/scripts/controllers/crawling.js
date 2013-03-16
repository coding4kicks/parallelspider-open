'use strict';

/*
 * Crawling Controller
 *
 * Tracks crawl status and redirects to splashdown when complete.
 * Crawl Progress is based on planned 20 pages per second
 *  - deviations +/- 100 cause status bar to stop or jump
 * Updates user's folder info by adding new crawl
 *
 * Functions:
 *  Initializing - Shows initializing display until the crawl starts
 *  Crawling - Updates progress and crawl info during the crawl
 *
 */ 

spiderwebApp.controller('CrawlingCtrl', function($scope, $timeout, $http, $q, $location, configService, resultsService, crawlService, folderService) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  // Get crawl info
  $scope.maxPages = crawlService.getMaxPages();
  var crawl = {};
  crawl.id = crawlService.getCrawlId();
  crawl.name = crawlService.getCrawlName();
  crawl.date = crawlService.getCrawlDate();

  // TODO: need to adjust for 20 page free, just start at 10 seconds?
  var remainingTime = $scope.maxPages/20; // (20 pages per second)

  // The pages displayed in the counter
  $scope.pagesCrawled = 0; // get from crawlService???

  // The pages crawled count from the server
  $scope.pageCount = {} //crawlService.getCrawlStatus();
  $scope.pageCount.count = -1; // -1 for initialization

  // Set up status control variables for controlling display
  $scope.status = {};
  $scope.status.initializing = true;
  $scope.status.crawling = false;


  var progressNumber = 0;
  $scope.progress = progressNumber + "%";

  var crawling = true,
      counter = 0;
      
  $scope.quoteList = [{"words":"a", "author":"b"}];
  $scope.quote = {};

  // Determine analysis time in minute and seconds
  $scope.time = {}
  $scope.time.minutes = Math.floor(remainingTime/60);
  $scope.time.seconds = remainingTime%60;

  // Fetch quotes from S3 
  // TODO: ? do I need to refactor to config for deployment?
  $http.get('quote-file.json')
    .then(function(results){
      $scope.quoteList = results.data; 
      $scope.quote = $scope.quoteList[Math.floor((Math.random()*$scope.quoteList.length))];
    });

  // Initializing - waiting for the crawl start
  var initializing = function(progressNumber) {

    // Check status from the server
    crawlService.getCrawlStatus()
      .then(function(results){
        $scope.pageCount = results
    });

    // Initialize until server says otherwise
    if ($scope.pageCount.count === -1) {
      $timeout( function() {
        initializing();
      }, 500);
    }
    else {
      $scope.status.initializing = false;
      $scope.status.crawling = true;
      crawling(progressNumber);
    }
  };

  var crawling = function(progressNumber) {

    // If recieve complete response from server
    if ($scope.pageCount.count === -2) {

      // Mocking. Must pass predifined crawl id to results and folders
      if (configService.getMock() === true) {
        resultsService.setCurrentAnalysis('results1SiteSearchOnly');        
        folderService.addAnalysis(configService.getDefaultFolder(), 
                                  crawl.name, crawl.date, crawl.id)
          .then(function(results) {
            // Stop crawling and redirect to splashdown page
            $scope.status.crawling = false;
            $location.path('/splashdown').replace();
          });
      }

      // Not mocking so set crawl id as current and update user's folder info
      else {
        resultsService.setCurrentAnalysis(crawlId);
        folderService.addAnalysis(configService.getDefaultFolder(), 
                                  crawl.name, crawl.date, crawl.id)
          .then(function(results) {
            // Stop crawling and redirect to splashdown page
            $scope.status.crawling = false;
            $location.path('/splashdown').replace();
          });
      }      
    }

    // If too far behind server count, jump pages crawled
    // TODO: Need separate adjustment for time?
    if (($scope.pageCount.count - $scope.pagesCrawled) > 100) {
      $scope.pagesCrawled = $scope.pageCount.count;
    }
   
    // Only increment bar and counters if less than max
    // and if not too far ahead of actual count on server
    if ($scope.pagesCrawled < $scope.maxPages &&
        ($scope.pagesCrawled - $scope.pageCount.count) < 100) {
    
      // Time remaining should count down evey second
      if (counter % 20 === 0) {
        remainingTime -= 1;
        $scope.time.minutes = Math.floor(remainingTime/60);
        $scope.time.seconds = remainingTime%60;
      }

      // Pages counted increases at 20 per second
      $scope.pagesCrawled += 1;

      // Progress is the percentage of pages counted with max as the total
      progressNumber = $scope.pagesCrawled/$scope.maxPages * 100;
      $scope.progress = progressNumber + "%";

      // Change quotes (and picture eventually) every 20 seconds
      if (counter % 300 === 0) {
        $scope.quote = $scope.quoteList[Math.floor((Math.random()*$scope.quoteList.length))];
      }
    }

    // Update page count every 5 seconds
    if (counter % 100 === 0) {
      crawlService.getCrawlStatus()
        .then(function(results){
          $scope.pageCount = results
        });
    }

    // Count 1/20th of a second
    counter += 1;
    if ($scope.status.crawling) {
      $timeout( function() {
        crawling(progressNumber);
      }, 50);
    }
  };

  // Start whole thing off with initializing
  initializing(progressNumber);

});
