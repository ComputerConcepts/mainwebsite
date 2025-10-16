#!/usr/bin/env python
"""
Test script to verify employee login and file manager access
"""
import requests
import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from pages.models import Employee

def test_employee_login():
    """Test employee login functionality"""
    print("Testing employee login functionality...")
    
    # Create a test client
    client = Client()
    
    # Test data
    test_email = 'testemployee@onecomputerconcepts.com'
    test_password = 'testpass123'
    
    # Check if user exists
    try:
        user = User.objects.get(email=test_email)
        employee = Employee.objects.get(user=user)
        print(f"✓ Test user exists: {user.username}")
        print(f"✓ Employee profile exists: {employee.employee_id}")
        print(f"✓ Employee is active: {employee.is_active}")
        print(f"✓ Email is verified: {employee.is_email_verified}")
    except (User.DoesNotExist, Employee.DoesNotExist):
        print("✗ Test user or employee profile not found")
        return False
    
    # Test login
    print("\nTesting login...")
    response = client.post('/employee/login/', {
        'email': test_email,
        'password': test_password
    })
    
    print(f"Login response status: {response.status_code}")
    print(f"Redirect URL: {response.get('Location', 'No redirect')}")
    
    # Check if login was successful (redirect to dashboard)
    if response.status_code == 302 and '/employee/dashboard/' in response.get('Location', ''):
        print("✓ Login successful!")
        
        # Test file manager access
        print("\nTesting file manager access...")
        response = client.get('/employee/files/')
        print(f"File manager response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ File manager accessible!")
            print("✓ All tests passed! File manager should work.")
            return True
        else:
            print(f"✗ File manager not accessible. Status: {response.status_code}")
            if response.status_code == 302:
                print(f"Redirected to: {response.get('Location')}")
    else:
        print("✗ Login failed")
        print(f"Response content: {response.content.decode()[:500]}...")
    
    return False

if __name__ == '__main__':
    print("=== Employee Login and File Manager Test ===\n")
    success = test_employee_login()
    
    if success:
        print("\n=== CONCLUSION ===")
        print("✓ Login system is working correctly")
        print("✓ File manager is accessible to authenticated users")
        print("✓ The enhanced JavaScript in file_manager.html should now work")
        print("\nYou can now:")
        print("1. Log in with: testemployee@onecomputerconcepts.com / testpass123")
        print("2. Navigate to File Manager")
        print("3. Test the drag-and-drop upload functionality")
    else:
        print("\n=== ISSUES FOUND ===")
        print("✗ There are still authentication or access issues")
        print("Please check the Django logs for more details")