'use strict';

spiderwebApp.controller('LoginCtrl', function($scope, $http) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];
  $scope.returnValue = "pleaseChange";

  $scope.logIn = function() {
    alert($scope.user);
    alert($scope.password);

    $http.defaults.useXDomain = true;

    //data = {'user':$scope.user, 'password':$scope.password};

    //$http.get('http://localhost:8000/checkusercredentials?user=spideradmin&password=123')
    //$http.get('results5.json')
    $http.jsonp('http://localhost:8000/')
      .then(function(results){
        alert('here');
      });

  };  
});
