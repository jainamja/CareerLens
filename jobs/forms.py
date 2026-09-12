from django import forms
from .models import Job
from resumes.models import Skill

class JobForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        help_text="Select required skills for this job."
    )
    optional_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        help_text="Select optional/nice-to-have skills for this job."
    )

    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'job_url', 'salary', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Developer'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Acme Corp'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Remote, San Francisco, CA'}),
            'job_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. $100,000 - $120,000'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Job description details...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['required_skills'] = self.instance.job_skills.filter(is_required=True).values_list('skill', flat=True)
            self.initial['optional_skills'] = self.instance.job_skills.filter(is_required=False).values_list('skill', flat=True)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        company = cleaned_data.get('company')
        description = cleaned_data.get('description')

        if title and not title.strip():
            self.add_error('title', 'This field cannot be blank or whitespace only.')
        if company and not company.strip():
            self.add_error('company', 'This field cannot be blank or whitespace only.')
        if description and not description.strip():
            self.add_error('description', 'This field cannot be blank or whitespace only.')
            
        required_skills = cleaned_data.get('required_skills', [])
        optional_skills = cleaned_data.get('optional_skills', [])
        
        # Check for overlap between required and optional skills
        overlap = set(required_skills).intersection(set(optional_skills))
        if overlap:
            self.add_error('optional_skills', 'A skill cannot be both required and optional.')
            
        return cleaned_data
