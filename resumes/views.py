from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Resume
from .forms import ResumeUploadForm
from .services.resume_processor import process_resume

@login_required(login_url='/login/')
def resume_list(request):
    resumes = Resume.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.original_filename = request.FILES['file'].name
            resume.save()
            process_resume(resume)
            messages.success(request, 'Resume uploaded and processed successfully.')
            return redirect('resumes:list')
        else:
            messages.error(request, 'Failed to upload resume. Please check the errors.')
    else:
        form = ResumeUploadForm()
        
    return render(request, 'resumes/list.html', {'resumes': resumes, 'form': form})

@login_required(login_url='/login/')
def resume_detail(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    grouped_skills = {}
    if resume.is_processed:
        for rs in resume.resume_skills.select_related('skill').all():
            cat = rs.skill.get_category_display()
            if cat not in grouped_skills:
                grouped_skills[cat] = []
            grouped_skills[cat].append(rs.skill)
            
    return render(request, 'resumes/detail.html', {'resume': resume, 'grouped_skills': grouped_skills})

@login_required(login_url='/login/')
def resume_delete(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        if resume.file:
            resume.file.delete(save=False)
        resume.delete()
        messages.success(request, 'Resume deleted successfully.')
        return redirect('resumes:list')
    # If GET, you could show a confirmation page, but typically handled via POST from list/detail
    return redirect('resumes:list')

@login_required(login_url='/login/')
def resume_reprocess(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        process_resume(resume)
        messages.success(request, 'Resume reprocessing complete.')
    return redirect('resumes:detail', pk=pk)
