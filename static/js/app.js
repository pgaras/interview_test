/*** Authored by Peter Garas for Ocom Software ***/

projectApp = angular.module('projectApp', ['ngResource', 'ngRoute', 'project.controllers']);

/*** Configurations ***/
projectApp.config(['$httpProvider', function($httpProvider){
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.headers.common['Cache-Control'] = 'no-cache';
        $httpProvider.defaults.cache = false;
    }]).
    config(function($routeProvider) {
            $routeProvider.
                when('/libraries', {
                    templateUrl: '/static/templates/library_list.html',
                    controller: 'libraryListController'
                }).
                when('/projects', {
                    templateUrl: '/static/templates/project_list.html',
                    controller: 'projectListController'
                }).
                otherwise({ // Any other URL, take me back to /
                    templateUrl: '/static/templates/welcome.html'
                });
    });

/*** Services ***/
projectApp.service('flagState', function () {
        return {
            user: undefined,
            prj: false,
            supe: false,
            library_edit_mode: false,
            current_library: -1,
            project_edit_mode: false,
            current_project: -1,
            library_add_mode: false,
            last_message: []
        };
    });

/*** Factories ***/
projectApp.factory('auth', function($resource) {
        function add_auth_header(data, headersGetter) {
            var headers = headersGetter();
            headers['Authorization'] = ('Basic ' + btoa(data.username + ':' + data.password));
        }
        return {
            login: $resource('/api/auth/login\\/', {}, {
                post: {
                    method: 'POST',
                    headers: add_auth_header
                }
            }),
            logout: $resource('/api/auth/logout\\/', {}, {
                post: {
                    method: 'POST'
                }
            })
        };
    }).
    factory('alertService', function($rootScope, $timeout) {
        var alertService = {};

        $rootScope.alerts = [];

        alertService.add = function(type, msg) {
            $rootScope.alerts.push({'type': type, 'msg': msg});
        };

        alertService.close_alert = function(index) {
            $rootScope.alerts.splice(index, 1);
        };

        alertService.clear_alerts = function() {
            $rootScope.alerts = [];
        };

        alertService.add_clear = function(type, msg, delay) {
            $rootScope.alerts = [];
            $timeout(function () {
                $rootScope.alerts.push({'type': type, 'msg': msg});
            }, delay);
        };

        $rootScope.close_alert = alertService.close_alert;
        return alertService;
    }).
    factory('focus', function ($rootScope, $timeout) {
        return function(name) {
            $timeout(function () {
                $rootScope.$broadcast('focusOn', name);
            });
        }
    }).
    factory('library', function($resource) {
        return {
            list: $resource('/api/libraries\\/', {}, {
                get: {
                    method: 'GET',
                    isArray: true
                }
            }),
            active_list: $resource('/api/libraries\\/', {}, {
                get: {
                    method: 'GET',
                    params: {
                        active: 'true'
                    },
                    isArray: true
                }
            }),
            inactive_list: $resource('/api/libraries\\/', {}, {
                get: {
                    method: 'GET',
                    params: {
                        active: 'false'
                    },
                    isArray: true
                }
            }),
            update: $resource('/api/libraries/edit\\/', {}, {
                put: {
                    method: 'PUT'
                }
            })
        };
    }).
    factory('project', function($resource) {
        return {
            list: $resource('/api/projects\\/', {}, {
                get: {
                    method: 'GET',
                    isArray: true
                }
            }),
            update: $resource('/api/projects\\/', {}, {
                put: {
                    method: 'PUT'
                }
            }),
            remove:
            $resource('/api/projects\\/', {}, {
                confirm: {
                    method: 'DELETE'
                }
            })
        };
    });

/*** Controllers ***/
angular.module('project.controllers', [
    'project.controller'
  ], null);

angular.module('project.controller', []).
    controller('authController', function($scope, $rootScope, $window, auth, alertService, flagState) {
        $('#id_auth_form').find('input').checkAndTriggerAutoFillEvent();

        $scope.flagState = flagState;

        $scope.getCredentials = function() {
            return {username: $scope.username, password: $scope.password};
        };

        $scope.login = function() {
            auth.login.post($scope.getCredentials()).
                $promise.
                    then(function(data) {
                        var body_elem = angular.element(document.querySelector('body'));

                        body_elem.addClass("hidden");

                        flagState.user = data.username;
                        flagState.supe = data.is_staff;
                        flagState.prj = false;
                        alertService.add_clear('success', "You are now logged in.", 0);
                        $window.location.href = '/';
                    }).
                    catch(function(data) {
                        $rootScope.message_title = "Login Error";
                        $rootScope.message_body = "Unrecognized credentials. Please try again.";
                        $scope.showModal(true);
                    });
        };

        $scope.logout = function(){
            auth.logout.post(function() {
                var body_elem = angular.element(document.querySelector('body'));

                body_elem.addClass("hidden");
                flagState.user = undefined;
                flagState.supe = false;
                flagState.prj = false;
                flagState.library_edit_mode = false;
                flagState.project_edit_mode = false;
                alertService.add_clear('success', "You are now logged out.", 1000);
                $window.location.href = '/';
            });
        };
    }).
    controller('libraryListController', function($scope, $http, $route, $rootScope, $window, alertService, library, flagState, focus) {
        $scope.flagState = flagState;
        $scope.library_edit_mode = false;
        $scope.library_master = {};

        $scope.list = function() {
            library.list.get(function(data) {
                $scope.libraries = data;
                library.inactive_list.get(function(data) {
                    $scope.inactive_libraries = data;
                    angular.forEach($scope.libraries, function(data, key) {
                        var found = false;

                        angular.forEach($scope.inactive_libraries, function(subdata, subkey) {
                            if (subdata.id === data.id) {
                                found = true;
                                $scope.libraries[key]['status'] = 'inactive';
                            }
                        });
                        if (!found) {
                            $scope.libraries[key]['status'] = 'active';
                        }
                    });
                });
            });
        };

        $scope.scroll_to_top = function() {
            $window.scrollTo(0, 0);
        };

        $scope.append = function() {
            $scope.library_master = false;
            flagState.current_library = 0;
            flagState.library_edit_mode = true;
            focus('add_library_focus_first');
        };

        $scope.edit = function(current, index) {
            $scope.library_master = {};
            flagState.current_library = current.id;
            $scope.library_master = angular.copy($scope.libraries[index]);
            flagState.library_edit_mode = true;
            focus('library_focus_first_' + current.id);
        };

        $scope.cancel = function(form) {
            if (!$scope.library_master) {
                form.add_description.$setViewValue('');
                form.add_description.$render();
                form.add_active_start_date.$setViewValue('');
                form.add_active_start_date.$render();
                form.add_active_end_date.$setViewValue('');
                form.add_active_end_date.$render();
            } else {
                angular.forEach(form, function(control, key1) {
                    if (typeof control === 'object' && control.hasOwnProperty('$modelValue') && control.$dirty) {
                        angular.forEach($scope.library_master, function(value, name) {
                            if (control.$name.indexOf(name) > -1) {
                                control.$setViewValue($scope.library_master[name]);
                                control.$render();
                            }
                        });
                    }
                });
            }
            form.$setPristine();
            form.$setUntouched();
            flagState.library_edit_mode = false;
            alertService.clear_alerts();
            //alertService.add_clear('warning', "Changes to the Library record were cancelled.", 0);
        };

        $scope.append_done = function(form) {
            var append_data = {
                'description': form.add_description.$viewValue,
                'active_start_date': form.add_active_start_date.$viewValue,
                'active_end_date': form.add_active_end_date.$viewValue
            };
            $http.post("api/libraries/", append_data).
            then(function(data, status, headers, config) {
                //success
                flagState.library_edit_mode = false;
                alertService.add_clear('success', "You have added a new library record.", 0);
                $route.reload();
            }, function(fail_data, status, headers, config) {
                $rootScope.message_title = "Save Library Error";
                $rootScope.message_body = "Error: unable to save information.";
                $scope.showModal(true);
            });
        };

        $scope.edit_done = function(form) {
            var edit_data = {};
            var found;

            angular.forEach(form, function(control, key1) {
                if (typeof control === 'object' && control.hasOwnProperty('$modelValue')) {
                    found = false;
                    angular.forEach($scope.library_master, function(value, name) {
                        if (control.$name.indexOf(name) === 0) {
                            if (typeof control.$modelValue === "undefined") {
                                edit_data[name] = $scope.library_master[name];
                            } else {
                                // we need to use view value as it is formatted to yyyy-mm-dd
                                edit_data[name] = control.$viewValue;
                            }
                            found = true;
                        }
                    });
                    if (!found) {
                        edit_data[control.$name] = control.$viewValue;
                    }
                }
            });
            edit_data['id'] = flagState.current_library;
            $http.put("api/libraries/edit/", edit_data).
            then(function(data, status, headers, config) {
                /*
                angular.forEach(edit_data, function(value, key) {
                    $scope.libraries[index][key] = value;
                });
                */
                alertService.add_clear('success', "Changes were saved to the library record.", 0);
                $route.reload();
                flagState.library_edit_mode = false;
            }, function(data, status, headers, config) {
                $rootScope.message_title = "Save Library Error";
                $rootScope.message_body = "Error: unable to save information.";
                $scope.showModal(true);
            });
        };
    }).
    controller('projectListController', function($scope, $http, $filter, $route, $rootScope, $compile, $window, alertService, library, project, flagState, focus) {
        $scope.flagState = flagState;
        $scope.project_edit_mode = false;
        $scope.project_master = {};
        $scope.new_libraries = [];
        $scope.new_no_added_libraries = true;

        $scope.library_list = function() {
            library.active_list.get(function(data) {
                $scope.libraries = data;
            });
        };

        $scope.project_list = function() {
            var all_libraries;

            project.list.get(function (data) {
                $scope.projects = data;
                library.list.get(function (all_data) {
                    all_libraries = all_data;
                    angular.forEach($scope.projects, function (item, key) {
                        var selected, found_subkey, found = false;

                        $scope.projects[key]['no_added_libraries'] = item.libraries.length === 0;
                        angular.forEach(item.libraries, function (lib_project_item, lib_project_item_key) {
                            angular.forEach(all_libraries, function (lib_item, lib_item_key) {
                                if (lib_project_item.id === lib_item.id) {
                                    found = true;
                                    selected = lib_item;
                                    found_subkey = lib_project_item_key;
                                }
                            });
                            if (found) {
                                $scope.projects[key].libraries[found_subkey]['remove'] = false;
                                $scope.projects[key].libraries[found_subkey]['updated'] = false;
                                $scope.projects[key].libraries[found_subkey]['new'] = false;
                            }
                        });
                    });
                });
            });
        };

        $scope.today = new Date();

        $scope.open_link = function(url) {
            $window.open(url, '_blank');
        };

        $scope.scroll_to_top = function() {
            $window.scrollTo(0, 0);
        };

        $scope.check_added_libraries = function(project_key, is_new) {
            if (is_new) {
                if ($scope.new_libraries.length === 0) {
                    $scope.new_no_added_libraries = true;
                    return true;
                }
                $scope.new_no_added_libraries = true;
                angular.forEach($scope.new_libraries, function(item, key) {
                     if (!item.remove) {
                         $scope.new_no_added_libraries = false;
                         return false;
                     }
                });
            } else {
                if ($scope.projects[project_key].libraries.length === 0) {
                    $scope.projects[project_key].no_added_libraries = true;
                    return true;
                }
                $scope.projects[project_key].no_added_libraries = true;
                angular.forEach($scope.projects[project_key].libraries, function(item, key) {
                    if (!item.remove) {
                        $scope.projects[project_key].no_added_libraries = false;
                        return false;
                    }
                });
            }
            return true;
        };

        $scope.append = function(form) {
            form.project_active_start_date.$setViewValue($filter('date')(new Date(), "yyyy-MM-dd"));
            form.project_active_start_date.$render();
            $scope.project_master = false;
            flagState.current_project = 0;
            flagState.project_edit_mode = true;
            focus('add_project_focus_first');
        };

        $scope.add_library = function() {
            flagState.library_add_mode = true;
        };

        $scope.add_library_done = function(form, is_new) {
            var library_description = '';
            var dropdown_value, version_value;
            var invalid = false;

            //let's validate
            if (is_new) {
                if (form.add_library_dropdown.$invalid || form.add_library_version.$invalid) {
                    invalid = true;
                }
            } else {
                if (form.library_dropdown.$invalid || form.library_version.$invalid) {
                    invalid = true;
                }
            }

            if (invalid) {
                $rootScope.message_title = "Save Library Error";
                $rootScope.message_body = "Error: please provide values for the library fields.";
                $scope.showModal(true);
                return;
            }

            if (is_new) {
                dropdown_value = parseInt(form.add_library_dropdown.$viewValue);
                version_value = form.add_library_version.$viewValue;
                form.add_library_version.$setViewValue('');
                form.add_library_version.$render();
            } else {
                dropdown_value = parseInt(form.library_dropdown.$viewValue);
                version_value = form.library_version.$viewValue;
                form.library_version.$setViewValue('');
                form.library_version.$render();
            }

            angular.forEach($scope.libraries, function(lib, key) {
                if (lib.id === dropdown_value) {
                    library_description = lib.description;
                }
            });

            var data = {
                id: dropdown_value,
                description: library_description,
                version: version_value,
                remove: false,
                updated: false,
                new: true
            };

            if (is_new) {
                $scope.new_libraries.push(data);
                $scope.check_added_libraries(-1, true);
            } else {
                angular.forEach($scope.projects, function (item, key) {
                    if (item.id === flagState.current_project) {
                        if (typeof $scope.projects[key].libraries === "undefined") {
                            $scope.projects[key].libraries = [];
                        }
                        $scope.projects[key].libraries.push(data);
                        $scope.projects[key].no_added_libraries = false;
                    }
                });
            }
            flagState.library_add_mode = false;
        };

        $scope.remove_library = function(project_id, library_id, library_index, is_new) {
            if (is_new) {
                angular.forEach($scope.new_libraries, function (lib_project_item, lib_project_item_key) {
                    if (lib_project_item_key === library_index && lib_project_item.id === library_id && !$scope.new_libraries[lib_project_item_key]['remove']) {
                        $scope.new_libraries[lib_project_item_key]['remove'] = true;
                        $scope.new_libraries[lib_project_item_key]['updated'] = true;
                    }
                });
                $scope.check_added_libraries(-1, true);
            } else {
                angular.forEach($scope.projects, function (item, key) {
                    if (item.id === project_id) {
                        angular.forEach(item.libraries, function (lib_project_item, lib_project_item_key) {
                            if (lib_project_item_key === library_index && lib_project_item.id === library_id && !$scope.projects[key].libraries[lib_project_item_key]['remove']) {
                                $scope.projects[key].libraries[lib_project_item_key]['remove'] = true;
                                $scope.projects[key].libraries[lib_project_item_key]['updated'] = true;
                            }
                            $scope.check_added_libraries(key, false);
                        });
                    }
                });
            }
        };

        $scope.edit = function(current, index) {
            $scope.project_master = {};
            flagState.current_project = current.id;
            $scope.project_master = angular.copy($scope.projects[index]);
            flagState.project_edit_mode = true;
            focus('project_focus_first_' + current.id);
        };

        $scope.remove = function(project_id) {
            if (confirm("The record will be gone forever. Do you wish to proceed?")) {
                $http.delete("api/projects/", {
                    data: {
                        id: project_id
                    },
                    headers: {
                        'Content-type': 'application/json;charset=utf-8'
                    }
                }).
                then(function(data, status, headers, config) {
                    flagState.project_edit_mode = false;
                    flagState.library_add_mode = false;
                    alertService.add_clear('warning', "You have deleted a Project record.", 0);
                    $route.reload();
                }, function(data, status, headers, config) {
                    $rootScope.message_title = "Save Project Error";
                    $rootScope.message_body = "Error: unable to delete record.";
                    $scope.showModal(true);
                });
            }
        };

        $scope.cancel_add_library = function() {
            flagState.library_add_mode = false;
        };

        $scope.cancel = function(form, is_new) {
            if (is_new) {
                form.project_active_start_date.$setViewValue('');
                form.project_active_start_date.$render();
                form.project_active_end_date.$setViewValue('');
                form.project_active_end_date.$render();
                form.project_description.$setViewValue('');
                form.project_description.$render();
                $scope.new_libraries = [];
            } else {
                angular.forEach(form, function(control, key1) {
                    if (typeof control === 'object' && control.hasOwnProperty('$modelValue') && control.$dirty) {
                        angular.forEach($scope.project_master, function(value, name) {
                            if (control.$name.indexOf(name) === 0) {
                                control.$setViewValue($scope.project_master[name]);
                                control.$render();
                            }
                        });
                    }
                });
                angular.forEach($scope.projects, function (item, key) {
                    if (item.id === flagState.current_project) {
                        angular.forEach(item.libraries, function (lib_project_item, lib_project_item_key) {
                            if ($scope.projects[key].libraries[lib_project_item_key]['new']) {
                                $scope.projects[key].libraries.splice(lib_project_item_key, 1);
                            } else if ($scope.projects[key].libraries[lib_project_item_key]['updated']) {
                                $scope.projects[key].libraries[lib_project_item_key]['remove'] = !$scope.projects[key].libraries[lib_project_item_key]['remove'];
                                $scope.projects[key].libraries[lib_project_item_key]['updated'] = false;
                            }
                        });
                    }
                });
            }
            form.$setPristine();
            form.$setUntouched();
            flagState.project_edit_mode = false;
            flagState.library_add_mode = false;
            alertService.clear_alerts();
            //alertService.add_clear('warning', "Changes to the Project record were cancelled.", 0);
        };

        $scope.append_done = function(form, libraries) {
            var append_data = {
                'name': form.project_name.$viewValue,
                'active_start_date': form.project_active_start_date.$viewValue,
                'active_end_date': form.project_active_end_date.$viewValue,
                'client_name': form.project_client_name.$viewValue,
                'description': form.project_description.$viewValue,
                'git_url': form.project_git_url.$viewValue,
                'testing_url': form.project_testing_url.$viewValue,
                'production_url': form.project_production_url.$viewValue
            };
            append_data['libraries'] = libraries;
            $http.post("api/projects/", append_data).
            then(function(data, status, headers, config) {
                flagState.project_edit_mode = false;
                flagState.library_add_mode = false;
                alertService.add_clear('success', "You have added a new Project record.", 0);
                $route.reload();
            }, function(fail_data, status, headers, config) {
                $rootScope.message_title = "Save Project Error";
                $rootScope.message_body = "Error: unable to save information.";
                $scope.showModal(true);
            });
        };

        $scope.edit_done = function(form, libraries) {
            var edit_data = {};
            var found;

            angular.forEach(form, function(control, control_key) {
                if (typeof control === 'object' && control.hasOwnProperty('$modelValue')) {
                    angular.forEach($scope.project_master, function(value, name) {
                        if (control.$name.indexOf(name) === 0) {
                            if (typeof control.$modelValue === "undefined") {
                                edit_data[name] = $scope.project_master[name];
                            } else {
                                // we need to use view value as it is formatted to yyyy-mm-dd
                                edit_data[name] = control.$viewValue;
                            }
                        }
                    });
                    if (!found) {
                        edit_data[control.$name] = control.$viewValue;
                    }
                }

            });
            edit_data['libraries'] = libraries;
            edit_data['id'] = flagState.current_project;
            $http.put("api/projects/edit/", edit_data).
            then(function(data, status, headers, config) {
                /*
                angular.forEach(edit_data, function(value, subkey) {
                    $scope.projects[index][subkey] = value;
                });
                */
                flagState.project_edit_mode = false;
                flagState.library_add_mode = false;
                alertService.add_clear('success', "Changes to the Project record were saved.", 0);
                $route.reload();
            }, function(data, status, headers, config) {
                $rootScope.message_title = "Save Project Error";
                $rootScope.message_body = "Error: unable to save information.";
                $scope.showModal(true);
            });
        };
    });

/*** Directives ***/
projectApp.directive('focusOn', function() {
   return function(scope, element, attr) {
      scope.$on('focusOn', function(e, name) {
        if(name === attr.focusOn) {
            element[0].focus();
        }
      });
   };
}).
directive("modalShow", function($parse) {
    return {
        restrict: "A",
        link: function (scope, element, attrs) {
            //Hide or show the modal
            scope.showModal = function (visible, elem) {
                if (!elem)
                    elem = element;
                if (visible)
                    $(elem).modal("show");
                else
                    $(elem).modal("hide");
            };
            //Watch for changes to the modal-visible attribute
            scope.$watch(attrs.modalShow, function (newValue, oldValue) {
                scope.showModal(newValue, attrs.$$element);
            });
            //Update the visible value when the dialog is closed through UI actions (Ok, cancel, etc.)
            $(element).bind("hide.bs.modal", function () {
                $parse(attrs.modalShow).assign(scope, false);
                if (!scope.$$phase && !scope.$root.$$phase)
                    scope.$apply();
            });
        }
    };
});

/*** Miscellaneous Global Functions ***/
function checkCredentials(username, password) {
    function setHeader(xhr) {
        // as per HTTP authentication spec [2], credentials must be
        // encoded in base64. Lets use window.btoa [3]
        xhr.setRequestHeader("Authorization", "Basic " + btoa(username + ':' + password));
    }

    $.ajax({type: "POST", url: "/api/auth/", beforeSend: setHeader}).fail(function(response) {
        console.log('Bad credentials.');
    }).done(function (done_response) {
        console.log('welcome ' + done_response.email, done_response);
    });
}
