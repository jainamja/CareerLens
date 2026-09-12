from rest_framework import serializers
from .models import Job, JobSkill
from resumes.models import Skill

class JobSkillSerializer(serializers.ModelSerializer):
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source='skill', write_only=True
    )
    name = serializers.CharField(source='skill.name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = JobSkill
        fields = ['id', 'skill_id', 'name', 'category', 'is_required']

class JobSerializer(serializers.ModelSerializer):
    skills = JobSkillSerializer(source='job_skills', many=True, required=False)

    class Meta:
        model = Job
        fields = ['id', 'title', 'company', 'description', 'location', 'job_url', 'salary', 'created_at', 'updated_at', 'skills']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        skills_data = validated_data.pop('job_skills', [])
        job = Job.objects.create(**validated_data)
        
        # Create JobSkills
        for skill_data in skills_data:
            JobSkill.objects.create(
                job=job,
                skill=skill_data['skill'],
                is_required=skill_data.get('is_required', False)
            )
            
        return job

    def update(self, instance, validated_data):
        skills_data = validated_data.pop('job_skills', None)
        
        # Update job fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If skills are provided, we update them. A common pattern is to clear and recreate.
        if skills_data is not None:
            instance.job_skills.all().delete()
            for skill_data in skills_data:
                JobSkill.objects.create(
                    job=instance,
                    skill=skill_data['skill'],
                    is_required=skill_data.get('is_required', False)
                )
                
        return instance
