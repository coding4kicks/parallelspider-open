'use strict';


spiderwebApp.controller('MainCtrl', function($scope, $timeout) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  // Top margin for the hang'n spiders
  $scope.spider1Margin = '0px';
  $scope.spider2Margin = '0px';
  $scope.spider3Margin = '0px';

  // Move a hanging spider up or down by its margin-top
  $scope.move = function(spider) {
    if ($scope[spider] === '0px' || $scope[spider] === '-0px') {
      var animateUp = function(position) {
        position = position + 5;
        $scope[spider] = '-' + position + 'px';
        if (position < 170){
          $timeout( function() {
            animateUp(position);
          }, 10);
        }
      };
      animateUp(0);  
    }
    else { 
      var animateDown = function(position) {
        position = position - 5;
        $scope[spider] = '-' + position + 'px';
        if (position > 0){
          $timeout( function() {
            animateDown(position);
          }, 10);
        }
      };
      animateDown(170);
      $scope[spider] = '0px' 
    };
  };

});
