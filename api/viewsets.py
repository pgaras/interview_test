# Authored by Peter Garas for Ocom Software

from datetime import datetime
from django.contrib import auth
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from . import serializers, models, utils


class AuthViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    A simple ViewSet for authentication.

    Warning: using the POST button here will result in exceptions due to the intentional absence of create and
    list methods (see more info below)

    <b>login</b>:
    Allow a user to log in

        Usage:
        [POST]: /api/auth/login/
        Note: An additional header parameter is required (refer to /static/app.js)

    <b>logout</b>:
    Log out currently logged in user (per browser session instance)

        POST: /api/auth/logout/
        Note: The current RequestContext session is used to identify and log out the user

    """

    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    authentication_classes = (utils.QuietBasicAuthentication,)

    @list_route(methods=['post'])
    def login(self, request, *args, **kwargs):
        user = auth.authenticate(username=request.data.get('username', ''), password=request.data.get('password', ''))

        if user is None:
            raise PermissionDenied
        else:
            request.user = user
            auth.login(request, request.user)
            return Response(self.serializer_class(request.user).data)

    @list_route(methods=['post'])
    def logout(self, request, *args, **kwargs):
        auth.logout(request)
        return Response({})


class LibraryViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    The Resource Library Viewset

    <b>list:</b>
    Obtain all library items or filter based on provided request parameters

        Usage: Get all library items
        [GET]: /api/libraries/

        Usage: Get active library items. A library item is active if the Active start Date is before the current date
        and the active end date is after the current date or null
        [GET]: /api/libraries/?active=true

        Usage: Get inactive library items (see above)
        [GET]: /api/libraries/?active=false

    <b>create:</b>
    Append a new library item to the Library list

        Usage:
        [POST]: /api/libraries/
            where POST data includes the following:
                'description':          the name or title of the library
                'active_start_date':    Active Start Date
                'active_end_date':      (optional) Active End Date (may be null or blank)

    <b>update:</b>
    Edit a library item

        Usage:
        [PUT]: /api/libraries/edit/
            where PUT data includes the following:
                'id':                   (required) the library record id
                'description':          the name or title of the library
                'active_start_date':    Active Start Date
                'active_end_date':      (optional) Active End Date

    """

    queryset = models.Library.objects.all()
    serializer_class = serializers.LibrarySerializer
    invalid_put_request = {"detail": "Invalid request: Please check your \"PUT\" data"}

    def list(self, request, *args, **kwargs):
        active_param = request.query_params.get('active')

        if isinstance(active_param, basestring):
            active, get_all = utils.get_param_flags(active_param)
        else:
            active = False
            get_all = True

        if get_all:
            libraries = models.Library.objects.all()
        else:
            now = datetime.now()

            if active:
                libraries = models.Library.objects.all().filter(active_start_date__lte=now)
                libraries = libraries.filter(Q(active_end_date__gte=now) | Q(active_end_date__isnull=True))
            else:
                all_libraries = models.Library.objects.all()
                active_libraries = all_libraries.filter(active_start_date__lte=now)
                active_libraries = active_libraries.filter(Q(active_end_date__gte=now) |
                                                           Q(active_end_date__isnull=True))
                libraries = set(all_libraries).difference(active_libraries)

        serializer = self.serializer_class(libraries, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        data = request.data
        result, response_data = utils.validate_date_entries(data)

        if not result:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['put'])
    def edit(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        try:
            library = models.Library.objects.get(pk=request.data.get('id'))
        except models.Library.DoesNotExist:
            return Response(self.invalid_put_request, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        result, response_data = utils.validate_date_entries(data)

        if not result:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if library:
            serializer = serializers.LibrarySerializer(library, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.invalid_put_request, status=status.HTTP_400_BAD_REQUEST)


class ProjectViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    The Project Viewset

    <b>list:</b>
    Obtain all project items

        Usage:
        [GET]: /api/projects/

    <b>create:</b>
    Append a new project item to the Project list

        Usage:
        [POST]: /api/projects/
            where POST data includes the following:
                'name':                 The project name
                'active_start_date':    The date this Project is active in the system. Default is the Current Date
                'active_end_date':      (optional) The Date this Project is not active in the system. If blank it's is
                                        active forever.
                'client_name':          The name of the client for the project
                'description':          (optional) This is a small description of the project (i.e. what it does and what it's for)
                'git_url':              The URL of the Git repository
                'testing_url':          (optional) The URL of the testing instance
                'production_url':       (optional) The URL of a production instance
                'libraries':            (optional) An array of library entries

        Note on libraries:
            In order for 'libraries' data to be recognized, the contents should have the following values:
                'id':                   (required) the library record id
                'version':              The version number used for this project i.e. "1.4.6" or "1.5.alpha", etc.
                'new':                  If this is set to true, the library item will be included in the project
                'remove':               If this is set to true, the library item will be removed from the project. If
                                        both this and the new parameter value is set to true, the new parameter is
                                        ignored

    <b>update:</b>
    Edit a project item

        Usage:
        [PUT]: /api/projects/edit/
            where PUT data includes the following:
                'id':                   (required) the project record id
                'name':                 The project name
                'active_start_date':    The date this Project is active in the system. Default is the Current Date
                'active_end_date':      (optional) The Date this Project is not active in the system. If blank it's is
                                        active forever.
                'client_name':          The name of the client for the project
                'description':          (optional) This is a small description of the project (i.e. what it does and
                                        what it's for)
                'git_url':              The URL of the Git repository
                'testing_url':          (optional) The URL of the testing instance
                'production_url':       (optional) The URL of a production instance
                'libraries':            (optional) An array of library entries. For more info on how to use this, see
                                        the 'libraries' parameter on Project.create

    <b>remove:</b>
    Remove a project item

        Usage:
        [DELETE]: /api/projects/
            where DELETE data includes the following:
                'id':                   (required) the project record id
    """

    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    invalid_put_request = {"detail": "Invalid request: Please check your \"PUT\" data"}

    def list(self, request, *args, **kwargs):
        projects = models.Project.objects.all()
        serializer = serializers.ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def _save_library_entries(self, project_id, libraries):
        for library in libraries:
            remove_param = library.get('remove')
            if isinstance(remove_param, basestring):
                remove, _ = utils.get_param_flags(remove_param)
            elif isinstance(remove_param, bool):
                remove = remove_param
            else:
                remove = False

            if remove:
                try:
                    models.ProjectLibrary.objects.filter(pk=library.get('id')).delete()
                except models.ProjectLibrary.DoesNotExist:
                    return False, {"detail": "Invalid request: Please check your \"POST/PUT\" data"}
            else:
                lib = {
                    'library_id': library['id'],
                    'version': library['version'],
                    'project_id': project_id
                }

                new_param = library.get('new')
                if isinstance(new_param, basestring):
                    is_new, _ = utils.get_param_flags(new_param)
                elif isinstance(new_param, bool):
                    is_new = new_param
                else:
                    is_new = False

                if new_param:
                    serializer = serializers.LibraryVersionySerializer(data=lib)

                    if serializer.is_valid():
                        models.ProjectLibrary.objects.create(**lib)
                    else:
                        return False, serializer.errors
                else:
                    try:
                        entry = models.ProjectLibrary.objects.get(pk=library.get('id'))
                    except models.ProjectLibrary.DoesNotExist:
                        return False, {
                            "detail":
                                "Invalid request: Changes to library data not saved. Please check your "
                                "\"POST/PUT\" data"}
                    else:
                        try:
                            entry.save(update_fields=lib)
                        except IntegrityError as err:
                            return False, {"detail": str(err)}

        return True, {}

    def create(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        data = request.data.copy()
        libs = request.data.get('libraries', [])

        if 'libraries' in data:
            del data['libraries']

        data = request.data
        result, response_data = utils.validate_date_entries(data)

        if not result:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            try:
                project = serializer.save()
            except IntegrityError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

            # we need to retrieve the newly-created project here
            if libs:
                result, response_data = self._save_library_entries(project.id, libs)

                if not result:
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['put'])
    def edit(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        try:
            project = models.Project.objects.get(pk=request.data.get('id'))
        except models.Project.DoesNotExist:
            return Response(self.invalid_put_request, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        libs = request.data.get('libraries', [])

        if 'libraries' in data:
            del data['libraries']

        if project:
            if data:
                serializer = serializers.ProjectSerializer(project, data=data)

                if serializer.is_valid():
                    serializer.save()

            self._save_library_entries(data['id'], libs)
            return Response(request.data)

        return Response({"detail": "Invalid request: Please check your \"PUT\" data"},
                        status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['delete'])
    def delete(self, request, *args, **kwargs):
        try:
            remove_project = models.Project.objects.get(pk=request.data.get('id'))
        except models.Project.DoesNotExist:
            return Response({"detail": "Invalid request: Please check your \"DELETE\" data"},
                            status=status.HTTP_400_BAD_REQUEST)

        remove_project.delete()
        return Response(request.data)


class ProjectLibraryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project and Library relation table 
    
    Note: you should see the version field here
    """

    queryset = models.ProjectLibrary.objects.all()
    serializer_class = serializers.ProjectLibrarySerializer
