from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from jobs.models import Job
from .models import Application
import datetime

class ApplicationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.job = Job.objects.create(user=self.user, title="Dev", company="Tech")
        
    def test_create_application(self):
        app = Application.objects.create(user=self.user, job=self.job)
        self.assertEqual(app.status, 'saved')
        self.assertIsNone(app.applied_date)
        
    def test_unique_together(self):
        Application.objects.create(user=self.user, job=self.job)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Application.objects.create(user=self.user, job=self.job)

class ApplicationWebTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')
        self.job_a = Job.objects.create(user=self.user_a, title="Job A", company="Company A")
        self.job_b = Job.objects.create(user=self.user_b, title="Job B", company="Company B")
        self.app_a = Application.objects.create(user=self.user_a, job=self.job_a, status='applied')
        
    def test_list_view(self):
        self.client.login(username='usera', password='password123')
        response = self.client.get(reverse('applications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Job A')
        
    def test_kanban_view(self):
        self.client.login(username='usera', password='password123')
        response = self.client.get(reverse('applications:kanban'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Job A')
        
    def test_create_view(self):
        self.client.login(username='usera', password='password123')
        job_new = Job.objects.create(user=self.user_a, title="New", company="C")
        
        # Test GET with prefilled job
        response = self.client.get(reverse('applications:create'), {'job': job_new.id})
        self.assertEqual(response.status_code, 200)
        
        # Test POST
        response = self.client.post(reverse('applications:create'), {
            'job': job_new.id,
            'status': 'assessment',
            'applied_date': '2026-09-12',
            'notes': 'Test'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Application.objects.filter(job=job_new, status='assessment').exists())
        
    def test_cross_user_access(self):
        self.client.login(username='usera', password='password123')
        # Try to view user_b's job in create
        response = self.client.get(reverse('applications:create'), {'job': self.job_b.id})
        self.assertEqual(response.status_code, 404)
        
        # Try to detail user_b's app (doesn't exist, let's create one)
        app_b = Application.objects.create(user=self.user_b, job=self.job_b)
        response = self.client.get(reverse('applications:detail', args=[app_b.id]))
        self.assertEqual(response.status_code, 404)
        
        response = self.client.post(reverse('applications:delete', args=[app_b.id]))
        self.assertEqual(response.status_code, 404)

class ApplicationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.job = Job.objects.create(user=self.user, title="API Job", company="Tech API")
        self.app = Application.objects.create(user=self.user, job=self.job, status='saved')
        self.url = reverse('v1:applications:application-list')
        
    def test_list_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Depending on pagination, data might be in response.data or response.data['results']
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['job_detail']['title'], "API Job")
        
    def test_create_api(self):
        self.client.force_authenticate(user=self.user)
        job2 = Job.objects.create(user=self.user, title="Job 2", company="C2")
        data = {
            'job': job2.id,
            'status': 'interview',
            'notes': 'API notes'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 2)
        
    def test_create_cross_user_job_api(self):
        other_user = User.objects.create_user(username='other', password='pw')
        other_job = Job.objects.create(user=other_user, title="Other Job", company="O")
        
        self.client.force_authenticate(user=self.user)
        data = {
            'job': other_job.id,
            'status': 'interview'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('job', response.data)
