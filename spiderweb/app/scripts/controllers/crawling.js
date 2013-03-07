'use strict';

spiderwebApp.controller('CrawlingCtrl', function($scope, $timeout, $http, $location, crawlService) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];


  // Get the max number of pages to crawl
  $scope.maxPages = crawlService.getMaxPages(); //TODO: get from crawlService

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

  $http.get('quote-file.json')
    .then(function(results){
      $scope.quoteList = results.data; 
      $scope.quote = $scope.quoteList[Math.floor((Math.random()*$scope.quoteList.length))];
    });

  // Check service for crawl start
  var initializing = function(progressNumber) {

    crawlService.getCrawlStatus()
      .then(function(results){
        $scope.pageCount = results
    });

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
   
    // Only increment bar and counters if less than max
    if ($scope.pagesCrawled < $scope.maxPages) {

      // Need a mechanism to slow down and stop counter if pageCount.count
      // gets too far behind
    
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

    // Once complete, redirect to splashdown
    if ($scope.pageCount.count === -2) {
      $location.path('/splashdown');
      $scope.apply;
    }

    // Update page count every 5 seconds
    if (counter % 100 === 0) {
      crawlService.getCrawlStatus()
        .then(function(results){
          $scope.pageCount = results
        });
      console.log($scope.pageCount);
    }

    // Count 1/20th of a second
    counter += 1;
    $timeout( function() {
      crawling(progressNumber);
    }, 50);
  };

  initializing(progressNumber);

});
