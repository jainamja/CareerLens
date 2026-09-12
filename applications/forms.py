from django import forms
from .models import Application
from jobs.models import Job

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['job', 'status', 'applied_date', 'notes']
        widgets = {
            'job': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'applied_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['job'].queryset = Job.objects.filter(user=user)
            self.fields['job'].label_from_instance = lambda obj: f"{obj.title} — {obj.company}"
