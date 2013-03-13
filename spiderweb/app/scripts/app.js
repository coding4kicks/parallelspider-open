'use strict';

var spiderwebApp = angular.module('spiderwebApp', ['ngCookies'])
  .config(['$routeProvider','$locationProvider', function($routeProvider, $locationProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'views/main.html',
        controller: 'MainCtrl'
      })
      .when('/ourwords', {
        templateUrl: 'views/ourwords.html',
        controller: 'OurwordsCtrl'
      })
      .when('/ourwords/:pageName', {
        templateUrl: 'views/ourwords.html',
        controller: 'OurwordsCtrl'
      })
      .when('/launchpad', {
        templateUrl: 'views/launchpad.html',
        controller: 'LaunchpadCtrl'
      })
      .when('/spiderdiaries', {
        templateUrl: 'views/spiderdiaries.html',
        controller: 'SpiderdiariesCtrl'
      })
      .when('/spiderdiaries/:pageType/:pageName', {
        templateUrl: 'views/spiderdiaries.html',
        controller: 'SpiderdiariesCtrl'
      })
      .when('/splashdown', {
        templateUrl: 'views/splashdown.html',
        controller: 'SplashdownCtrl'
      })
      .when('/splashdown/result/:resultId', {
        templateUrl: 'views/splashdown.html',
        controller: 'SplashdownCtrl'
      })
      .when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl'
      })
      .when('/myaccount/accountId', {
        templateUrl: 'views/myaccount.html',
        controller: 'MyaccountCtrl'
      })
      .when('/signup', {
        templateUrl: 'views/signup.html',
        controller: 'SignupCtrl'
      })
      .when('/crawling', {
        templateUrl: 'views/crawling.html',
        controller: 'CrawlingCtrl'
      })
      .otherwise({
        redirectTo: '/'
      });

    //$locationProvider.html5Mode(true);
    
  }])


  ////////////////////////////
  // SERVICES
  ////////////////////////////
  .service('configService', function() {
    // change4deployment
    var host = 'localhost:8000',
        protocol = 'http';

    return {
      setHost: function (configHost) {
        host = configHost;
      },
      getHost: function () {
        return host;
      },
      setProtocol: function (configProtocol) {
        protocol = configProtocol;
      },
      getProtocol: function () {
        return protocol;
      }

    };
  })

  .service('resultsService', function ($http, $q, sessionService, configService) {

    // Where am I setting this???
    // Either get the results passed, the current if one is set, or none
    var currentAnalysis = {};
    //var currentAnalysis = {'id': 'results1SiteSearchOnly'};
    
    return {
      getAnalysis:function (analysisId) {

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/gets3signature',
            data = {'analysisId': analysisId,
                    'shortSession': sessionService.getShortSession(),
                    'longSession': sessionService.getLongSession() },
            deferred = $q.defer();
        alert(data.analysisId);
        $http.post(url, data)
          .success(function(data, status, headers, config){
            console.log(data.url);
            if (data.url !== 'error') {
              $http.get(data.url)
                .success(function(data, status, headers, config){
                  deferred.resolve(data);
                })
                .error(function(data, status, headers, config){
                  console.log('error');
                });
            }
            else {
              console.log('error');
            }
          })
          .error(function(data, status, headers, config){
            console.log("error");
          });

        return deferred.promise;
        // Must later account for user ???
        //return currentAnalysis;
      },

      getCurrentAnalysis: function () {
        return currentAnalysis;
      },

      setCurrentAnalysis: function (analysis) {
        currentAnalysis = analysis;
      },

      listAnalyses:function () {
        // This function will take the "user"??? and list their analyses
        // later funcionality should also allow them to place analysis into folders like gmail
        // even later timeseries analysis should be enabled.
      }
    };
  })

  // Manage Session State
  .service('sessionService', function() {
    var longSession = "",  // General info and analysis access
        shortSession = "", // Purchase and change user info session
        userName = "";

    return {
      setShortSession:function (session) {
        shortSession = session;
        // set in cookie too?
      },
      getShortSession:function () {
        // try to retrieve from cookie if empty
        return shortSession;
      },
      setLongSession:function (session) {
        longSession = session;
        // set in cookie
      },
      getLongSession:function (session) {
        return longSession;
      },
      setUserName: function (name) {
        userName = name;
      },
      getUserName: function () {
        // try to get from cookie if empty
        return userName;
      }
    };
  })

  .service('crawlService', function ($http, $q, sessionService, configService) {
    var crawlId = "",
        maxPages = 0;
    
    return {
      getCrawlId:function () {
        return crawlId;
      },
      setCrawlId:function (id) {
        crawlId = id;
      },

      getMaxPages:function () {
        return maxPages;
      },

      setMaxPages:function (pages) {
        maxPages = pages;
      },

      getCrawlStatus:function () {

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/checkcrawlstatus',
            data = {'id': crawlId, 
                    'shortSession': sessionService.getShortSession(),
                    'longSession': sessionService.getLongSession() },
            deferred = $q.defer();


        $http.post(url, data)
          .success(function(data, status, headers, config){
            deferred.resolve(data);
          })
          .error(function(data, status, headers, config){
            console.log('error');
          });

        return deferred.promise;
      }
    };
  })


  ////////////////////////////
  // DIRECTIVES
  ////////////////////////////

  // Adjusts view size so footer is never higher up than bottom of page
  // Made 10 px too big so scroll bar is always there and things don't jump
  .directive('psFullscreen', function() {

    // TODO: possibly adjust for window resize;
    // http://www.javascripter.net/faq/browserw.htm
    // http://jsfiddle.net/ShadowBelmolve/c2B2z/13/
    return function(scope, element, attrs) {
      var height = window.innerHeight - 190;
      scope.minHeight = height + 'px';
    }  
  })

  // ON HOLD - unable to get filter working, haven't even tried linking addInfo box
  //  <analysisbox title="visibleText" name="Visible Text" site="site" results="results" searchText="searchText"></analysisbox>
  // Analysis box to display word, links, domains, etc.
  // Depends upon site, request, and searchText in parent scope
//  .directive( 'analysisbox', function () {
//    return {
//      restrict: 'E',
//      replace: true,
//      scope: { type: "@title", name: "@", site: "&", results: "&", searchText: "&"},
//      templateUrl: 'views/analysisbox/analysisbox.html',
//      link: function(scope, element, attrs) {
//
//        scope.$watch(function() {
//          return scope.site()
//          }, 
//          function(value) {
//            scope.localSite = value;     
//          });
//
//        scope.$watch(function() {
//          return scope.results()
//          }, 
//          function(value) {
//            scope.localResults = value;     
//          });
//
//        scope.$watch(function() {
//          return scope.searchText()
//          }, 
//          function(value) {
//            scope.localSearchText = value;     
//          });
//      }
//    };
//
//  })
//

  // Validates integers (from Angular websites)
  .directive('integer', function() {
    var INTEGER_REGEXP = /^\-?\d*$/;
    return {
      require: 'ngModel',
      link: function(scope, elm, attrs, ctrl) {
        ctrl.$parsers.unshift(function(viewValue) {
          if (INTEGER_REGEXP.test(viewValue)) {
            // it is valid
            ctrl.$setValidity('integer', true);
            return viewValue;
          } else {
            // it is invalid, return undefined (no model update)
            ctrl.$setValidity('integer', false);
            return undefined;
          }
        });
      }
    };
  })

  // Tooltip directive from Angular UI bootstrap
  .directive( 'tooltipPopup', function () {
    return {
      restrict: 'E',
      replace: true,
      scope: { tooltipTitle: '@', placement: '@', animation: '&', isOpen: '&' },
      templateUrl: 'views/tooltip/tooltip-popup.html'
    };
  })

  .directive( 'tooltip', [ '$compile', '$timeout', '$parse', function ( $compile, $timeout, $parse ) {
    
    var template =
      '<tooltip-popup '+
        'tooltip-title="{{tt_tooltip}}" '+
        'placement="{{tt_placement}}" '+
        'animation="tt_animation()" '+
        'is-open="tt_isOpen"'+
        '>'+
      '</tooltip-popup>';
    
    return {
      scope: true,
      link: function ( scope, element, attr ) {
        var tooltip = $compile( template )( scope ),
            transitionTimeout;

        attr.$observe( 'tooltip', function ( val ) {
          scope.tt_tooltip = val;
        });

        attr.$observe( 'tooltipPlacement', function ( val ) {
          // If no placement was provided, default to 'top'.
          scope.tt_placement = val || 'top';
        });

        attr.$observe( 'tooltipAnimation', function ( val ) {
          scope.tt_animation = $parse( val );
        });

        // By default, the tooltip is not open.
        scope.tt_isOpen = false;
        
        // Calculate the current position and size of the directive element.
        function getPosition() {
          return {
            width: element.prop( 'offsetWidth' ),
            height: element.prop( 'offsetHeight' ),
            top: element.prop( 'offsetTop' ),
            left: element.prop( 'offsetLeft' )
          };
        }
        
        // Show the tooltip popup element.
        function show() {
          var position,
              ttWidth,
              ttHeight,
              ttPosition;
            
          // If there is a pending remove transition, we must cancel it, lest the
          // toolip be mysteriously removed.
          if ( transitionTimeout ) {
            $timeout.cancel( transitionTimeout );
          }
          
          // Set the initial positioning.
          tooltip.css({ top: 0, left: 0, display: 'block' });
          
          // Now we add it to the DOM because need some info about it. But it's not
          // visible yet anyway.
          element.after( tooltip );
          
          // Get the position of the directive element.
          position = getPosition();
          
          // Get the height and width of the tooltip so we can center it.
          ttWidth = tooltip.prop( 'offsetWidth' );
          ttHeight = tooltip.prop( 'offsetHeight' );
          
          // Calculate the tooltip's top and left coordinates to center it with
          // this directive.
          switch ( scope.tt_placement ) {
            case 'right':
              ttPosition = {
                top: (position.top + position.height / 2 - ttHeight / 2) + 'px',
                left: (position.left + position.width) + 'px'
              };
              break;
            case 'bottom':
              ttPosition = {
                top: (position.top + position.height) + 'px',
                left: (position.left + position.width / 2 - ttWidth / 2) + 'px'
              };
              break;
            case 'left':
              ttPosition = {
                top: (position.top + position.height / 2 - ttHeight / 2) + 'px',
                left: (position.left - ttWidth) + 'px'
              };
              break;
            default:
              ttPosition = {
                top: (position.top - ttHeight) + 'px',
                left: (position.left + position.width / 2 - ttWidth / 2) + 'px'
              };
              break;
          }
          
          // Now set the calculated positioning.
          tooltip.css( ttPosition );
            
          // And show the tooltip.
          scope.tt_isOpen = true;
        }
        
        // Hide the tooltip popup element.
        function hide() {
          // First things first: we don't show it anymore.
          //tooltip.removeClass( 'in' );
          scope.tt_isOpen = false;
          
          // And now we remove it from the DOM. However, if we have animation, we
          // need to wait for it to expire beforehand.
          // FIXME: this is a placeholder for a port of the transitions library.
          if ( angular.isDefined( scope.tt_animation ) && scope.tt_animation() ) {
            transitionTimeout = $timeout( function () { tooltip.remove(); }, 500 );
          } else {
            tooltip.remove();
          }
        }
        
        // Register the event listeners.
        element.bind( 'mouseenter', function() {
          scope.$apply( show );
        });
        element.bind( 'mouseleave', function() {
          scope.$apply( hide );
        });
      }
    };
  }])

  //
  // Tabs directive from angular UI bootstrap
  //
  .controller('TabsController', ['$scope', '$element', function($scope, $element) {
    var panes = $scope.panes = [];
  
    this.select = $scope.select = function selectPane(pane) {
      angular.forEach(panes, function(pane) {
        pane.selected = false;
      });
      pane.selected = true;
    };
  
    this.addPane = function addPane(pane) {
      if (!panes.length) {
        $scope.select(pane);
      }
      panes.push(pane);
    };
  
    this.removePane = function removePane(pane) {
      var index = panes.indexOf(pane);
      panes.splice(index, 1);
      //Select a new pane if removed pane was selected
      if (pane.selected && panes.length > 0) {
        $scope.select(panes[index < panes.length ? index : index-1]);
      }
    };
  }])
  .directive('tabs', function() {
    return {
      restrict: 'EA',
      transclude: true,
      scope: {},
      controller: 'TabsController',
      templateUrl: 'views/tabs/tabs.html',
      replace: true
    };
  })
  .directive('pane', ['$parse', function($parse) {
    return {
      require: '^tabs',
      restrict: 'EA',
      transclude: true,
      scope:{
        heading:'@'
      },
      link: function(scope, element, attrs, tabsCtrl) {
        var getSelected, setSelected;
        scope.selected = false;
        if (attrs.active) {
          getSelected = $parse(attrs.active);
          setSelected = getSelected.assign;
          scope.$watch(
            function watchSelected() {return getSelected(scope.$parent);},
            function updateSelected(value) {scope.selected = value;}
          );
          scope.selected = getSelected ? getSelected(scope.$parent) : false;
        }
        scope.$watch('selected', function(selected) {
          if(selected) {
            tabsCtrl.select(scope);
          }
          if(setSelected) {
            setSelected(scope.$parent, selected);
          }
        });
  
        tabsCtrl.addPane(scope);
        scope.$on('$destroy', function() {
          tabsCtrl.removePane(scope);
        });
      },
      templateUrl: 'views/tabs/pane.html',
      replace: true
    };
  }])

//
// Transitions from bootstrap UI
//

/**
* $transition service provides a consistent interface to trigger CSS 3 transitions and to be informed when they complete.
* @param {DOMElement} element The DOMElement that will be animated.
* @param {string|object|function} trigger The thing that will cause the transition to start:
* - As a string, it represents the css class to be added to the element.
* - As an object, it represents a hash of style attributes to be applied to the element.
* - As a function, it represents a function to be called that will cause the transition to occur.
* @return {Promise} A promise that is resolved when the transition finishes.
*/
.factory('$transition', ['$q', '$timeout', '$rootScope', function($q, $timeout, $rootScope) {

  var $transition = function(element, trigger, options) {
    options = options || {};
    var deferred = $q.defer();
    var endEventName = $transition[options.animation ? "animationEndEventName" : "transitionEndEventName"];

    var transitionEndHandler = function(event) {
      $rootScope.$apply(function() {
        element.unbind(endEventName, transitionEndHandler);
        deferred.resolve(element);
      });
    };

    if (endEventName) {
      element.bind(endEventName, transitionEndHandler);
    }

    // Wrap in a timeout to allow the browser time to update the DOM before the transition is to occur
    $timeout(function() {
      if ( angular.isString(trigger) ) {
        element.addClass(trigger);
      } else if ( angular.isFunction(trigger) ) {
        trigger(element);
      } else if ( angular.isObject(trigger) ) {
        element.css(trigger);
      }
      //If browser does not support transitions, instantly resolve
      if ( !endEventName ) {
        deferred.resolve(element);
      }
    });

    // Add our custom cancel function to the promise that is returned
    // We can call this if we are about to run a new transition, which we know will prevent this transition from ending,
    // i.e. it will therefore never raise a transitionEnd event for that transition
    deferred.promise.cancel = function() {
      if ( endEventName ) {
        element.unbind(endEventName, transitionEndHandler);
      }
      deferred.reject('Transition cancelled');
    };

    return deferred.promise;
  };

  // Work out the name of the transitionEnd event
  var transElement = document.createElement('trans');
  var transitionEndEventNames = {
    'WebkitTransition': 'webkitTransitionEnd',
    'MozTransition': 'transitionend',
    'OTransition': 'oTransitionEnd',
    'msTransition': 'MSTransitionEnd',
    'transition': 'transitionend'
  };
  var animationEndEventNames = {
    'WebkitTransition': 'webkitAnimationEnd',
    'MozTransition': 'animationend',
    'OTransition': 'oAnimationEnd',
    'msTransition': 'MSAnimationEnd',
    'transition': 'animationend'
  };
  function findEndEventName(endEventNames) {
    for (var name in endEventNames){
      if (transElement.style[name] !== undefined) {
        return endEventNames[name];
      }
    }
  }
  $transition.transitionEndEventName = findEndEventName(transitionEndEventNames);
  $transition.animationEndEventName = findEndEventName(animationEndEventNames);
  return $transition;
}])

//
// DIALOG Controller from Boostrap UI
//
.controller('MessageBoxController', ['$scope', 'dialog', 'model', function($scope, dialog, model){
  $scope.title = model.title;
  $scope.message = model.message;
  $scope.buttons = model.buttons;
  $scope.close = function(res){
    dialog.close(res);
  };
}])

.provider("$dialog", function(){

  // The default options for all dialogs.
  var defaults = {
    backdrop: true,
    dialogClass: 'modal',
    backdropClass: 'modal-backdrop',
    transitionClass: 'fade',
    triggerClass: 'in',
    dialogOpenClass: 'modal-open',
    resolve:{},
    backdropFade: false,
    dialogFade:false,
    keyboard: true, // close with esc key
    backdropClick: true // only in conjunction with backdrop=true
    /* other options: template, templateUrl, controller */
};

var globalOptions = {};

  var activeBackdrops = {value : 0};

  // The `options({})` allows global configuration of all dialogs in the application.
  //
  // var app = angular.module('App', ['ui.bootstrap.dialog'], function($dialogProvider){
  // // don't close dialog when backdrop is clicked by default
  // $dialogProvider.options({backdropClick: false});
  // });
this.options = function(value){
globalOptions = value;
};

  // Returns the actual `$dialog` service that is injected in controllers
this.$get = ["$http", "$document", "$compile", "$rootScope", "$controller", "$templateCache", "$q", "$transition", "$injector",
  function ($http, $document, $compile, $rootScope, $controller, $templateCache, $q, $transition, $injector) {

var body = $document.find('body');

function createElement(clazz) {
var el = angular.element("<div>");
el.addClass(clazz);
return el;
}

    // The `Dialog` class represents a modal dialog. The dialog class can be invoked by providing an options object
    // containing at lest template or templateUrl and controller:
    //
    // var d = new Dialog({templateUrl: 'foo.html', controller: 'BarController'});
    //
    // Dialogs can also be created using templateUrl and controller as distinct arguments:
    //
    // var d = new Dialog('path/to/dialog.html', MyDialogController);
function Dialog(opts) {

      var self = this, options = this.options = angular.extend({}, defaults, globalOptions, opts);

      this.backdropEl = createElement(options.backdropClass);
      if(options.backdropFade){
        this.backdropEl.addClass(options.transitionClass);
        this.backdropEl.removeClass(options.triggerClass);
      }

      this.modalEl = createElement(options.dialogClass);
      if(options.dialogFade){
        this.modalEl.addClass(options.transitionClass);
        this.modalEl.removeClass(options.triggerClass);
      }

      this.handledEscapeKey = function(e) {
        if (e.which === 27) {
          self.close();
          e.preventDefault();
          self.$scope.$apply();
        }
      };

      this.handleBackDropClick = function(e) {
        self.close();
        e.preventDefault();
        self.$scope.$apply();
      };
    }

    // The `isOpen()` method returns wether the dialog is currently visible.
    Dialog.prototype.isOpen = function(){
      return this._open;
    };

    // The `open(templateUrl, controller)` method opens the dialog.
    // Use the `templateUrl` and `controller` arguments if specifying them at dialog creation time is not desired.
    Dialog.prototype.open = function(templateUrl, controller){
      var self = this, options = this.options;

      if(templateUrl){
        options.templateUrl = templateUrl;
      }
      if(controller){
        options.controller = controller;
      }

      if(!(options.template || options.templateUrl)) {
        throw new Error('Dialog.open expected template or templateUrl, neither found. Use options or open method to specify them.');
      }

      this._loadResolves().then(function(locals) {
        var $scope = locals.$scope = self.$scope = locals.$scope ? locals.$scope : $rootScope.$new();

        self.modalEl.html(locals.$template);

        if (self.options.controller) {
          var ctrl = $controller(self.options.controller, locals);
          self.modalEl.contents().data('ngControllerController', ctrl);
        }

        $compile(self.modalEl)($scope);
        self._addElementsToDom();
        body.addClass(self.options.dialogOpenClass);

        // trigger tranisitions
        setTimeout(function(){
          if(self.options.dialogFade){ self.modalEl.addClass(self.options.triggerClass); }
          if(self.options.backdropFade){ self.backdropEl.addClass(self.options.triggerClass); }
        });

        self._bindEvents();
      });

      this.deferred = $q.defer();
      return this.deferred.promise;
    };

    // closes the dialog and resolves the promise returned by the `open` method with the specified result.
    Dialog.prototype.close = function(result){
      var self = this;
      var fadingElements = this._getFadingElements();

      body.removeClass(self.options.dialogOpenClass);
      if(fadingElements.length > 0){
        for (var i = fadingElements.length - 1; i >= 0; i--) {
          $transition(fadingElements[i], removeTriggerClass).then(onCloseComplete);
        }
        return;
      }

      this._onCloseComplete(result);

      function removeTriggerClass(el){
        el.removeClass(self.options.triggerClass);
      }

      function onCloseComplete(){
        if(self._open){
          self._onCloseComplete(result);
        }
      }
    };

    Dialog.prototype._getFadingElements = function(){
      var elements = [];
      if(this.options.dialogFade){
        elements.push(this.modalEl);
      }
      if(this.options.backdropFade){
        elements.push(this.backdropEl);
      }

      return elements;
    };

    Dialog.prototype._bindEvents = function() {
      if(this.options.keyboard){ body.bind('keydown', this.handledEscapeKey); }
      if(this.options.backdrop && this.options.backdropClick){ this.backdropEl.bind('click', this.handleBackDropClick); }
    };

    Dialog.prototype._unbindEvents = function() {
      if(this.options.keyboard){ body.unbind('keydown', this.handledEscapeKey); }
      if(this.options.backdrop && this.options.backdropClick){ this.backdropEl.unbind('click', this.handleBackDropClick); }
    };

    Dialog.prototype._onCloseComplete = function(result) {
      this._removeElementsFromDom();
      this._unbindEvents();

      this.deferred.resolve(result);
    };

    Dialog.prototype._addElementsToDom = function(){
      body.append(this.modalEl);

      if(this.options.backdrop) {
        if (activeBackdrops.value === 0) {
          body.append(this.backdropEl);
        }
        activeBackdrops.value++;
      }

      this._open = true;
    };

    Dialog.prototype._removeElementsFromDom = function(){
      this.modalEl.remove();

      if(this.options.backdrop) {
        activeBackdrops.value--;
        if (activeBackdrops.value === 0) {
          this.backdropEl.remove();
        }
      }
      this._open = false;
    };

    // Loads all `options.resolve` members to be used as locals for the controller associated with the dialog.
    Dialog.prototype._loadResolves = function(){
      var values = [], keys = [], templatePromise, self = this;

      if (this.options.template) {
        templatePromise = $q.when(this.options.template);
      } else if (this.options.templateUrl) {
        templatePromise = $http.get(this.options.templateUrl, {cache:$templateCache})
        .then(function(response) { return response.data; });
      }

      angular.forEach(this.options.resolve || [], function(value, key) {
        keys.push(key);
        values.push(angular.isString(value) ? $injector.get(value) : $injector.invoke(value));
      });

      keys.push('$template');
      values.push(templatePromise);

      return $q.all(values).then(function(values) {
        var locals = {};
        angular.forEach(values, function(value, index) {
          locals[keys[index]] = value;
        });
        locals.dialog = self;
        return locals;
      });
    };

    // The actual `$dialog` service that is injected in controllers.
    return {
      // Creates a new `Dialog` with the specified options.
      dialog: function(opts){
        return new Dialog(opts);
      },
      // creates a new `Dialog` tied to the default message box template and controller.
      //
      // Arguments `title` and `message` are rendered in the modal header and body sections respectively.
      // The `buttons` array holds an object with the following members for each button to include in the
      // modal footer section:
      //
      // * `result`: the result to pass to the `close` method of the dialog when the button is clicked
      // * `label`: the label of the button
      // * `cssClass`: additional css class(es) to apply to the button for styling
      messageBox: function(title, message, buttons){
        return new Dialog({templateUrl: 'template/dialog/message.html', controller: 'MessageBoxController', resolve:
          {model: function() {
            return {
              title: title,
              message: message,
              buttons: buttons
            };
          }
        }});
      }
    };
  }];
})


  ////////////////////////////
  // Page Load Configuration
  ////////////////////////////

.run(function($cookieStore, sessionService) {
  // Check for session tokens and name in cookies, yum yum
  sessionService.setLongSession($cookieStore.get('ps_longsession'));
  sessionService.setShortSession($cookieStore.get('ps_shortsession'));
  sessionService.setUserName($cookieStore.get('ps_username'));    
});
  ////////////////////////////
  // HELPER FUNCS
  ////////////////////////////

// Array Remove - By John Resig (MIT Licensed)
Array.prototype.remove = function(from, to) {
  var rest = this.slice((to || from) + 1 || this.length);
  this.length = from < 0 ? this.length + from : from;
  return this.push.apply(this, rest);
};

function isEmpty(obj) {
    for(var prop in obj) {
        if(obj.hasOwnProperty(prop))
            return false;
    }
    return true;
}




