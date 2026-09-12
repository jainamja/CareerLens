from rest_framework import views, viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import MatchResult
from .serializers import MatchResultSerializer
from .services.matcher import calculate_match
from resumes.models import Resume
from jobs.models import Job

class MatchResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet to retrieve existing MatchResults.
    """
    serializer_class = MatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure user can only see matches for their own resumes/jobs
        return MatchResult.objects.filter(
            resume__user=self.request.user,
            job__user=self.request.user
        )

class CalculateMatchView(views.APIView):
    """
    API View to trigger a new match calculation or recalculation.
    POST data: {'resume_id': <id>, 'job_id': <id>}
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        resume_id = request.data.get('resume_id')
        job_id = request.data.get('job_id')
        
        if not resume_id or not job_id:
            return Response({"error": "resume_id and job_id are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify ownership
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        job = get_object_or_404(Job, id=job_id, user=request.user)
        
        # Calculate
        match_result = calculate_match(resume, job)
        
        serializer = MatchResultSerializer(match_result)
        return Response(serializer.data, status=status.HTTP_200_OK)
