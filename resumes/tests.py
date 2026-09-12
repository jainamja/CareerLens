import io
import pymupdf as fitz
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Resume
from .services.pdf_extractor import process_resume_pdf, PDFExtractionError
import os
import tempfile

class PDFExtractorTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_test_pdf(self, text, filename, encrypt=False):
        doc = fitz.open()
        if text is not None:
            page = doc.new_page()
            page.insert_text(fitz.Point(50, 50), text)
        
        filepath = os.path.join(self.temp_dir.name, filename)
        if encrypt:
            doc.save(filepath, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="password")
        else:
            doc.save(filepath)
        return filepath

    def test_valid_pdf_extraction(self):
        filepath = self.create_test_pdf("John Doe\nPython Developer", "test1.pdf")
        text = process_resume_pdf(filepath)
        self.assertIn("John Doe", text)
        self.assertIn("Python Developer", text)

    def test_empty_pdf_extraction(self):
        filepath = self.create_test_pdf("", "empty.pdf")
        with self.assertRaises(PDFExtractionError) as context:
            process_resume_pdf(filepath)
        self.assertIn("No readable text", str(context.exception))

    def test_encrypted_pdf_extraction(self):
        filepath = self.create_test_pdf("Secret", "encrypted.pdf", encrypt=True)
        with self.assertRaises(PDFExtractionError) as context:
            process_resume_pdf(filepath)
        self.assertIn("password protected", str(context.exception))

    def test_corrupted_pdf_extraction(self):
        filepath = os.path.join(self.temp_dir.name, "corrupt.pdf")
        with open(filepath, "w") as f:
            f.write("This is not a pdf file")
            
        with self.assertRaises(PDFExtractionError) as context:
            process_resume_pdf(filepath)
        self.assertIn("We couldn't read this PDF", str(context.exception))


class ResumeAPITests(APITestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('seed_skills')
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')

    def generate_pdf_file(self, filename="test.pdf", size=1024):
        # Generate a valid pdf file in memory
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 50), "Test Resume")
        pdf_bytes = doc.write()
        
        # If we need a larger file, we can pad it (though PDF might be corrupt if we just pad blindly)
        # For valid PDF size testing, we'll use a mocked size or just the small valid PDF
        return SimpleUploadedFile(filename, pdf_bytes, content_type='application/pdf')

    def test_upload_resume_success(self):
        self.client.login(username='usera', password='password123')
        url = reverse('v1:resumes:resume-list')
        pdf_file = self.generate_pdf_file()
        response = self.client.post(url, {'file': pdf_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Resume.objects.count(), 1)
        resume = Resume.objects.first()
        self.assertEqual(resume.user, self.user_a)
        self.assertTrue(resume.is_processed)
        self.assertIn("Test Resume", resume.raw_text)

    def test_upload_non_pdf_fails(self):
        self.client.login(username='usera', password='password123')
        url = reverse('v1:resumes:resume-list')
        txt_file = SimpleUploadedFile("test.txt", b"Hello", content_type='text/plain')
        response = self.client.post(url, {'file': txt_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
        self.assertEqual(Resume.objects.count(), 0)

    def test_upload_oversized_file_fails(self):
        self.client.login(username='usera', password='password123')
        url = reverse('v1:resumes:resume-list')
        # Simulate oversized file
        large_file = SimpleUploadedFile("large.pdf", b"x" * (6 * 1024 * 1024), content_type='application/pdf')
        response = self.client.post(url, {'file': large_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
        self.assertIn('exceed', str(response.data['file']))

    def test_security_user_cannot_access_others_resume(self):
        # User A creates a resume
        pdf_file = self.generate_pdf_file("usera.pdf")
        resume = Resume.objects.create(user=self.user_a, file=pdf_file, original_filename="usera.pdf")

        # User B tries to access it
        self.client.login(username='userb', password='password123')
        url_detail = reverse('v1:resumes:resume-detail', kwargs={'pk': resume.pk})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # User B tries to delete it
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # User B tries to reprocess it
        url_reprocess = reverse('v1:resumes:resume-reprocess', kwargs={'pk': resume.pk})
        response = self.client.post(url_reprocess)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_access_fails(self):
        url = reverse('v1:resumes:resume-list')
        response = self.client.get(url)
        # DRF session auth usually returns 403 Forbidden for default IsAuthenticated unless modified,
        # but in our setup it returns 403. Let's just check it's not 2xx.
        self.assertIn(response.status_code, [401, 403])

    def test_reprocess_resume(self):
        self.client.login(username='usera', password='password123')
        pdf_file = self.generate_pdf_file("usera.pdf")
        resume = Resume.objects.create(user=self.user_a, file=pdf_file, original_filename="usera.pdf", is_processed=False)
        
        url = reverse('v1:resumes:resume-reprocess', kwargs={'pk': resume.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resume.refresh_from_db()
        self.assertTrue(resume.is_processed)
        self.assertIn("Test Resume", resume.raw_text)
