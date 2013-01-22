'use strict';

describe('Controller: LaunchpadCtrl', function() {

  // load the controller's module
  beforeEach(module('spiderwebApp'));

  var LaunchpadCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function($controller) {
    scope = {};
    LaunchpadCtrl = $controller('LaunchpadCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function() {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
