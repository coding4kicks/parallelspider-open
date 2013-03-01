'use strict';

spiderwebApp.controller('MainCtrl', function($scope, $http, $timeout) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  ////////////////////////////
  // HANGING SPIDER ANIMATION
  ////////////////////////////

  // Top margin for the hang'n spiders
  $scope.spider1Margin = '0px';
  $scope.spider2Margin = '0px';
  $scope.spider3Margin = '0px';

  // Top margin for the hidden text boxes
  $scope.text1Margin = '-150px';
  $scope.text2Margin = '-150px';
  $scope.text3Margin = '-150px';

  // Move a hanging spider up or down by its margin-top
  $scope.move = function(spider) {

    // Get the appropriate text margin
    var text = "text" + spider.slice(6,13);
    var textPosition;

    // Animate up if at the bottom (account for -0px at end of down)
    if ($scope[spider] === '0px' || $scope[spider] === '-0px') {
      var animateUp = function(position, textPosition) {
        position = position + 5;
        $scope[spider] = '-' + position + 'px';

        // Adjust text margin
        textPosition = textPosition - 5;
        $scope[text] = (-1 * textPosition) + 'px';

        // Call again if not done
        if (position < 175){
          $timeout( function() {
            animateUp(position, textPosition);
          }, 10);
        }
      };
      animateUp(0, 150);  
    }

    // Animate down if not at bottom, returns -0px at finish
    else { 
      var animateDown = function(position, textPosition) {
        position = position - 5;
        $scope[spider] = '-' + position + 'px';

        // Adjust text margin
        textPosition = textPosition - 5;
        $scope[text] = textPosition + 'px';

        // Call again if not done
        if (position > 0){
          $timeout( function() {
            animateDown(position, textPosition);
          }, 10);
        }
      };
      animateDown(170, 20);
    };
  };

  ////////////////////////////
  // FOR BLOCK ANIMATION
  ////////////////////////////

  $scope.for1MarginLeft = '0px';
  $scope.for1MarginTop = '0px';
  $scope.for2MarginLeft = '0px';
  $scope.for2MarginTop = '0px';
  $scope.for3MarginLeft = '0px';
  $scope.for3MarginTop = '0px';

  $scope.text1MarginTop = '-50px';
  $scope.text1Visibility = 'hidden';
  $scope.text2MarginTop = '-50px';
  $scope.text2Visibility = 'hidden';
  $scope.text3MarginTop = '-50px';
  $scope.text3Visibility = 'hidden';

  $scope.animate = function(forBlock) {

    var leftMargin = forBlock + 'Left',
        topMargin = forBlock + 'Top';

     // Get the appropriate text margin
    var text = "text" + forBlock.slice(3,13) + 'Top';
    var textPosition;
    var textVisibility = text.slice(0,5) + 'Visibility';

    if ($scope[leftMargin] === '0px' || $scope[leftMargin] === '-0px') {
      var animateUpLeft = function(position, textPosition) {
        position = position + 5;
        $scope[leftMargin] = (-1 * position) + 'px';
        $scope[topMargin] = (-1 * position) + 'px';

        // Adjust text margin
        textPosition = textPosition - 5;
        $scope[text] = (-1 * textPosition) + 'px';

        // Call again if not done
        if (position < 35){
          $timeout( function() {
            animateUpLeft(position, textPosition);
          }, 10);
        }
      };
      animateUpLeft(0, 50);    
      $scope[textVisibility] = 'visible'; 
    }

    else {
      var animateDownRight = function(position, textPosition) {
        position = position - 5;
        $scope[leftMargin] = (-1 * position) + 'px';
        $scope[topMargin] = (-1 * position) + 'px';

        // Adjust text margin
        textPosition = textPosition - 5;
        $scope[text] = textPosition + 'px';

        // Call again if not done
        if (position > 0){
          $timeout( function() {
            animateDownRight(position, textPosition);
          }, 10);
        }
      };
      animateDownRight(35, -15);
      $scope[textVisibility] = 'hidden'; 
    };
  }

  ////////////////////////////
  // ADVANCED OPTIONS DISPLAY
  ////////////////////////////
  $scope.showAdvOpts = false;
  $scope.spanSize = 'span8';
  $scope.advOptMargin = '-30px';

  $scope.showOptions = function() {

    if ($scope.spanSize==='span12') {
      $scope.spanSize='span8';
    }
    else {
      $scope.spanSize='span12';
    }
    $scope.showAdvOpts=!$scope.showAdvOpts;
  }

  ////////////////////////////
  // CRAWL INFO + ADV OPTS FORMS
  ////////////////////////////
  $scope.crawl = {};

  $scope.crawl.additionalSites = [];
  $scope.additionalSites;

  $scope.crawl.wordSearches = [];
  $scope.wordSearches;

  $scope.crawl.wordContexts = [];
  $scope.wordContexts;

  $scope.predefinedSynRings = [{name: 'none', title: 'None'}, 
                               {name: 'curseWords', title: 'Curse Words'},
                               {name: 'racistLang', title: 'Racist Language'},
                               {name: 'drugRefs', title: 'Drug References'}];

  $scope.crawl.wordnets = [];
  $scope.wordnets;

  $scope.crawl.customSynRings = [];
  $scope.customSynRings;

  $scope.crawl.xpathSelectors = [];
  $scope.xpathSelectors;

  $scope.crawl.cssSelectors = [];
  $scope.cssSelectors;

  // scope[type] is the the model item in the form input
  // scope.crawl[type] is the list of all items added
  $scope.add = function(type) {
    var input = $scope[type]
    if (typeof input !== "undefined" && input != "") {
      // need to copy objects
      if (input instanceof Object) {
        var copy = {};
				for ( var property in input ) copy[property] = input[property];
        $scope.crawl[type].push(copy);        
      }
      else { // other type is array, and strings are immutable
        $scope.crawl[type].push(input);
      }
    }    
  }

  $scope.remove = function(type, index) {
    $scope.crawl[type].remove(index);        
  }

  ////////////////////////////
  // CRAWL SUBMISSION
  ////////////////////////////
  $scope.attemptedSubmission = false;

  // TODO: refactor crawl to list of items so can iterate through on server

  $scope.crawlSite = function() {
    var url = 'http://localhost:8000/initiatecrawl';

    if (typeof $scope.crawl.maxPages !== "undefined" &&
        $scope.crawl.maxPages > 20) {
      if ($scope.name !== "") {

        // TODO: refactor to crawl service
        $http.post(url, $scope.crawl)
          .success(function(data, status, headers, config){
            
            if (data.loggedIn) {
              alert("initiated");              
            }
            else {
              $scope.openLogin();
            }

          })
          .error(function(data, status, headers, config){
            alert("Server Error. Unable to Crawl, Sorry.");
          });       
      }
      else {
        alert("Must sign in to initiate crawl greater than 20 pages.");
        $scope.openLogin();
      }
    }
    else{

      $http.post(url, $scope.crawl)
        .success(function(data, status, headers, config){
          
            alert("initiated");              

        })
        .error(function(data, status, headers, config){
          alert("Server Error. Unable to Crawl, Sorry.");
        }); 
    }
    console.log($scope.crawl);
  }
  
});

