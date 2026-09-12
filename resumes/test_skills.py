import io
import pymupdf as fitz
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Resume, Skill, ResumeSkill
from .services.pdf_extractor import process_resume_pdf, PDFExtractionError
from .services.skill_extractor import extract_skills
from .services.resume_processor import process_resume
from django.core.management import call_command
import os
import tempfile

class SkillExtractionTests(TestCase):
    def setUp(self):
        call_command('seed_skills')
        
    def test_skill_creation_and_uniqueness(self):
        skill = Skill.objects.get(normalized_name='python')
        self.assertEqual(skill.name, 'Python')
        self.assertEqual(skill.category, 'language')
        
        # Test command is idempotent
        call_command('seed_skills')
        self.assertEqual(Skill.objects.filter(normalized_name='python').count(), 1)
        
    def test_extraction_basic(self):
        text = "I am a backend developer experienced with Python, Django, and PostgreSQL."
        skills = extract_skills(text)
        names = [s.name for s in skills]
        self.assertIn("Python", names)
        self.assertIn("Django", names)
        self.assertIn("PostgreSQL", names)
        self.assertNotIn("Java", names)
        
    def test_extraction_case_handling(self):
        text = "Experienced with pyThon, dJaNgO, and PANDAS."
        skills = extract_skills(text)
        names = [s.name for s in skills]
        self.assertIn("Python", names)
        self.assertIn("Django", names)
        self.assertIn("Pandas", names)
        
    def test_extraction_aliases(self):
        text = "I built APIs with DRF, JS, and Postgres."
        skills = extract_skills(text)
        names = [s.name for s in skills]
        self.assertIn("Django REST Framework", names)
        self.assertIn("JavaScript", names)
        self.assertIn("PostgreSQL", names)
        
    def test_extraction_false_positives(self):
        # "CSS" should not trigger "C"
        text = "I know CSS and React."
        skills = extract_skills(text)
        names = [s.name for s in skills]
        self.assertIn("CSS", names)
        self.assertIn("React", names)
        self.assertNotIn("C", names)
        
        # "C" alone should trigger "C"
        text2 = "I program in C and C++."
        skills2 = extract_skills(text2)
        names2 = [s.name for s in skills2]
        self.assertIn("C", names2)
        self.assertIn("C++", names2)
        
    def test_resume_processor_integration(self):
        user = User.objects.create_user(username='usera', password='password123')
        resume = Resume.objects.create(user=user, original_filename="test.pdf")
        # Fake the file path and text extraction by directly saving raw_text and mocking extract_skills?
        # Actually, let's just use the mock or a real simple PDF to test the full processor
        temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        filepath = os.path.join(temp_dir.name, "test_resume.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 50), "Python, Django, React")
        doc.save(filepath)
        
        with open(filepath, 'rb') as f:
            pdf_file = SimpleUploadedFile("test_resume.pdf", f.read(), content_type='application/pdf')
            
        resume.file = pdf_file
        resume.save()
        
        process_resume(resume)
        
        self.assertTrue(resume.is_processed)
        skills = [rs.skill.name for rs in resume.resume_skills.all()]
        self.assertIn("Python", skills)
        self.assertIn("Django", skills)
        self.assertIn("React", skills)
        
        # Reprocessing: change the text (simulating updated pdf or just calling process again on different text)
        page.insert_text(fitz.Point(50, 100), "No React anymore")
        # To simulate a changed PDF, we just change the raw_text before processing? No, process_resume extracts from file.
        # We will create a new PDF
        filepath_new = os.path.join(temp_dir.name, "test_resume_v2.pdf")
        doc2 = fitz.open()
        page2 = doc2.new_page()
        page2.insert_text(fitz.Point(50, 50), "Python, Django")
        doc2.save(filepath_new)
        
        with open(filepath_new, 'rb') as f:
            resume.file = SimpleUploadedFile("test_resume_v2.pdf", f.read(), content_type='application/pdf')
        resume.save()
        
        process_resume(resume)
        resume.refresh_from_db()
        skills_v2 = [rs.skill.name for rs in resume.resume_skills.all()]
        self.assertIn("Python", skills_v2)
        self.assertIn("Django", skills_v2)
        self.assertNotIn("React", skills_v2)
        
        temp_dir.cleanup()
