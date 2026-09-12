from django.db import models
from resumes.models import Resume
from jobs.models import Job

class MatchResult(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='match_results')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='match_results')
    
    skill_coverage_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    text_similarity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('resume', 'job')
        
    def __str__(self):
        return f"Match: {self.resume.user.username} - {self.resume.original_filename} <-> {self.job.title}"
