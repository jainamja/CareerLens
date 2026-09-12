from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('', views.application_list, name='list'),
    path('kanban/', views.application_kanban, name='kanban'),
    path('create/', views.application_create, name='create'),
    path('<int:pk>/', views.application_detail, name='detail'),
    path('<int:pk>/edit/', views.application_edit, name='edit'),
    path('<int:pk>/delete/', views.application_delete, name='delete'),
]
