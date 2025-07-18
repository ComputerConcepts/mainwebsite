from django import forms
from django.contrib.auth.models import User
from .models import Events, JobPosting, Employee

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


class EmployeeProfileForm(forms.ModelForm):
    """Form for employee profile editing with restrictions"""
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        disabled=True  # Always disabled for non-superusers
    )
    
    class Meta:
        model = Employee
        fields = ['phone', 'department', 'position', 'address', 'emergency_contact', 'emergency_phone']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title/Position'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Name'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for User fields
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        
        # If not superuser, disable restricted fields
        if user and not user.is_superuser:
            self.fields['email'].disabled = True
            self.fields['department'].disabled = True
            self.fields['position'].disabled = True
            
            # Add help text to show restrictions
            self.fields['email'].help_text = "Only administrators can modify email addresses."
            self.fields['department'].help_text = "Only administrators can modify department."
            self.fields['position'].help_text = "Only administrators can modify job titles."
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        # Save User fields (only if user is superuser)
        if hasattr(self, 'user') and self.user.is_superuser:
            user = employee.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if commit:
                user.save()
        
        if commit:
            employee.save()
        return employee