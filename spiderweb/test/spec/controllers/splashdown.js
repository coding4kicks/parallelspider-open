'use strict';

describe('Controller: SplashdownCtrl', function() {

  // load the controller's module
  beforeEach(module('spiderwebApp'));

  beforeEach(inject(function($httpBackend) {
    $httpBackend.whenGET('results5.json').respond({});
  }));  

  var SplashdownCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function($controller) {
    scope = {};
    SplashdownCtrl = $controller('SplashdownCtrl', {
      $scope: scope
    });
  }));

  //beforeEach(inject($httpBacked) {
  //  $httpBackend.whenGET('results.json').respond('fakeData');
  //});

  it('should attach a list of awesomeThings to the scope', function() {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
