'use strict';

describe('Controller: CrawlingCtrl', function() {

  // load the controller's module
  beforeEach(module('spiderwebApp'));

  beforeEach(inject(function($httpBackend) {
    $httpBackend.whenGET('quote-file.json').respond({});
  })); 

  var CrawlingCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function($controller) {
    scope = {};
    CrawlingCtrl = $controller('CrawlingCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function() {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
