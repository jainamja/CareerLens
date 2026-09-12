import json
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

    def test_register_success(self):
        url = reverse('v1:auth:register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepassword',
            'password_confirm': 'securepassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username_fails(self):
        url = reverse('v1:auth:register')
        data = {
            'username': 'testuser',
            'email': 'different@example.com',
            'password': 'securepassword',
            'password_confirm': 'securepassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch_fails(self):
        url = reverse('v1:auth:register')
        data = {
            'username': 'anotheruser',
            'email': 'another@example.com',
            'password': 'securepassword',
            'password_confirm': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        url = reverse('v1:auth:login')
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify session is created
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_credentials_fails(self):
        url = reverse('v1:auth:login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_logout_success(self):
        self.client.login(username='testuser', password='testpassword123')
        url = reverse('v1:auth:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_me_authenticated(self):
        self.client.login(username='testuser', password='testpassword123')
        url = reverse('v1:auth:me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertTrue(response.data['is_authenticated'])
        self.assertNotIn('password', response.data)

    def test_me_unauthenticated_fails(self):
        url = reverse('v1:auth:me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_check_still_works(self):
        url = reverse('v1:health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
