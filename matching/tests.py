from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from resumes.models import Resume, Skill, ResumeSkill
from jobs.models import Job, JobSkill
from .models import MatchResult
from .services.matcher import calculate_skill_coverage, calculate_text_similarity, calculate_match
from django.core.management import call_command
import decimal

class MatchingServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        call_command('seed_skills')
        self.python_skill = Skill.objects.get(normalized_name='python')
        self.django_skill = Skill.objects.get(normalized_name='django')
        self.aws_skill = Skill.objects.get(normalized_name='aws')
        
        self.resume = Resume.objects.create(
            user=self.user,
            original_filename="resume.pdf",
            raw_text="I am a backend developer experienced in Python and Django."
        )
        ResumeSkill.objects.create(resume=self.resume, skill=self.python_skill)
        ResumeSkill.objects.create(resume=self.resume, skill=self.django_skill)
        
        self.job = Job.objects.create(
            user=self.user,
            title="Backend Dev",
            description="Looking for a Python developer with Django and AWS experience."
        )
        # Required skills: Python, Django, AWS
        JobSkill.objects.create(job=self.job, skill=self.python_skill, is_required=True)
        JobSkill.objects.create(job=self.job, skill=self.django_skill, is_required=True)
        JobSkill.objects.create(job=self.job, skill=self.aws_skill, is_required=True)
        
    def test_skill_coverage(self):
        score, matched, missing = calculate_skill_coverage(self.resume, self.job)
        # Required are Python, Django, AWS. Resume has Python, Django.
        # Score = 2/3 = 66.67
        self.assertEqual(score, 66.67)
        self.assertIn("Python", matched)
        self.assertIn("Django", matched)
        self.assertIn("AWS", missing)
        self.assertEqual(len(matched), 2)
        self.assertEqual(len(missing), 1)
        
    def test_skill_coverage_no_required_skills(self):
        # Remove all required skills
        JobSkill.objects.all().delete()
        score, matched, missing = calculate_skill_coverage(self.resume, self.job)
        self.assertEqual(score, 0.0)
        self.assertEqual(matched, [])
        self.assertEqual(missing, [])
        
    def test_skill_coverage_ignores_optional(self):
        # Change AWS to optional
        js = JobSkill.objects.get(skill=self.aws_skill)
        js.is_required = False
        js.save()
        
        score, matched, missing = calculate_skill_coverage(self.resume, self.job)
        # Now required are only Python and Django. Resume has both. Score = 100
        self.assertEqual(score, 100.0)
        self.assertNotIn("AWS", missing)
        
    def test_text_similarity(self):
        score = calculate_text_similarity(self.resume, self.job)
        self.assertTrue(0.0 < score <= 100.0)
        
    def test_text_similarity_empty(self):
        empty_resume = Resume.objects.create(user=self.user, original_filename="e.pdf", raw_text="")
        score = calculate_text_similarity(empty_resume, self.job)
        self.assertEqual(score, 0.0)

    def test_calculate_match_integration(self):
        result = calculate_match(self.resume, self.job)
        self.assertEqual(result.resume, self.resume)
        self.assertEqual(result.job, self.job)
        self.assertEqual(float(result.skill_coverage_score), 66.67)
        self.assertTrue(result.text_similarity_score > 0)
        self.assertIn("Python", result.matched_skills)
        self.assertIn("AWS", result.missing_skills)

class MatchResultModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.resume = Resume.objects.create(user=self.user, original_filename="a.pdf")
        self.job = Job.objects.create(user=self.user, title="Job")
        
    def test_unique_together(self):
        MatchResult.objects.create(resume=self.resume, job=self.job)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            MatchResult.objects.create(resume=self.resume, job=self.job)

class MatchingAPITests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')
        
        self.resume_a = Resume.objects.create(user=self.user_a, original_filename="a.pdf", raw_text="text")
        self.job_a = Job.objects.create(user=self.user_a, title="Job A", description="text")
        
        self.resume_b = Resume.objects.create(user=self.user_b, original_filename="b.pdf", raw_text="text")
        self.job_b = Job.objects.create(user=self.user_b, title="Job B", description="text")
        
        self.url_calculate = reverse('v1:matching:calculate')

    def test_calculate_match_api(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'resume_id': self.resume_a.id,
            'job_id': self.job_a.id
        }
        response = self.client.post(self.url_calculate, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['skill_coverage_score'], '0.00')
        self.assertTrue(float(response.data['text_similarity_score']) > 0)
        
    def test_cross_user_matching(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            'resume_id': self.resume_b.id, # Belongs to user b
            'job_id': self.job_a.id
        }
        response = self.client.post(self.url_calculate, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class MatchingWebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='usera', password='password123')
        self.resume = Resume.objects.create(user=self.user, original_filename="a.pdf", is_processed=True)
        self.job = Job.objects.create(user=self.user, title="Job A")
        self.client.login(username='usera', password='password123')
        
    def test_select_resume_view(self):
        response = self.client.get(reverse('matching:select_resume', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.resume.original_filename)
        
    def test_select_resume_post(self):
        response = self.client.post(reverse('matching:select_resume', args=[self.job.id]), {
            'resume_id': self.resume.id
        })
        self.assertEqual(response.status_code, 302)
        match_result = MatchResult.objects.get(resume=self.resume, job=self.job)
        self.assertRedirects(response, reverse('matching:result', args=[match_result.id]))
        
    def test_match_result_view(self):
        match = calculate_match(self.resume, self.job)
        response = self.client.get(reverse('matching:result', args=[match.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Match Analysis")
        self.assertContains(response, self.job.title)
