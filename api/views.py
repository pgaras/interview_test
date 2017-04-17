# Authored by Peter Garas for Ocom Software

from datetime import datetime
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from . import models, serializers, utils


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        context['app_name'] = getattr(settings, 'APPLICATION_NAME', '')
        context['project_permissions'] = 'true' if utils.get_project_permissions(self.request.user) else 'false'
        context['staff_permissions'] = 'true' if self.request.user.is_staff else 'false'
        return context


# The following views are deactivated in favor of ViewSets. please refer to api/viewsets.py
class LibraryView(APIView):
    def get(self, request, *args, **kwargs):
        active = request.query_params.get('active', False)
        inactive = request.query_params.get('inactive', False)
        now = datetime.now()

        if active:
            libraries = models.Library.objects.filter(active_start_date__lte=now)
            libraries = libraries.filter(Q(active_end_date__gte=now) | Q(active_end_date__isnull=True))
        elif inactive:
            all_libraries = models.Library.objects.all()
            active_libraries = all_libraries.filter(active_start_date__lte=now)
            active_libraries = active_libraries.filter(Q(active_end_date__gte=now) | Q(active_end_date__isnull=True))
            libraries = set(all_libraries).difference(active_libraries)
        else:
            libraries = models.Library.objects.all()

        serializer = serializers.LibrarySerializer(libraries, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        data = request.data
        result, response_data = utils.validate_date_entries(data)

        if not result:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.LibrarySerializer(data=request.data)

        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        try:
            library = models.Library.objects.get(pk=request.data.get('id'))
        except models.Library.DoesNotExist:
            return Response({"detail": "Invalid request: Please check your \"PUT\" data"},
                            status=status.HTTP_400_BAD_REQUEST)

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

        raise LookupError("Unable to process request.")


class ProjectView(APIView):
    def get(self, request, *args, **kwargs):
        projects = models.Project.objects.all()
        serializer = serializers.ProjectSerializer(projects, many=True)
        return JsonResponse(serializer.data, safe=False)

    def _save_library_entries(self, project_id, libraries):
        for library in libraries:
            if library.get('remove', False):
                try:
                    models.ProjectLibrary.objects.filter(pk=library.get('id')).delete()
                except models.ProjectLibrary.DoesNotExist:
                    return False, {"detail": "Invalid request: Please check your \"POST\" data"}
            else:
                lib = {
                    'library_id': library['id'],
                    'version': library['version'],
                    'project_id': project_id
                }

                if library.get('new', False):
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
                                "Invalid request: Changes to library data not saved. Please check your \"POST\" data"}
                    else:
                        try:
                            entry.save(update_fields=lib)
                        except IntegrityError as err:
                            return False, {"detail": str(err)}

            return True, {}

    def delete(self, request, *args, **kwargs):
        try:
            remove_project = models.Project.objects.get(pk=request.data.get('id'))
        except models.Project.DoesNotExist:
            return Response({"detail": "Invalid request: Please check your \"DELETE\" data"},
                            status=status.HTTP_400_BAD_REQUEST)

        remove_project.delete()
        return Response(request.data)

    def post(self, request, *args, **kwargs):
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

        serializer = serializers.ProjectSerializer(data=request.data)

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

    def put(self, request, *args, **kwargs):
        try:
            if request.data.get('active_end_date', '') == '':
                request.data['active_end_date'] = None
        except AttributeError:
            pass

        try:
            project = models.Project.objects.get(pk=request.data.get('id'))
        except models.Project.DoesNotExist:
            return Response({"detail": "Invalid request: Please check your \"PUT\" data"},
                            status=status.HTTP_400_BAD_REQUEST)

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
