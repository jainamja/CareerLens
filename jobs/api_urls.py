from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import JobViewSet

app_name = 'jobs_api'

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')

urlpatterns = [
    path('', include(router.urls)),
]
