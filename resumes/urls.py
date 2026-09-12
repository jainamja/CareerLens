from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('resumes/', views.resume_list, name='list'),
    path('resumes/<int:pk>/', views.resume_detail, name='detail'),
    path('resumes/<int:pk>/delete/', views.resume_delete, name='delete'),
    path('resumes/<int:pk>/reprocess/', views.resume_reprocess, name='reprocess'),
]
