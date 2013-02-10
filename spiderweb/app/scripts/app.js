'use strict';

var spiderwebApp = angular.module('spiderwebApp', [])
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
      .otherwise({
        redirectTo: '/'
      });

    //$locationProvider.html5Mode(true);

  }])

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

  // Tabs directive from angular UI bootstrap
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
  }]);

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
