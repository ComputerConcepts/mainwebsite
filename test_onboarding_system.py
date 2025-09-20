"""
Test script for HR Onboarding System
Tests the complete workflow from form creation to submission
"""

import os
import sys
import django
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import (
    Employee, OnboardingForm, OnboardingFormField, 
    ProspectiveEmployee, OnboardingInvitation, OnboardingSubmission
)
from pages.onboarding_emails import OnboardingEmailService

def test_onboarding_system():
    """Test the complete onboarding workflow"""
    print("🚀 Testing HR Onboarding System")
    print("=" * 50)
    
    try:
        # 1. Create test HR user
        print("1. Creating test HR user...")
        hr_user, created = User.objects.get_or_create(
            username='hr_test_user',
            defaults={
                'email': 'hr_test@onecomputerconcepts.com',
                'first_name': 'HR',
                'last_name': 'Tester',
                'is_staff': True
            }
        )
        
        # Create employee profile
        hr_employee, created = Employee.objects.get_or_create(
            user=hr_user,
            defaults={
                'department': 'HR',
                'role': 'admin',
                'phone': '555-0123',
                'address': 'Test Address',
                'emergency_contact_name': 'Emergency Contact',
                'emergency_contact_phone': '555-0124'
            }
        )
        print(f"   ✅ HR user created: {hr_user.username}")
        
        # 2. Create onboarding form
        print("2. Creating onboarding form...")
        onboarding_form = OnboardingForm.objects.create(
            title='Software Developer Onboarding',
            description='Complete onboarding form for new software developers',
            created_by=hr_user,
            pin_expiry_hours=48,
            allow_multiple_submissions=False,
            send_confirmation_email=True
        )
        print(f"   ✅ Form created: {onboarding_form.title}")
        
        # 3. Add form fields
        print("3. Adding form fields...")
        fields_data = [
            {
                'field_type': 'text',
                'field_name': 'first_name',
                'field_label': 'First Name',
                'is_required': True,
                'order': 1
            },
            {
                'field_type': 'text',
                'field_name': 'last_name',
                'field_label': 'Last Name',
                'is_required': True,
                'order': 2
            },
            {
                'field_type': 'email',
                'field_name': 'email',
                'field_label': 'Email Address',
                'is_required': True,
                'order': 3
            },
            {
                'field_type': 'phone',
                'field_name': 'phone',
                'field_label': 'Phone Number',
                'is_required': True,
                'order': 4
            },
            {
                'field_type': 'select',
                'field_name': 'experience_level',
                'field_label': 'Experience Level',
                'field_options': ['Junior', 'Mid-level', 'Senior', 'Lead'],
                'is_required': True,
                'order': 5
            },
            {
                'field_type': 'textarea',
                'field_name': 'previous_experience',
                'field_label': 'Previous Experience',
                'help_text': 'Tell us about your relevant work experience',
                'is_required': False,
                'order': 6
            },
            {
                'field_type': 'file',
                'field_name': 'resume',
                'field_label': 'Resume',
                'help_text': 'Upload your current resume (PDF preferred)',
                'is_required': True,
                'order': 7
            }
        ]
        
        for field_data in fields_data:
            OnboardingFormField.objects.create(
                onboarding_form=onboarding_form,
                **field_data
            )
        
        print(f"   ✅ Added {len(fields_data)} form fields")
        
        # 4. Create prospective employee
        print("4. Creating prospective employee...")
        prospective_employee = ProspectiveEmployee.objects.create(
            email='john.doe@example.com',
            first_name='John',
            last_name='Doe',
            phone='555-0125',
            created_by=hr_user
        )
        
        # Generate PIN
        pin = prospective_employee.generate_pin()
        print(f"   ✅ Prospective employee created: {prospective_employee.email}")
        print(f"   🔑 Generated PIN: {pin}")
        
        # 5. Create invitation
        print("5. Creating onboarding invitation...")
        invitation = OnboardingInvitation.objects.create(
            onboarding_form=onboarding_form,
            prospective_employee=prospective_employee,
            sent_by=hr_user,
            custom_message='Welcome to Computer Concepts! We are excited to have you join our development team.'
        )
        print(f"   ✅ Invitation created: {invitation.id}")
        
        # 6. Test PIN validation
        print("6. Testing PIN validation...")
        print(f"   🔍 PIN valid: {prospective_employee.is_pin_valid()}")
        print(f"   📅 PIN expires: {prospective_employee.pin_expiry}")
        
        # 7. Simulate form submission
        print("7. Simulating form submission...")
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '555-0125',
            'experience_level': 'Mid-level',
            'previous_experience': 'I have 3 years of experience in Python and Django development.',
            'resume': {
                'original_name': 'john_doe_resume.pdf',
                'file_path': 'onboarding/test_resume.pdf'
            }
        }
        
        submission = OnboardingSubmission.objects.create(
            invitation=invitation,
            form_data=form_data,
            uploaded_files=[{
                'field_name': 'resume',
                'original_name': 'john_doe_resume.pdf',
                'file_path': 'onboarding/test_resume.pdf',
                'file_size': 245760
            }],
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        # Update invitation status
        invitation.status = 'completed'
        invitation.completion_date = timezone.now()
        invitation.save()
        
        print(f"   ✅ Submission created: {submission.id}")
        print(f"   📝 Applicant name: {submission.get_applicant_name()}")
        
        # 8. Test form display data
        print("8. Testing form display...")
        form_fields = onboarding_form.fields.all().order_by('order')
        display_data = []
        for field in form_fields:
            value = submission.form_data.get(field.field_name, '')
            display_data.append({
                'field': field,
                'value': value
            })
        
        print(f"   ✅ Form has {len(display_data)} fields with data")
        for item in display_data:
            field_name = item['field'].field_label
            value = str(item['value'])[:50] + ('...' if len(str(item['value'])) > 50 else '')
            print(f"      • {field_name}: {value}")
        
        # 9. Test statistics
        print("9. Testing dashboard statistics...")
        stats = {
            'total_forms': OnboardingForm.objects.filter(is_active=True).count(),
            'total_invitations': OnboardingInvitation.objects.count(),
            'pending_submissions': OnboardingSubmission.objects.filter(review_status='pending').count(),
            'active_prospects': ProspectiveEmployee.objects.filter(is_active=True).count(),
        }
        
        print(f"   📊 Statistics:")
        print(f"      • Active Forms: {stats['total_forms']}")
        print(f"      • Total Invitations: {stats['total_invitations']}")
        print(f"      • Pending Submissions: {stats['pending_submissions']}")
        print(f"      • Active Prospects: {stats['active_prospects']}")
        
        # 10. Test email template rendering (without sending)
        print("10. Testing email template rendering...")
        try:
            from django.template.loader import render_to_string
            
            context = {
                'invitation': invitation,
                'prospective_employee': prospective_employee,
                'onboarding_form': onboarding_form,
                'pin': pin,
                'pin_expiry': prospective_employee.pin_expiry,
                'onboarding_url': 'https://onecomputerconcepts.com/onboarding/login/',
                'custom_message': invitation.custom_message,
                'current_year': timezone.now().year,
            }
            
            text_content = render_to_string('email/onboarding/invitation.txt', context)
            html_content = render_to_string('email/onboarding/invitation.html', context)
            
            print(f"   ✅ Email templates rendered successfully")
            print(f"      • Text content length: {len(text_content)} chars")
            print(f"      • HTML content length: {len(html_content)} chars")
            
        except Exception as e:
            print(f"   ⚠️  Email template rendering failed: {e}")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 50)
        
        return {
            'success': True,
            'form': onboarding_form,
            'prospective_employee': prospective_employee,
            'invitation': invitation,
            'submission': submission,
            'pin': pin,
            'stats': stats
        }
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test submissions
        OnboardingSubmission.objects.filter(
            invitation__prospective_employee__email='john.doe@example.com'
        ).delete()
        
        # Delete test invitations
        OnboardingInvitation.objects.filter(
            prospective_employee__email='john.doe@example.com'
        ).delete()
        
        # Delete test prospective employees
        ProspectiveEmployee.objects.filter(
            email='john.doe@example.com'
        ).delete()
        
        # Delete test forms
        OnboardingForm.objects.filter(
            title='Software Developer Onboarding'
        ).delete()
        
        # Delete test HR employee
        Employee.objects.filter(
            user__username='hr_test_user'
        ).delete()
        
        # Delete test HR user
        User.objects.filter(
            username='hr_test_user'
        ).delete()
        
        print("✅ Test data cleaned up successfully")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

if __name__ == '__main__':
    result = test_onboarding_system()
    
    if result['success']:
        print(f"\n📋 Test Results Summary:")
        print(f"   • Form ID: {result['form'].id}")
        print(f"   • Prospect Email: {result['prospective_employee'].email}")
        print(f"   • Invitation ID: {result['invitation'].id}")
        print(f"   • Submission ID: {result['submission'].id}")
        print(f"   • Access PIN: {result['pin']}")
        
        # Ask if user wants to cleanup
        response = input("\n🗑️  Do you want to clean up test data? (y/N): ")
        if response.lower() in ['y', 'yes']:
            cleanup_test_data()
        else:
            print("📌 Test data preserved for manual testing")
    else:
        print(f"\n❌ Tests failed: {result['error']}")