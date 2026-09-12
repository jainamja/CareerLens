from django.urls import path
from .api_views import DashboardStatsView, AnalyticsView

app_name = 'dashboard_api'

urlpatterns = [
    path('dashboard/stats/', DashboardStatsView.as_view(), name='stats'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]
