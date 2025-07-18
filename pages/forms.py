from django import forms
from .models import Events, JobPosting

class EventImageForm(forms.ModelForm):
    class Meta:
        model = Events
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'required': 'true'})
        }

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title', 'department', 'location', 'job_type', 'description',
            'requirements', 'responsibilities', 'benefits', 'salary_range', 'experience_level',
            'application_deadline', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Senior Software Engineer'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Engineering'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York or Remote'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'maxlength': 5000, 'placeholder': 'Enter a detailed job description...'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'maxlength': 3000, 'placeholder': 'List required skills, qualifications, and experience...'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'maxlength': 3000, 'placeholder': 'List key responsibilities for this role...'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe benefits, perks, and incentives...'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., $80,000 - $100,000'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'application_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }