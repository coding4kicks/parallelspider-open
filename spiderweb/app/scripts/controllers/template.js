'use strict';

spiderwebApp.controller('TemplateCtrl', function($scope, $dialog, $cookieStore, $http, sessionService, configService) {
  $scope.awesomeThings = [
    'HTML5 Boilerplate',
    'AngularJS',
    'Testacular'
  ];

  // 
  angular.element(window).bind('resize', function(){
    var height = window.innerHeight - 190;
    $scope.minHeight = height + 'px';
    $scope.$digest();    
  });

  // Onload name is pulled from cookies by app.run()
  $scope.name = sessionService.getUserName(); //empty if not logged in

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

          // set displayed name 
          $scope.name = result.name;

          // set in session service
          sessionService.setUserName(result.name);
          sessionService.setShortSession(result.short_session);
          sessionService.setLongSession(result.long_session);

          // set in cookie store
          $cookieStore.put('ps_longsession', result.long_session);
          $cookieStore.put('ps_shortsession', result.short_session);
          $cookieStore.put('ps_username', result.name);
        }
        else {
          // login cancelled
        }
        //alert('results: ' + result.login);
      }
    });
  };

  $scope.signout = function() {
    // TODO: need to remove local session cookie with user name

    // Configure resource fetch details
    var url = configService.getProtocol() + '://' + 
              configService.getHost() + '/signout',
        data = {'shortSession': sessionService.getShortSession(),
                'longSession': sessionService.getLongSession() };
        //deferred = $q.defer();


    $http.post(url, data)
      .success(function(data, status, headers, config){
        console.log('logged out');

        // Delete cookies and remove session variables and name from scope
        $cookieStore.remove('ps_longsession');
        $cookieStore.remove('ps_shortsession');
        $cookieStore.remove('ps_username');
        sessionService.setShortSession("");
        sessionService.setLongSession("");
        $scope.name = "";

      })
      .error(function(data, status, headers, config){
        console.log('error');
      });

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
function LoginController($scope, $http, dialog, configService){

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

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/checkusercredentials',
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
