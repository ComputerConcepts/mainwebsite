#!/usr/bin/env python
"""
Test script to create a form with a signature field
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.contrib.auth.models import User
from pages.models import Employee, OnboardingForm, OnboardingFormField, ProspectiveEmployee, OnboardingInvitation
from pages.onboarding_emails import OnboardingEmailService
from datetime import timedelta
import uuid

def create_signature_test_form():
    """Create a test form with a signature field"""
    print("🧪 Creating onboarding form with signature field...")
    
    # Get HR user
    try:
        user = User.objects.get(username='hr_test')
        print(f"✓ Using HR user: {user.username}")
    except User.DoesNotExist:
        print("✗ HR test user not found. Creating one...")
        user = User.objects.create_user(
            username='hr_test',
            email='hr@test.com',
            password='testpass123'
        )
        print(f"✓ Created HR user: {user.username}")
    
    # Create form with signature field
    form = OnboardingForm.objects.create(
        title='Signature Test Form',
        description='Testing digital signature functionality',
        created_by=user,
        pin_expiry_hours=24,
        allow_multiple_submissions=False,
        send_confirmation_email=True
    )
    print(f"✓ Created form: {form.title}")
    
    # Create fields including signature
    fields_data = [
        {
            'field_type': 'text',
            'field_name': 'full_name',
            'field_label': 'Full Name',
            'placeholder': 'Enter your full name',
            'is_required': True,
            'order': 0
        },
        {
            'field_type': 'email',
            'field_name': 'email',
            'field_label': 'Email Address',
            'placeholder': 'your.email@company.com',
            'is_required': True,
            'order': 1
        },
        {
            'field_type': 'signature',
            'field_name': 'digital_signature',
            'field_label': 'Digital Signature',
            'help_text': 'Please draw your signature in the box above',
            'is_required': True,
            'order': 2
        }
    ]
    
    for field_data in fields_data:
        field = OnboardingFormField.objects.create(
            onboarding_form=form,
            **field_data
        )
        print(f"✓ Created field: {field.field_label} ({field.field_type})")
    
    # Create a test prospective employee (or get existing)
    prospect, created = ProspectiveEmployee.objects.get_or_create(
        email='test.signature@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'Signature',
            'current_pin': '123456',
            'pin_expiry': form.created_at + timedelta(hours=24),
            'created_by': user
        }
    )
    if created:
        print(f"✓ Created test prospect: {prospect.email}")
    else:
        print(f"✓ Using existing prospect: {prospect.email}")
    
    # Create invitation
    invitation = OnboardingInvitation.objects.create(
        onboarding_form=form,
        prospective_employee=prospect,
        sent_by=user,
        custom_message='Please complete your onboarding form with digital signature.'
    )
    print(f"✓ Created invitation: {invitation.id}")
    
    print(f"\n🎉 Signature test form created successfully!")
    print(f"📋 Form ID: {form.id}")
    print(f"👤 Prospect Email: {prospect.email}")
    print(f"🔑 PIN Code: {prospect.current_pin}")
    print(f"🔗 Invitation ID: {invitation.id}")
    
    print(f"\n📍 Test URLs:")
    print(f"  Login: http://127.0.0.1:8000/onboarding/login/")
    print(f"  Form: http://127.0.0.1:8000/onboarding/form/{invitation.id}/")
    
    print(f"\n📝 Test Instructions:")
    print(f"1. Go to the login URL")
    print(f"2. Enter email: {prospect.email}")
    print(f"3. Enter PIN: {prospect.current_pin}")
    print(f"4. Fill out the form and test the signature field")
    print(f"5. Submit the form to test signature processing")
    
    return True

if __name__ == '__main__':
    try:
        create_signature_test_form()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()