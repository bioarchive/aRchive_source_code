'use strict';

/* Controllers */

var pkgControllers = angular.module('pkgControllers', []);


pkgControllers.controller('PkgCtrl', ['$scope', '$routeParams', 'Pkg', 'PkgVersion',
  function($scope, $routeParams, Pkg, PkgVersion) {
    $scope.pkg_list = Pkg.query();
    $scope.pkg = Pkg.get({pkgId: $routeParams.pkgId});

    if($routeParams.pkgVersion !== undefined){
      $scope.deps = PkgVersion.query({pkgId: $routeParams.pkgId, pkgVers: $routeParams.pkgVersion});
      $scope.version = $routeParams.pkgVersion;
    }
  }]);
