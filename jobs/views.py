from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Job, JobSkill
from resumes.models import Skill
from .forms import JobForm

@login_required
def job_list(request):
    jobs = Job.objects.filter(user=request.user)
    
    # Search functionality
    query = request.GET.get('q', '').strip()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__icontains=query) |
            Q(description__icontains=query)
        )
        
    # Filtering functionality
    location = request.GET.get('location', '').strip()
    if location:
        jobs = jobs.filter(location__icontains=location)
        
    skill_id = request.GET.get('skill')
    if skill_id:
        jobs = jobs.filter(job_skills__skill_id=skill_id, job_skills__is_required=True)
        
    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    skills = Skill.objects.all().order_by('name')
    
    return render(request, 'jobs/list.html', {
        'page_obj': page_obj,
        'query': query,
        'location_filter': location,
        'skill_filter': skill_id,
        'skills': skills,
    })

@login_required
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            
            # Save skills
            for skill in form.cleaned_data['required_skills']:
                JobSkill.objects.create(job=job, skill=skill, is_required=True)
            for skill in form.cleaned_data['optional_skills']:
                JobSkill.objects.create(job=job, skill=skill, is_required=False)
                
            messages.success(request, 'Job created successfully.')
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobForm()
    return render(request, 'jobs/create_edit.html', {'form': form, 'title': 'Add Job'})

@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            
            # Update skills
            JobSkill.objects.filter(job=job).delete()
            for skill in form.cleaned_data['required_skills']:
                JobSkill.objects.create(job=job, skill=skill, is_required=True)
            for skill in form.cleaned_data['optional_skills']:
                JobSkill.objects.create(job=job, skill=skill, is_required=False)
                
            messages.success(request, 'Job updated successfully.')
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/create_edit.html', {'form': form, 'title': 'Edit Job', 'job': job})

@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    required_skills = job.job_skills.filter(is_required=True).select_related('skill')
    optional_skills = job.job_skills.filter(is_required=False).select_related('skill')
    
    return render(request, 'jobs/detail.html', {
        'job': job,
        'required_skills': required_skills,
        'optional_skills': optional_skills,
    })

@login_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('jobs:list')
    return render(request, 'jobs/delete.html', {'job': job})
