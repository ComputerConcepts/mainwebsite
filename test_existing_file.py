#!/usr/bin/env python
"""
Test the file view with an existing file
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import FileDocument

def test_existing_file():
    """Test with an existing file"""
    # Use the first file that exists
    file_doc = FileDocument.objects.first()
    
    if file_doc:
        print(f"Testing with existing file: {file_doc.id}")
        print(f"File name: {file_doc.name}")
        print(f"File type: {file_doc.file_type}")
        print(f"Size: {file_doc.get_file_size_display()}")
        
        # Test the properties used in template
        print(f"is_image: {file_doc.is_image}")
        print(f"is_pdf: {file_doc.is_pdf}")
        print(f"is_video: {file_doc.is_video}")
        print(f"is_audio: {file_doc.is_audio}")
        
        # Test file path
        file_path = file_doc.get_file_path()
        if file_path and os.path.exists(file_path):
            print(f"✅ File exists on disk: {file_path}")
        else:
            print(f"❌ File missing on disk: {file_path}")
        
        print(f"\nTest URL: http://127.0.0.1:8000/employee/files/view/{file_doc.id}/")
        return file_doc.id
    else:
        print("No files found in database")
        return None

if __name__ == "__main__":
    test_existing_file()
