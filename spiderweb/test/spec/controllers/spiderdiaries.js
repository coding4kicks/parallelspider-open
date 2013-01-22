'use strict';

describe('Controller: SpiderdiariesCtrl', function() {

  // load the controller's module
  beforeEach(module('spiderwebApp'));

  var SpiderdiariesCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function($controller) {
    scope = {};
    SpiderdiariesCtrl = $controller('SpiderdiariesCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function() {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
