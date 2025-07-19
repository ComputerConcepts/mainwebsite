from django import forms
from django.contrib.auth.models import User
from .models import Events, JobPosting, Employee, FileFolder, FileDocument, Board

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


class FolderForm(forms.ModelForm):
    """Form for creating and editing folders"""
    
    class Meta:
        model = FileFolder
        fields = ['name', 'parent', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Folder name'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter parent folders to show user's folders and shared folders
        if user:
            try:
                employee = Employee.objects.get(user=user)
                from django.db.models import Q
                self.fields['parent'].queryset = FileFolder.objects.filter(
                    Q(created_by=employee) | Q(shared_with=employee)
                ).distinct()
            except Employee.DoesNotExist:
                self.fields['parent'].queryset = FileFolder.objects.none()


class FileUploadForm(forms.Form):
    """Form for uploading files - files handled via JavaScript/HTML"""
    
    folder = forms.ModelChoiceField(
        queryset=FileFolder.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'File description'}),
        required=False
    )
    tags = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags separated by commas'}),
        required=False
    )
    is_public = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter folders to show user's folders and shared folders
        if user:
            try:
                employee = Employee.objects.get(user=user)
                from django.db.models import Q
                self.fields['folder'].queryset = FileFolder.objects.filter(
                    Q(created_by=employee) | Q(shared_with=employee)
                ).distinct()
            except Employee.DoesNotExist:
                self.fields['folder'].queryset = FileFolder.objects.none()


class FileShareForm(forms.Form):
    """Form for sharing files with other users via email"""
    
    email = forms.EmailField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'id': 'email-search',
            'autocomplete': 'off'
        }),
        required=True,
        help_text='Enter the email address of the person you want to share with'
    )
    permission = forms.ChoiceField(
        choices=[
            ('view', 'View Only'),
            ('edit', 'Edit'),
            ('full', 'Full Access'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='view'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional message'}),
        required=False
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if user exists
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(email=email)
                # Check if employee profile exists
                Employee.objects.get(user=user)
                return email
            except (User.DoesNotExist, Employee.DoesNotExist):
                raise forms.ValidationError(
                    'No employee found with this email address. Please check the email or contact the administrator.'
                )
        return email


class FileSearchForm(forms.Form):
    """Form for searching files"""
    
    query = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search files and folders...',
            'autocomplete': 'off'
        }),
        required=False
    )
    file_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('document', 'Documents'),
            ('image', 'Images'),
            ('video', 'Videos'),
            ('audio', 'Audio'),
            ('pdf', 'PDFs'),
            ('spreadsheet', 'Spreadsheets'),
            ('presentation', 'Presentations'),
            ('archive', 'Archives'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    date_range = forms.ChoiceField(
        choices=[
            ('', 'Any Time'),
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('year', 'This Year'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    tags = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags separated by commas'
        }),
        required=False
    )


class BoardShareForm(forms.Form):
    """Form for sharing boards with other users via email"""
    
    email = forms.EmailField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'id': 'email-search',
            'autocomplete': 'off'
        }),
        required=True,
        help_text='Enter the email address of the person you want to share with'
    )
    permission = forms.ChoiceField(
        choices=[
            ('view', 'View Only'),
            ('edit', 'Edit'),
            ('admin', 'Admin'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='view'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional message'}),
        required=False
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if user exists
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(email=email)
                # Check if employee profile exists
                Employee.objects.get(user=user)
                return email
            except (User.DoesNotExist, Employee.DoesNotExist):
                raise forms.ValidationError(
                    'No employee found with this email address. Please check the email or contact the administrator.'
                )
        return email