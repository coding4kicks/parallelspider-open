'use strict';

describe('Controller: OurwordsCtrl', function() {

  // load the controller's module
  beforeEach(module('spiderwebApp'));

  var OurwordsCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function($controller) {
    scope = {};
    OurwordsCtrl = $controller('OurwordsCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function() {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
