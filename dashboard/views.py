from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
import json
from itertools import chain
from operator import attrgetter

from resumes.models import Resume, ResumeSkill, Skill
from jobs.models import Job, JobSkill
from applications.models import Application
from matching.models import MatchResult

@login_required(login_url='/login/')
def home(request):
    user = request.user
    
    # 1. Resumes
    resumes = Resume.objects.filter(user=user)
    total_resumes = resumes.count()
    processed_resumes = resumes.filter(is_processed=True).count()
    recent_resumes = resumes.order_by('-updated_at')[:5]
    
    # 2. Jobs
    jobs = Job.objects.filter(user=user)
    total_jobs = jobs.count()
    one_week_ago = timezone.now() - timedelta(days=7)
    jobs_this_week = jobs.filter(created_at__gte=one_week_ago).count()
    recent_jobs = jobs.order_by('-created_at')[:5]
    
    # 3. Applications
    apps = Application.objects.filter(user=user).select_related('job')
    total_apps = apps.count()
    active_apps = apps.exclude(status__in=[Application.StatusChoices.REJECTED, Application.StatusChoices.OFFER]).count()
    
    status_counts = apps.values('status').annotate(count=Count('status'))
    # Convert status counts to a fast lookup
    sc_dict = {item['status']: item['count'] for item in status_counts}
    
    pipeline_data = []
    for val, label in Application.StatusChoices.choices:
        pipeline_data.append({
            'label': label,
            'count': sc_dict.get(val, 0)
        })
        
    recent_apps = apps.order_by('-updated_at')[:5]
    
    # 4. Matches
    matches = MatchResult.objects.filter(resume__user=user, job__user=user).select_related('resume', 'job')
    total_matches = matches.count()
    latest_match = matches.order_by('-created_at').first()
    recent_matches = matches.order_by('-created_at')[:5]
    
    # 5. Skill Overview (From Resume)
    resume_skills = ResumeSkill.objects.filter(resume__user=user).select_related('skill')
    skill_frequencies = {}
    for rs in resume_skills:
        cat = rs.skill.category
        name = rs.skill.name
        if cat not in skill_frequencies:
            skill_frequencies[cat] = {}
        if name not in skill_frequencies[cat]:
            skill_frequencies[cat][name] = 0
        skill_frequencies[cat][name] += 1
        
    # 6. Missing Skills (From Matches)
    missing_freq = {}
    for m in matches:
        for skill_name in m.missing_skills:
            missing_freq[skill_name] = missing_freq.get(skill_name, 0) + 1
    sorted_missing = sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 7. Recent Activity (Unified Timeline)
    # Give them synthetic attributes to render uniformly
    activity_resumes = list(resumes.order_by('-uploaded_at')[:5])
    for r in activity_resumes:
        r.activity_type = 'resume'
        r.activity_time = r.uploaded_at
        r.activity_title = 'Resume uploaded'
        r.activity_desc = r.original_filename
        
    activity_jobs = list(jobs.order_by('-created_at')[:5])
    for j in activity_jobs:
        j.activity_type = 'job'
        j.activity_time = j.created_at
        j.activity_title = 'Job tracked'
        j.activity_desc = j.title

    activity_apps = list(apps.order_by('-updated_at')[:5])
    for a in activity_apps:
        a.activity_type = 'application'
        a.activity_time = a.updated_at
        a.activity_title = f'Application moved to {a.get_status_display()}'
        a.activity_desc = a.job.title
        
    activity_matches = list(matches.order_by('-created_at')[:5])
    for m in activity_matches:
        m.activity_type = 'match'
        m.activity_time = m.created_at
        m.activity_title = 'Match calculated'
        m.activity_desc = f"{m.job.title} ({m.skill_coverage_score}%)"

    all_activity = sorted(
        chain(activity_resumes, activity_jobs, activity_apps, activity_matches),
        key=attrgetter('activity_time'),
        reverse=True
    )[:8]

    context = {
        'total_resumes': total_resumes,
        'processed_resumes': processed_resumes,
        
        'total_jobs': total_jobs,
        'jobs_this_week': jobs_this_week,
        'recent_jobs': recent_jobs,
        
        'total_apps': total_apps,
        'active_apps': active_apps,
        'pipeline_data': pipeline_data,
        'recent_apps': recent_apps,
        
        'total_matches': total_matches,
        'latest_match': latest_match,
        'recent_matches': recent_matches,
        
        'skill_frequencies': skill_frequencies,
        'missing_skills': sorted_missing,
        'activities': all_activity,
        'status_choices': Application.StatusChoices.choices,
    }
    return render(request, 'dashboard/home.html', context)


@login_required(login_url='/login/')
def analytics_view(request):
    user = request.user
    
    # Time bounds
    now = timezone.now()
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)
    
    # Applications
    apps = Application.objects.filter(user=user)
    total_apps = apps.count()
    interviews = apps.filter(status=Application.StatusChoices.INTERVIEW).count()
    offers = apps.filter(status=Application.StatusChoices.OFFER).count()
    rejected = apps.filter(status=Application.StatusChoices.REJECTED).count()
    active_apps = total_apps - (offers + rejected)
    
    interview_rate = (interviews / total_apps * 100) if total_apps > 0 else 0
    offer_rate = (offers / total_apps * 100) if total_apps > 0 else 0
    
    app_status_counts = {choice[0]: {'label': choice[1], 'count': 0} for choice in Application.StatusChoices.choices}
    for item in apps.values('status').annotate(count=Count('status')):
        if item['status'] in app_status_counts:
            app_status_counts[item['status']]['count'] = item['count']
            
    apps_this_week = apps.filter(created_at__gte=one_week_ago).count()
    apps_this_month = apps.filter(created_at__gte=one_month_ago).count()
    
    # Matches
    matches = MatchResult.objects.filter(resume__user=user, job__user=user)
    match_aggregates = matches.aggregate(
        avg_cov=Avg('skill_coverage_score'),
        avg_sim=Avg('text_similarity_score'),
        max_cov=Max('skill_coverage_score'),
        max_sim=Max('text_similarity_score')
    )
    
    # Match Distribution (Coverage)
    score_dist = {
        '0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0
    }
    for m in matches:
        score = float(m.skill_coverage_score)
        if score <= 20: score_dist['0-20'] += 1
        elif score <= 40: score_dist['21-40'] += 1
        elif score <= 60: score_dist['41-60'] += 1
        elif score <= 80: score_dist['61-80'] += 1
        else: score_dist['81-100'] += 1
        
    # Jobs
    jobs = Job.objects.filter(user=user)
    total_jobs = jobs.count()
    jobs_this_week = jobs.filter(created_at__gte=one_week_ago).count()
    jobs_this_month = jobs.filter(created_at__gte=one_month_ago).count()
    
    # Common required job skills
    job_skills = JobSkill.objects.filter(job__user=user, is_required=True).values('skill__name').annotate(count=Count('skill')).order_by('-count')[:5]

    context = {
        'has_apps': total_apps > 0,
        'total_apps': total_apps,
        'active_apps': active_apps,
        'interviews': interviews,
        'offers': offers,
        'rejected': rejected,
        'interview_rate': interview_rate,
        'offer_rate': offer_rate,
        'app_status_counts': app_status_counts.values(),
        'apps_this_week': apps_this_week,
        'apps_this_month': apps_this_month,
        
        'has_matches': matches.exists(),
        'avg_cov': match_aggregates['avg_cov'] or 0.0,
        'avg_sim': match_aggregates['avg_sim'] or 0.0,
        'max_cov': match_aggregates['max_cov'] or 0.0,
        'max_sim': match_aggregates['max_sim'] or 0.0,
        'score_dist': score_dist,
        'max_score_count': max(list(score_dist.values()) + [1]),
        
        'total_jobs': total_jobs,
        'jobs_this_week': jobs_this_week,
        'jobs_this_month': jobs_this_month,
        'common_job_skills': job_skills,
    }
    return render(request, 'dashboard/analytics.html', context)
