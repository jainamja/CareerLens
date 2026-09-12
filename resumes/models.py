import uuid
import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def resume_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('resumes', str(instance.user.id), new_filename)

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    raw_text = models.TextField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.original_filename} ({self.user.username})"

    class Meta:
        ordering = ['-uploaded_at']

class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('language', 'Language'),
        ('framework', 'Framework'),
        ('library', 'Library'),
        ('database', 'Database'),
        ('tool', 'Tool'),
        ('cloud', 'Cloud'),
        ('concept', 'Concept'),
    ]
    
    name = models.CharField(max_length=100)
    normalized_name = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ResumeSkill(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='resume_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='resume_skills')
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('resume', 'skill')
        
    def __str__(self):
        return f"{self.resume.user.username} - {self.skill.name}"

