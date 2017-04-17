# Authored by Peter Garas for Ocom Software

from django.contrib.auth.models import User
from api.models import Library, Project, ProjectLibrary
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name', 'email', 'is_staff')
        read_only_fields = ('id', 'is_staff')

    def restore_object(self, attrs, instance=None):
        user = super(UserSerializer, self).restore_object(attrs, instance)
        user.set_password(attrs['password'])
        return user


class LibrarySerializer(serializers.ModelSerializer):
    description = serializers.CharField()
    active_start_date = serializers.DateField()
    active_end_date = serializers.DateField(allow_null=True)

    class Meta:
        model = Library
        fields = '__all__'


class ProjectLibrarySerializer(serializers.HyperlinkedModelSerializer):
    library_id = serializers.ReadOnlyField(source='library.id')
    description = serializers.CharField(source='library.description')
    version = serializers.CharField()

    class Meta:
        model = ProjectLibrary
        fields = ('id', 'library_id', 'description', 'version')


class LibraryVersionySerializer(serializers.ModelSerializer):
    version = serializers.CharField()

    class Meta:
        model = ProjectLibrary
        fields = ('id', 'version',)


class ProjectSerializer(serializers.ModelSerializer):
    active_start_date = serializers.DateField()
    active_end_date = serializers.DateField(allow_null=True)
    libraries = ProjectLibrarySerializer(source='projectlibrary_set', many=True, allow_null=True, read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'active_start_date', 'active_end_date', 'description', 'client_name', 'git_url',
                  'testing_url', 'production_url', 'libraries')
