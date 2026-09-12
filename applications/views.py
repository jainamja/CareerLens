from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import IntegrityError
from .models import Application
from .forms import ApplicationForm
from jobs.models import Job

@login_required
def application_list(request):
    applications = Application.objects.filter(user=request.user).select_related('job')
    
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
        
    query = request.GET.get('q')
    if query:
        applications = applications.filter(
            Q(job__title__icontains=query) | Q(job__company__icontains=query)
        )
        
    return render(request, 'applications/list.html', {
        'applications': applications,
        'current_status': status_filter,
        'search_query': query,
    })

@login_required
def application_kanban(request):
    applications = Application.objects.filter(user=request.user).select_related('job')
    
    query = request.GET.get('q')
    if query:
        applications = applications.filter(
            Q(job__title__icontains=query) | Q(job__company__icontains=query)
        )
        
    grouped_applications = []
    for val, label in Application.StatusChoices.choices:
        grouped_applications.append({
            'value': val,
            'label': label,
            'apps': [app for app in applications if app.status == val]
        })
        
    return render(request, 'applications/kanban.html', {
        'columns': grouped_applications,
        'search_query': query,
    })

@login_required
def application_create(request):
    job_id = request.GET.get('job')
    initial_data = {}
    
    if job_id:
        job = get_object_or_404(Job, pk=job_id, user=request.user)
        # Check if application already exists
        existing_app = Application.objects.filter(user=request.user, job=job).first()
        if existing_app:
            messages.info(request, "You are already tracking this job.")
            return redirect('applications:detail', pk=existing_app.pk)
        initial_data['job'] = job
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            try:
                application.save()
                messages.success(request, "Application tracked successfully.")
                return redirect('applications:list')
            except IntegrityError:
                messages.error(request, "You already have an application for this job.")
    else:
        form = ApplicationForm(initial=initial_data, user=request.user)
        
    return render(request, 'applications/form.html', {
        'form': form,
        'title': 'Add Application'
    })

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application.objects.select_related('job'), pk=pk, user=request.user)
    return render(request, 'applications/detail.html', {
        'application': application
    })

@login_required
def application_edit(request, pk):
    application = get_object_or_404(Application, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Application updated successfully.")
                return redirect('applications:detail', pk=application.pk)
            except IntegrityError:
                messages.error(request, "You already have an application for this job.")
    else:
        form = ApplicationForm(instance=application, user=request.user)
        
    return render(request, 'applications/form.html', {
        'form': form,
        'title': 'Edit Application',
        'application': application
    })

@login_required
def application_delete(request, pk):
    application = get_object_or_404(Application.objects.select_related('job'), pk=pk, user=request.user)
    
    if request.method == 'POST':
        application.delete()
        messages.success(request, "Application deleted successfully.")
        return redirect('applications:list')
        
    return render(request, 'applications/delete.html', {
        'application': application
    })
