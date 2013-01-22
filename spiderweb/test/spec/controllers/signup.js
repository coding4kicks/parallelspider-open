'use strict';

describe('Controller: SignupCtrl', function() {

  // load the controller's module
  beforeEach(module('spiderwebApp'));

  var SignupCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function($controller) {
    scope = {};
    SignupCtrl = $controller('SignupCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function() {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
