from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Job, JobSkill
from resumes.models import Skill
from django.core.management import call_command

class JobModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        call_command('seed_skills')
        self.skill1 = Skill.objects.get(normalized_name='python')
        self.skill2 = Skill.objects.get(normalized_name='django')

    def test_job_creation(self):
        job = Job.objects.create(
            user=self.user,
            title="Backend Developer",
            company="Test Corp",
            description="Looking for a dev."
        )
        self.assertEqual(job.title, "Backend Developer")
        self.assertTrue(job.created_at)
        self.assertTrue(job.updated_at)
        
    def test_job_skill_creation_and_uniqueness(self):
        job = Job.objects.create(user=self.user, title="Dev", company="Corp", description="Desc")
        JobSkill.objects.create(job=job, skill=self.skill1, is_required=True)
        JobSkill.objects.create(job=job, skill=self.skill2, is_required=False)
        
        self.assertEqual(job.job_skills.count(), 2)
        
        # Test uniqueness constraint
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            JobSkill.objects.create(job=job, skill=self.skill1)


class JobOwnershipTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')
        
        self.job_a = Job.objects.create(user=self.user_a, title="Job A", company="Corp A", description="Desc A")
        self.job_b = Job.objects.create(user=self.user_b, title="Job B", company="Corp B", description="Desc B")
        
    def test_web_ownership(self):
        self.client.login(username='usera', password='password123')
        
        # List should only show Job A
        response = self.client.get(reverse('jobs:list'))
        self.assertContains(response, "Job A")
        self.assertNotContains(response, "Job B")
        
        # Detail view for Job B should be 404 for User A
        response = self.client.get(reverse('jobs:detail', args=[self.job_b.id]))
        self.assertEqual(response.status_code, 404)
        
        # Edit view for Job B should be 404
        response = self.client.get(reverse('jobs:edit', args=[self.job_b.id]))
        self.assertEqual(response.status_code, 404)
        
        # Delete view for Job B should be 404
        response = self.client.post(reverse('jobs:delete', args=[self.job_b.id]))
        self.assertEqual(response.status_code, 404)


class JobSearchFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        call_command('seed_skills')
        self.skill = Skill.objects.get(normalized_name='python')
        
        self.job1 = Job.objects.create(user=self.user, title="Python Dev", company="Acme", description="Backend", location="Remote")
        self.job2 = Job.objects.create(user=self.user, title="Frontend Dev", company="Beta", description="UI UX", location="New York")
        
        JobSkill.objects.create(job=self.job1, skill=self.skill, is_required=True)
        
        self.client.login(username='testuser', password='password123')
        
    def test_search_title(self):
        response = self.client.get(reverse('jobs:list') + '?q=python')
        self.assertContains(response, "Python Dev")
        self.assertNotContains(response, "Frontend Dev")
        
    def test_search_company(self):
        response = self.client.get(reverse('jobs:list') + '?q=Beta')
        self.assertContains(response, "Frontend Dev")
        self.assertNotContains(response, "Python Dev")
        
    def test_filter_location(self):
        response = self.client.get(reverse('jobs:list') + '?location=Remote')
        self.assertContains(response, "Python Dev")
        self.assertNotContains(response, "Frontend Dev")
        
    def test_filter_skill(self):
        response = self.client.get(reverse('jobs:list') + f'?skill={self.skill.id}')
        self.assertContains(response, "Python Dev")
        self.assertNotContains(response, "Frontend Dev")


class JobAPITests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')
        call_command('seed_skills')
        self.skill = Skill.objects.get(normalized_name='python')
        
        self.job = Job.objects.create(user=self.user_a, title="Job API", company="Corp API", description="Desc")
        JobSkill.objects.create(job=self.job, skill=self.skill, is_required=True)
        
        self.url_list = reverse('v1:jobs:job-list')
        self.url_detail = reverse('v1:jobs:job-detail', args=[self.job.id])

    def test_auth_required(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_get_jobs_ownership(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated DRF responses
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)
        
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 0)
        
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_create_job_with_skills(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            "title": "New API Job",
            "company": "API Corp",
            "description": "API desc",
            "skills": [
                {"skill_id": self.skill.id, "is_required": True}
            ]
        }
        response = self.client.post(self.url_list, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.filter(user=self.user_a).count(), 2)
        
        job_id = response.data['id']
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.job_skills.count(), 1)
        self.assertTrue(job.job_skills.first().is_required)
        
    def test_update_job(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            "title": "Updated API Job"
        }
        response = self.client.patch(self.url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Updated API Job")
        
    def test_delete_job(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Job.objects.count(), 0)
