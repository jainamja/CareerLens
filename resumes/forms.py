from django import forms
from .models import Resume

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'})
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            max_size_mb = 5
            if file.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"File size must not exceed {max_size_mb} MB.")
            
            if file.content_type != 'application/pdf' and not file.name.endswith('.pdf'):
                raise forms.ValidationError("Only PDF files are allowed.")
        return file
