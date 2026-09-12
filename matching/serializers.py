from rest_framework import serializers
from .models import MatchResult

class MatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchResult
        fields = [
            'id', 'resume', 'job', 'skill_coverage_score', 'text_similarity_score',
            'matched_skills', 'missing_skills', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
