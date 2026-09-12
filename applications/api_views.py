from rest_framework import viewsets, permissions, filters
from .models import Application
from .serializers import ApplicationSerializer

class ApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows applications to be viewed or edited.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the applications
        for the currently authenticated user.
        """
        queryset = Application.objects.filter(user=self.request.user).select_related('job')
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        q_param = self.request.query_params.get('q')
        if q_param:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(job__title__icontains=q_param) | Q(job__company__icontains=q_param)
            )
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
