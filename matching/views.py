from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from resumes.models import Resume
from jobs.models import Job
from .models import MatchResult
from .services.matcher import calculate_match

@login_required
def select_resume(request, job_id):
    """View to select a resume to match against a specific job."""
    job = get_object_or_404(Job, pk=job_id, user=request.user)
    resumes = Resume.objects.filter(user=request.user, is_processed=True)
    
    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        if resume_id:
            resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
            # Calculate and save
            match_result = calculate_match(resume, job)
            return redirect('matching:result', match_id=match_result.pk)
        else:
            messages.error(request, "Please select a resume.")
            
    return render(request, 'matching/select.html', {
        'job': job,
        'resumes': resumes
    })

@login_required
def match_result(request, match_id):
    """View to display the match result."""
    # Enforce ownership through the relationships
    match_result = get_object_or_404(MatchResult, pk=match_id, resume__user=request.user, job__user=request.user)
    
    # Retrieve optional skills logic
    # Optional skills are those that are in job optional skills and also in resume
    job_optional_skills = set(js.skill.name for js in match_result.job.job_skills.filter(is_required=False))
    resume_skills = set(rs.skill.name for rs in match_result.resume.resume_skills.all())
    matched_optional = sorted(list(job_optional_skills.intersection(resume_skills)))
    missing_optional = sorted(list(job_optional_skills - resume_skills))
    
    if request.method == 'POST' and 'recalculate' in request.POST:
        match_result = calculate_match(match_result.resume, match_result.job)
        messages.success(request, "Match recalculated successfully.")
        return redirect('matching:result', match_id=match_result.pk)
        
    return render(request, 'matching/result.html', {
        'match': match_result,
        'matched_optional': matched_optional,
        'missing_optional': missing_optional,
    })
