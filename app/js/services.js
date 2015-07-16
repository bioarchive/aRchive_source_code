'use strict';

/* Services */

var pkgServices = angular.module('pkgServices', ['ngResource']);

pkgServices.factory('Pkg', ['$resource',
  function($resource){
    return $resource('pkg/api/:pkgId.json', {}, {
      query: {method:'GET', params:{pkgId:'api'}, isArray:true}
    });
  }]);

pkgServices.factory('PkgVersion', ['$resource',
  function($resource){
    return $resource('pkg/api/:pkgId/:pkgVers.json', {}, {
      query: {method:'GET', params:{pkgId:'api', pkgVers: '1.0'}, isArray:true}
    });
  }]);
