from django.urls import path
from .api_views import RegisterAPIView, LoginAPIView, LogoutAPIView, MeAPIView

app_name = 'accounts_api'

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('me/', MeAPIView.as_view(), name='me'),
]
