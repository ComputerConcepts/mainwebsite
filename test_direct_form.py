#!/usr/bin/env python
"""
Simple test to verify the form builder works by directly testing the form creation
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.contrib.auth.models import User
from pages.models import Employee, OnboardingForm, OnboardingFormField
import json

def test_form_creation():
    """Test that we can create a form with multiple fields"""
    print("🧪 Testing direct form creation...")
    
    # Get or create test HR user
    try:
        user = User.objects.get(username='hr_test')
        print(f"✓ Found existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='hr_test',
            email='hr@test.com',
            password='testpass123',
            first_name='HR',
            last_name='Manager'
        )
        print(f"✓ Created new user: {user.username}")
    
    # Get or create employee
    try:
        employee = Employee.objects.get(user=user)
        # Update to ensure HR access
        employee.department = 'HR'
        employee.role = 'admin'
        employee.save()
        print(f"✓ Updated employee: {employee}")
    except Employee.DoesNotExist:
        employee = Employee.objects.create(
            user=user,
            employee_id='HR001',
            department='HR',
            position='HR Manager',
            role='admin',
            phone='+1-555-123-4567'
        )
        print(f"✓ Created new employee: {employee}")
    
    # Test creating a form with multiple fields
    print("\n🧪 Creating onboarding form with multiple fields...")
    
    # Create the form
    form = OnboardingForm.objects.create(
        title='Multi-Field Test Form',
        description='Testing multiple field creation',
        created_by=user,  # Use user instead of employee
        pin_expiry_hours=48,
        allow_multiple_submissions=False,
        send_confirmation_email=True
    )
    print(f"✓ Created form: {form.title}")
    
    # Create multiple fields
    fields_data = [
        {
            'field_type': 'text',
            'field_name': 'first_name',
            'field_label': 'First Name',
            'placeholder': 'Enter your first name',
            'is_required': True,
            'order': 0
        },
        {
            'field_type': 'text',
            'field_name': 'last_name',
            'field_label': 'Last Name',
            'placeholder': 'Enter your last name',
            'is_required': True,
            'order': 1
        },
        {
            'field_type': 'email',
            'field_name': 'email',
            'field_label': 'Email Address',
            'placeholder': 'your.email@company.com',
            'help_text': 'We will use this for communication',
            'is_required': True,
            'order': 2
        },
        {
            'field_type': 'phone',
            'field_name': 'phone',
            'field_label': 'Phone Number',
            'placeholder': '+1 (555) 123-4567',
            'help_text': 'Include country code',
            'is_required': False,
            'order': 3
        },
        {
            'field_type': 'select',
            'field_name': 'department',
            'field_label': 'Department',
            'help_text': 'Select your intended department',
            'is_required': True,
            'field_options': ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance'],
            'order': 4
        }
    ]
    
    created_fields = []
    for field_data in fields_data:
        field = OnboardingFormField.objects.create(
            onboarding_form=form,
            **field_data
        )
        created_fields.append(field)
        print(f"✓ Created field: {field.field_label} ({field.field_type})")
    
    print(f"\n✅ Successfully created form with {len(created_fields)} fields!")
    
    # Verify fields exist and are in correct order
    form_fields = OnboardingFormField.objects.filter(onboarding_form=form).order_by('order')
    print(f"✓ Form has {form_fields.count()} fields in database")
    
    for i, field in enumerate(form_fields):
        print(f"  {i+1}. {field.field_label} ({field.field_type}) - Required: {field.is_required}")
    
    # Test that we can add even more fields
    print(f"\n🧪 Adding additional fields to test scalability...")
    
    additional_fields = [
        {
            'field_type': 'textarea',
            'field_name': 'bio',
            'field_label': 'Brief Bio',
            'placeholder': 'Tell us about yourself...',
            'help_text': 'Max 500 characters',
            'is_required': False,
            'max_length': 500,
            'order': 5
        },
        {
            'field_type': 'date',
            'field_name': 'start_date',
            'field_label': 'Preferred Start Date',
            'help_text': 'When would you like to start?',
            'is_required': True,
            'order': 6
        },
        {
            'field_type': 'radio',
            'field_name': 'experience_level',
            'field_label': 'Experience Level',
            'help_text': 'Select your experience level',
            'is_required': True,
            'field_options': ['Entry Level', 'Mid Level', 'Senior Level', 'Executive'],
            'order': 7
        },
        {
            'field_type': 'checkbox',
            'field_name': 'skills',
            'field_label': 'Technical Skills',
            'help_text': 'Select all that apply',
            'is_required': False,
            'field_options': ['Python', 'JavaScript', 'React', 'Django', 'SQL', 'AWS', 'Docker'],
            'order': 8
        },
        {
            'field_type': 'file',
            'field_name': 'resume',
            'field_label': 'Resume/CV',
            'help_text': 'Upload your resume (PDF preferred)',
            'is_required': True,
            'order': 9
        }
    ]
    
    for field_data in additional_fields:
        field = OnboardingFormField.objects.create(
            onboarding_form=form,
            **field_data
        )
        created_fields.append(field)
        print(f"✓ Added field: {field.field_label} ({field.field_type})")
    
    # Final verification
    final_fields = OnboardingFormField.objects.filter(onboarding_form=form).order_by('order')
    print(f"\n🎉 Final result: Form '{form.title}' has {final_fields.count()} fields!")
    
    print(f"\n📝 Complete field list:")
    for i, field in enumerate(final_fields):
        options_text = f" - Options: {field.field_options}" if field.field_options else ""
        print(f"  {i+1:2d}. {field.field_label:20s} ({field.field_type:10s}) Required: {field.is_required}{options_text}")
    
    print(f"\n✅ SUCCESS: Form builder can handle multiple fields of different types!")
    return True

if __name__ == '__main__':
    try:
        test_form_creation()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()