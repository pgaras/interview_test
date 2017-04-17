"""interview_test URL Configuration"""

from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from api import views, viewsets


router = routers.DefaultRouter()
router.register(r'auth', viewsets.AuthViewSet)
router.register(r'libraries', viewsets.LibraryViewSet)
router.register(r'projects', viewsets.ProjectViewSet)
router.register(r'project_libraries', viewsets.ProjectLibraryViewSet)


urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.HomeView.as_view(), name='project'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
