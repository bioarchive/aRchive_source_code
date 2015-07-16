'use strict';

/* App Module */

var pkgApp = angular.module('pkgApp', [
  'ngRoute',
  'pkgAnimations',
  'pkgControllers',
  'pkgFilters',
  'pkgServices'
]);

pkgApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/pkg/', {
        templateUrl: 'partials/pkg.html',
        controller: 'PkgCtrl'
      }).
      when('/pkg/:pkgId/', {
        templateUrl: 'partials/pkg.html',
        controller: 'PkgCtrl'
      }).
      when('/pkg/:pkgId/:pkgVersion/', {
        templateUrl: 'partials/pkg.html',
        controller: 'PkgCtrl'
      }).
      otherwise({
        redirectTo: '/pkg/Biobase/'
      });
  }]);
