from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    path('job/<int:job_id>/select-resume/', views.select_resume, name='select_resume'),
    path('result/<int:match_id>/', views.match_result, name='result'),
]
