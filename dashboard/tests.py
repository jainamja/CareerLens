from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from resumes.models import Resume, Skill, ResumeSkill
from jobs.models import Job, JobSkill
from applications.models import Application
from matching.models import MatchResult

class DashboardWebTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')
        
        # User A data
        self.resume_a = Resume.objects.create(user=self.user_a, original_filename="a.pdf")
        self.job_a = Job.objects.create(user=self.user_a, title="Job A", company="Corp A")
        self.app_a = Application.objects.create(user=self.user_a, job=self.job_a, status='applied')
        self.match_a = MatchResult.objects.create(resume=self.resume_a, job=self.job_a, skill_coverage_score=80, text_similarity_score=75)
        
        # User B data
        self.resume_b = Resume.objects.create(user=self.user_b, original_filename="b.pdf")
        self.job_b = Job.objects.create(user=self.user_b, title="Job B", company="Corp B")
        self.app_b = Application.objects.create(user=self.user_b, job=self.job_b, status='offer')
        
    def test_dashboard_access_unauthenticated(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertRedirects(response, '/login/?next=/dashboard/')
        
    def test_dashboard_home_authenticated(self):
        self.client.login(username='usera', password='password123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        
        # Verify counts in context
        self.assertEqual(response.context['total_resumes'], 1)
        self.assertEqual(response.context['total_jobs'], 1)
        self.assertEqual(response.context['total_apps'], 1)
        self.assertEqual(response.context['total_matches'], 1)
        
        # Verify data isolation
        self.assertNotContains(response, "Corp B")
        self.assertContains(response, "Corp A")

    def test_dashboard_analytics_authenticated(self):
        self.client.login(username='usera', password='password123')
        response = self.client.get(reverse('dashboard:analytics'))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.context['total_apps'], 1)
        self.assertEqual(response.context['interviews'], 0)
        self.assertEqual(response.context['offers'], 0)
        
        # User B has an offer
        self.client.logout()
        self.client.login(username='userb', password='password123')
        response = self.client.get(reverse('dashboard:analytics'))
        self.assertEqual(response.context['offers'], 1)
        self.assertEqual(response.context['offer_rate'], 100.0)

    def test_empty_dashboard(self):
        empty_user = User.objects.create_user(username='empty', password='password123')
        self.client.login(username='empty', password='password123')
        
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_resumes'], 0)
        
        response = self.client.get(reverse('dashboard:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_apps'], 0)


from rest_framework.test import APITestCase
from rest_framework import status

class DashboardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='password123')
        self.job = Job.objects.create(user=self.user, title="API Job", company="Tech API")
        self.app = Application.objects.create(user=self.user, job=self.job, status='saved')
        
    def test_dashboard_stats_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api_v1:dashboard:stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['jobs']['total'], 1)
        self.assertEqual(data['applications']['total'], 1)
        
    def test_analytics_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api_v1:dashboard:analytics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['applications']['total'], 1)
        self.assertEqual(data['applications']['offer_rate'], 0.0)
