from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ResumeViewSet

app_name = 'resumes_api'

router = DefaultRouter()
router.register(r'resumes', ResumeViewSet, basename='resume')

urlpatterns = [
    path('', include(router.urls)),
]
