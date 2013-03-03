'use strict';

spiderwebApp.controller('TemplateCtrl', function($scope, $dialog, sessionService) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  // TODO: onload need to check for (and set) name in cookies
  $scope.name = "" //empty if not logged in

  $scope.opts = {
    backdrop: true,
    keyboard: false,
    backdropClick: false,
    templateUrl: 'views/login.html', 
    controller: 'LoginController'
  };

  $scope.openLogin = function(){
    var d = $dialog.dialog($scope.opts);
    d.open().then(function(result){
      if(result) {
        if (result.login === 'success') {
          $scope.name = result.name;
          sessionService.setUserName(result.name);
          sessionService.setShortSession(result.short_session);
          sessionService.setLongSession(result.long_session);
        }
        else {
          // login cancelled
        }
        //alert('results: ' + result.login);
      }
    });
  };

  $scope.signout = function() {

    // need to logout out on server and remove session id from redis
    // need to remove local session cookie with user name
    $scope.name = "";
  };

  // MESSAGE BOX NOT CURRENTLY USED
  $scope.openMessageBox = function(){
    var title = 'This is a message box';
    var msg = 'This is the content of the message box';
    var btns = [{result:'cancel', label: 'Cancel'}, {result:'ok', label: 'OK', cssClass: 'btn-primary'}];

    $dialog.messageBox(title, msg, btns)
      .open()
      .then(function(result){
        alert('dialog closed with result: ' + result);
    });
  };
});

// the dialog is injected in the specified controller
function LoginController($scope, $http, dialog){

  $scope.error = {};
  $scope.error.show = false;
  $scope.error.message = ""

  $scope.close = function(result, btn){

    if (btn === 'login') {
      // Why don't I need this?
      //$http.defaults.useXDomain = true;

      if (typeof result !== 'undefined' && 
          typeof result.user !== 'undefined' &&
          result.user !== "" &&
          typeof result.password !== 'undefined' &&
          result.password !== "") {

        var url = 'http://localhost:8000/checkusercredentials',
            data = {};

        data.user = result.user;
        data.password = result.password;

        $http.post(url, data)
          .success(function(data, status, headers, config){
            
            if (data.login === "success") {
              dialog.close(data);              
            }
            else {
              $scope.error.show = true;
              $scope.error.message = "Invalid Email and Password."
            }

          })
          .error(function(data, status, headers, config){
            $scope.error.show = true;
            $scope.error.message = "Server Error."
          });
      }
      else {
        $scope.error.show = true;
        $scope.error.message = "Must enter both email and password."
      }
    }

    else {
      dialog.close('cancelled');
    }

  };
}
