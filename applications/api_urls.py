from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ApplicationViewSet

app_name = 'applications_api'

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
]
