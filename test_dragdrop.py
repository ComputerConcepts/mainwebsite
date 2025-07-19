#!/usr/bin/env python
"""
Test script to verify drag and drop functionality
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from pages.models import Employee, FileDocument, FileFolder
import json

def test_drag_drop_functionality():
    """Test the drag and drop file moving functionality"""
    print("=== DRAG AND DROP TEST ===")
    
    # Create a test client
    client = Client()
    
    # Get the test user
    try:
        user = User.objects.get(username='aayushgauba')
        employee = Employee.objects.get(user=user)
        print(f"Found user: {user.username} - {user.email}")
        print(f"Employee active: {employee.is_active}, verified: {employee.is_email_verified}")
    except (User.DoesNotExist, Employee.DoesNotExist) as e:
        print(f"Error finding user: {e}")
        return False
    
    # Login the user
    login_data = {
        'email': 'aayushgauba@onecomputerconcepts.com',
        'password': 'testpass123'  # Updated password
    }
    
    response = client.post('/employee/login/', login_data)
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        print("Login form returned, checking for errors...")
        # Check if login was successful by looking for redirect
        if 'employee_dashboard' in str(response.content):
            print("Login appears to be successful")
        else:
            print("Login failed - check password")
            return False
    elif response.status_code == 302:
        print("Login successful - redirected")
    else:
        print(f"Unexpected login response: {response.status_code}")
        return False
    
    # Check authentication
    response = client.get('/employee/files/')
    print(f"File manager access status: {response.status_code}")
    
    if response.status_code == 302:
        print("Still redirected to login - authentication failed")
        return False
    elif response.status_code == 200:
        print("Successfully accessed file manager")
    else:
        print(f"Unexpected file manager response: {response.status_code}")
        return False
    
    # Create test folder and file if they don't exist
    try:
        test_folder = FileFolder.objects.filter(name='Test Folder', created_by=employee).first()
        if not test_folder:
            test_folder = FileFolder.objects.create(
                name='Test Folder',
                created_by=employee
            )
        print(f"Test folder: {test_folder.name} (ID: {test_folder.id})")
        
        test_file = FileDocument.objects.filter(name='test.txt', uploaded_by=employee).first()
        if not test_file:
            # Create a dummy file for testing
            test_file = FileDocument.objects.create(
                name='test.txt',
                uploaded_by=employee,
                file_size=100,
                mime_type='text/plain'
            )
        print(f"Test file: {test_file.name} (ID: {test_file.id})")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        return False
    
    # Test the move_file endpoint
    move_data = {
        'file_id': str(test_file.id),
        'target_folder_id': str(test_folder.id)
    }
    
    response = client.post('/employee/files/move/', 
                          json.dumps(move_data), 
                          content_type='application/json')
    
    print(f"Move file response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            response_data = json.loads(response.content)
            print(f"Move response: {response_data}")
            
            if response_data.get('success'):
                print("✅ Drag and drop functionality is working!")
                return True
            else:
                print(f"❌ Move failed: {response_data.get('message')}")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.content}")
            return False
    else:
        print(f"❌ HTTP error: {response.status_code}")
        print(f"Response content: {response.content}")
        return False

if __name__ == '__main__':
    success = test_drag_drop_functionality()
    if success:
        print("\n🎉 Test passed! Drag and drop functionality is working correctly.")
    else:
        print("\n❌ Test failed! There are issues with the drag and drop functionality.")
