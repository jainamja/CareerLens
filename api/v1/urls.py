from django.urls import path, include
from api.views import HealthCheckView

app_name = 'api_v1'

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('auth/', include('accounts.api_urls', namespace='auth')),
    path('', include('resumes.api_urls', namespace='resumes')),
    path('', include('jobs.api_urls', namespace='jobs')),
    path('', include('applications.api_urls', namespace='applications')),
    path('matching/', include('matching.api_urls', namespace='matching')),
    path('', include('dashboard.api_urls', namespace='dashboard')),
]
