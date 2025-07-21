#!/usr/bin/env python
"""
Test script to check if the file view works for the specific file ID
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import FileDocument, Employee
from django.contrib.auth.models import User

def test_file_view():
    """Test the specific file ID from the URL"""
    file_id = "480446df-19f5-4bbc-b63e-7387dd11c37f"
    
    print(f"Testing file ID: {file_id}")
    
    # Check if file exists
    try:
        file_doc = FileDocument.objects.get(id=file_id)
        print(f"✅ File found: {file_doc.name}")
        print(f"   Uploaded by: {file_doc.uploaded_by.get_full_name()}")
        print(f"   File type: {file_doc.file_type}")
        print(f"   Size: {file_doc.get_file_size_display()}")
        print(f"   Created: {file_doc.created_at}")
        
        # Check if file exists on disk
        file_path = file_doc.get_file_path()
        if file_path and os.path.exists(file_path):
            print(f"✅ File exists on disk: {file_path}")
        else:
            print(f"❌ File missing on disk: {file_path}")
        
        # Test properties used in template
        print(f"   is_image: {file_doc.is_image}")
        print(f"   is_pdf: {file_doc.is_pdf}")
        print(f"   is_video: {file_doc.is_video}")
        print(f"   is_audio: {file_doc.is_audio}")
        
        return True
        
    except FileDocument.DoesNotExist:
        print(f"❌ File with ID {file_id} not found in database")
        
        # Let's see what files do exist
        print("\nExisting files:")
        files = FileDocument.objects.all()[:10]  # Show first 10 files
        for f in files:
            print(f"   {f.id} - {f.name}")
        
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_users():
    """Check if there are any users/employees"""
    print("\nChecking users and employees:")
    
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    employees = Employee.objects.all()
    print(f"Total employees: {employees.count()}")
    
    if employees.exists():
        for emp in employees[:5]:  # Show first 5 employees
            print(f"   {emp.get_full_name()} - {emp.user.email if emp.user else 'No user'}")

if __name__ == "__main__":
    print("🔍 Testing file view functionality...\n")
    test_file_view()
    test_users()
    print("\n✅ Test completed!")
