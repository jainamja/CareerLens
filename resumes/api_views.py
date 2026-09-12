from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Resume
from .serializers import ResumeSerializer, ResumeDetailSerializer
from .services.resume_processor import process_resume

class ResumeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
        
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ResumeDetailSerializer
        return ResumeSerializer

    def perform_create(self, serializer):
        file = self.request.data.get('file')
        original_filename = file.name if file else "unknown.pdf"
        resume = serializer.save(user=self.request.user, original_filename=original_filename)
        # Process the resume synchronously
        process_resume(resume)
        
    def perform_destroy(self, instance):
        # File field cleanup could happen via signals or here
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()

    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        resume = self.get_object()
        
        skills = []
        if resume.is_processed:
            skills = [{'name': rs.skill.name, 'category': rs.skill.category} for rs in resume.resume_skills.select_related('skill').all()]
            
        return Response({
            "id": resume.id,
            "original_filename": resume.original_filename,
            "is_processed": resume.is_processed,
            "processing_error": resume.processing_error,
            "raw_text": resume.raw_text,
            "skills": skills
        })
        
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        resume = self.get_object()
        process_resume(resume)
        return Response({"message": "Resume reprocessing initiated."})
