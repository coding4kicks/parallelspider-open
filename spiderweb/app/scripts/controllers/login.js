'use strict';
// NOT USING - logic is in template
spiderwebApp.controller('LoginCtrl', function($scope, $http) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];
  $scope.returnValue = "pleaseChange";

  $scope.logIn = function() {

    // Why don't I need this?
    //$http.defaults.useXDomain = true;

    var url = 'http://localhost:8000/checkusercredentials?user='
              + $scope.user + '&' + 'password=' + $scope.password 
              + '&callback=JSON_CALLBACK';

    $http.get(url)
      .success(function(data, status, headers, config){
        console.log(data.login);
        $scope.returnValue = data.fullname;
      });

  };  
});
