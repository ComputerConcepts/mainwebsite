#!/usr/bin/env python
"""
Test script to verify the onboarding form builder functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from pages.models import Employee, OnboardingForm, OnboardingFormField
import json

class FormBuilderTest:
    def __init__(self):
        self.client = Client()
        self.setup_test_user()
    
    def setup_test_user(self):
        """Create a test HR user"""
        try:
            # Create a test user
            self.user = User.objects.create_user(
                username='hr_test',
                email='hr@test.com',
                password='testpass123'
            )
            
            # Create employee record for HR
            self.employee = Employee.objects.create(
                user=self.user,
                employee_id='HR001',
                department='HR',
                position='HR Manager',
                role='admin',  # Added admin role
                is_hr=True
            )
            
            print(f"✓ Created test HR user: {self.user.username}")
            
        except Exception as e:
            print(f"✗ Error creating test user: {e}")
            # Try to get existing user
            try:
                self.user = User.objects.get(username='hr_test')
                self.employee = Employee.objects.get(user=self.user)
                # Update role to ensure HR access
                self.employee.department = 'HR'
                self.employee.role = 'admin'
                self.employee.is_hr = True
                self.employee.save()
                print(f"✓ Using existing HR user: {self.user.username}")
            except:
                print("✗ Could not create or find test user")
                return False
        return True
    
    def test_form_creation_endpoint(self):
        """Test that the form creation endpoint works"""
        print("\n🧪 Testing form creation endpoint...")
        
        # Login as HR user
        login_success = self.client.login(username='hr_test', password='testpass123')
        if not login_success:
            print("✗ Could not login as HR user")
            return False
        
        print("✓ Successfully logged in as HR user")
        
        # Test GET request to form creation page
        try:
            response = self.client.get('/employee/hr/onboarding/forms/create/')
            print(f"✓ GET /employee/hr/onboarding/forms/create/ returned status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Form creation page loads successfully")
                return True
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error accessing form creation page: {e}")
            return False
    
    def test_form_submission(self):
        """Test creating a form via POST"""
        print("\n🧪 Testing form submission...")
        
        # Login first
        self.client.login(username='hr_test', password='testpass123')
        
        # Test form data
        form_data = {
            'title': 'Test Onboarding Form',
            'description': 'This is a test form created via API',
            'pin_expiry_hours': 48,
            'allow_multiple_submissions': False,
            'send_confirmation_email': True,
            'fields': [
                {
                    'field_type': 'text',
                    'field_name': 'full_name',
                    'field_label': 'Full Name',
                    'placeholder': 'Enter your full name',
                    'help_text': '',
                    'is_required': True,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': [],
                    'order': 0
                },
                {
                    'field_type': 'email',
                    'field_name': 'email_address',
                    'field_label': 'Email Address',
                    'placeholder': 'Enter your email',
                    'help_text': '',
                    'is_required': True,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': [],
                    'order': 1
                }
            ]
        }
        
        try:
            response = self.client.post(
                '/employee/hr/onboarding/forms/create/',
                data=json.dumps(form_data),
                content_type='application/json'
            )
            
            print(f"✓ POST request sent, status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    print("✓ Form created successfully!")
                    print(f"  Form ID: {response_data.get('form_id')}")
                    return True
                else:
                    print(f"✗ Form creation failed: {response_data.get('message')}")
                    return False
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
                if hasattr(response, 'content'):
                    print(f"Response: {response.content.decode()}")
                return False
                
        except Exception as e:
            print(f"✗ Error submitting form: {e}")
            return False
    
    def test_field_addition(self):
        """Test that multiple fields can be added"""
        print("\n🧪 Testing multiple field addition...")
        
        # Login first
        self.client.login(username='hr_test', password='testpass123')
        
        # Create a form with 5 different field types
        form_data = {
            'title': 'Multi-Field Test Form',
            'description': 'Testing multiple field types',
            'pin_expiry_hours': 24,
            'allow_multiple_submissions': False,
            'send_confirmation_email': True,
            'fields': [
                {
                    'field_type': 'text',
                    'field_name': 'first_name',
                    'field_label': 'First Name',
                    'placeholder': 'Enter first name',
                    'help_text': '',
                    'is_required': True,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': [],
                    'order': 0
                },
                {
                    'field_type': 'text',
                    'field_name': 'last_name',
                    'field_label': 'Last Name',
                    'placeholder': 'Enter last name',
                    'help_text': '',
                    'is_required': True,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': [],
                    'order': 1
                },
                {
                    'field_type': 'email',
                    'field_name': 'email',
                    'field_label': 'Email Address',
                    'placeholder': 'your.email@company.com',
                    'help_text': 'We will use this for communication',
                    'is_required': True,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': [],
                    'order': 2
                },
                {
                    'field_type': 'phone',
                    'field_name': 'phone',
                    'field_label': 'Phone Number',
                    'placeholder': '+1 (555) 123-4567',
                    'help_text': 'Include country code',
                    'is_required': False,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': [],
                    'order': 3
                },
                {
                    'field_type': 'select',
                    'field_name': 'department',
                    'field_label': 'Department',
                    'placeholder': '',
                    'help_text': 'Select your intended department',
                    'is_required': True,
                    'min_length': None,
                    'max_length': None,
                    'validation_regex': '',
                    'field_options': ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance'],
                    'order': 4
                }
            ]
        }
        
        try:
            response = self.client.post(
                '/employee/hr/onboarding/forms/create/',
                data=json.dumps(form_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    form_id = response_data.get('form_id')
                    print(f"✓ Multi-field form created successfully! ID: {form_id}")
                    
                    # Verify fields were created
                    form = OnboardingForm.objects.get(id=form_id)
                    fields = OnboardingFormField.objects.filter(onboarding_form=form).order_by('order')
                    
                    print(f"✓ Created {fields.count()} fields:")
                    for field in fields:
                        print(f"  - {field.field_label} ({field.field_type})")
                    
                    if fields.count() == 5:
                        print("✓ All 5 fields created successfully!")
                        return True
                    else:
                        print(f"✗ Expected 5 fields, got {fields.count()}")
                        return False
                else:
                    print(f"✗ Multi-field form creation failed: {response_data.get('message')}")
                    return False
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error creating multi-field form: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Form Builder Tests...")
        print("=" * 50)
        
        tests = [
            self.test_form_creation_endpoint,
            self.test_form_submission,
            self.test_field_addition
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                    print("✅ PASSED")
                else:
                    failed += 1
                    print("❌ FAILED")
            except Exception as e:
                failed += 1
                print(f"❌ FAILED with exception: {e}")
            
            print("-" * 30)
        
        print(f"\n📊 Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed! The form builder is working correctly.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")

if __name__ == '__main__':
    tester = FormBuilderTest()
    tester.run_all_tests()