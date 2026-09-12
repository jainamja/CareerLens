from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta

from resumes.models import Resume
from jobs.models import Job
from applications.models import Application
from matching.models import MatchResult

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Resumes
        resumes = Resume.objects.filter(user=user)
        total_resumes = resumes.count()
        processed_resumes = resumes.filter(is_processed=True).count()
        
        # Jobs
        jobs = Job.objects.filter(user=user)
        total_jobs = jobs.count()
        one_week_ago = timezone.now() - timedelta(days=7)
        jobs_this_week = jobs.filter(created_at__gte=one_week_ago).count()
        
        # Applications
        apps = Application.objects.filter(user=user)
        total_apps = apps.count()
        active_apps = apps.exclude(status__in=[Application.StatusChoices.REJECTED, Application.StatusChoices.OFFER]).count()
        
        status_counts = {choice[0]: 0 for choice in Application.StatusChoices.choices}
        for item in apps.values('status').annotate(count=Count('status')):
            status_counts[item['status']] = item['count']
            
        # Matches
        matches = MatchResult.objects.filter(resume__user=user, job__user=user).order_by('-created_at')
        total_matches = matches.count()
        latest_match = matches.first()
        
        return Response({
            "resumes": {
                "total": total_resumes,
                "processed": processed_resumes
            },
            "jobs": {
                "total": total_jobs,
                "recent": jobs_this_week
            },
            "applications": {
                "total": total_apps,
                "active": active_apps,
                "by_status": status_counts
            },
            "matches": {
                "total": total_matches,
                "latest_skill_coverage": float(latest_match.skill_coverage_score) if latest_match else None,
                "latest_text_similarity": float(latest_match.text_similarity_score) if latest_match else None
            }
        })

class AnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        apps = Application.objects.filter(user=user)
        total_apps = apps.count()
        interviews = apps.filter(status=Application.StatusChoices.INTERVIEW).count()
        offers = apps.filter(status=Application.StatusChoices.OFFER).count()
        
        interview_rate = (interviews / total_apps * 100) if total_apps > 0 else 0
        offer_rate = (offers / total_apps * 100) if total_apps > 0 else 0
        
        app_status_counts = {choice[0]: 0 for choice in Application.StatusChoices.choices}
        for item in apps.values('status').annotate(count=Count('status')):
            app_status_counts[item['status']] = item['count']
            
        matches = MatchResult.objects.filter(resume__user=user, job__user=user)
        match_aggregates = matches.aggregate(
            avg_cov=Avg('skill_coverage_score'),
            avg_sim=Avg('text_similarity_score')
        )
        
        jobs = Job.objects.filter(user=user)
        total_jobs = jobs.count()
        one_week_ago = timezone.now() - timedelta(days=7)
        jobs_this_week = jobs.filter(created_at__gte=one_week_ago).count()
        
        return Response({
            "applications": {
                "total": total_apps,
                "interview_rate": round(interview_rate, 2),
                "offer_rate": round(offer_rate, 2),
                "by_status": app_status_counts
            },
            "matches": {
                "total": matches.count(),
                "average_skill_coverage": round(match_aggregates['avg_cov'] or 0.0, 2),
                "average_text_similarity": round(match_aggregates['avg_sim'] or 0.0, 2)
            },
            "jobs": {
                "total": total_jobs,
                "added_this_week": jobs_this_week
            }
        })
