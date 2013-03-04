'use strict';

spiderwebApp.controller('CrawlingCtrl', function($scope, $timeout, $http, crawlService) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];


  // Get the appropriate text margin
  $scope.maxPages = 5000; // get from crawlService

  // need to adjust for 20 page free, just start at 10 seconds?
  var remainingTime = $scope.maxPages/20; // (20 pages seconds)
  $scope.pagesCrawled = 0; // get from crawlService

  // get the page count
  $scope.pageCount = {} //crawlService.getCrawlStatus();

  var progressNumber = 10;
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

  var progress = function(progressNumber) {
    
    if ($scope.pagesCrawled === $scope.maxPages) {
      return;
    }

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
      progress(progressNumber);
    }, 50);
  }

  progressNumber = 0;
  progress(progressNumber);

});
