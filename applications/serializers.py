from rest_framework import serializers
from .models import Application
from jobs.serializers import JobSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    # Read-only nested job data for response
    job_detail = JobSerializer(source='job', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_detail', 'status', 'applied_date', 
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_job(self, value):
        request = self.context.get('request')
        if request and value.user != request.user:
            raise serializers.ValidationError("You can only apply to jobs you own.")
        return value
