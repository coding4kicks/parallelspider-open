'use strict';

spiderwebApp.controller('LoginCtrl', function($scope, $http) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];
  $scope.returnValue = "pleaseChange";

  $scope.parsefunc = function(data) {
    $scope.data = data;
  }

  $scope.logIn = function() {
    //alert($scope.user);
    //alert($scope.password);

    //$http.defaults.useXDomain = true;

    //data = {'user':$scope.user, 'password':$scope.password};
  
    //$http.get('http://localhost:8000/checkusercredentials?user=spideradmin&password=123')
    //$http.get('results5.json')
    //$http.jsonp('http://localhost:8000/checkusercredentials?user=spideradmin&password=123&callback=JSON_CALLBACK')
     // .success(function(data){
     //   console.log(data.found);
      //  alert('here');
       // //alert(results);
      //});

     //var url = "http://public-api.wordpress.com/rest/v1/sites/wtmpeachtest.wordpress.com/posts?callback=JSON_CALLBACK";

    //var url = "http://localhost:8000/?callback=JSON_CALLBACK";
    var url = 'http://localhost:8000/checkusercredentials?user=spideradmin&password=123&callback=JSON_CALLBACK';
    console.log('here');
        $http.jsonp(url)
            .success(function(data){
                alert('here');
                console.log(data.login);
            });

  };  
});
