from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import MatchResultViewSet, CalculateMatchView

app_name = 'matching_api'

router = DefaultRouter()
router.register(r'matches', MatchResultViewSet, basename='match')

urlpatterns = [
    path('', include(router.urls)),
    path('calculate/', CalculateMatchView.as_view(), name='calculate'),
]
