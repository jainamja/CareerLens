from rest_framework import serializers
from .models import Resume, Skill, ResumeSkill

def validate_pdf_size(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise serializers.ValidationError(f"File size must not exceed {max_size_mb} MB.")
    
    if file.content_type != 'application/pdf':
        raise serializers.ValidationError("Only PDF files are allowed.")
    return file

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name', 'category')

class ResumeSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, validators=[validate_pdf_size])
    
    class Meta:
        model = Resume
        fields = ('id', 'file', 'original_filename', 'uploaded_at', 'is_processed', 'processing_error', 'updated_at')
        read_only_fields = ('id', 'original_filename', 'uploaded_at', 'is_processed', 'processing_error', 'updated_at')

class ResumeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'original_filename', 'uploaded_at', 'is_processed', 'processing_error', 'updated_at', 'raw_text')
