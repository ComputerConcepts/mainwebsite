#!/usr/bin/env python
"""
Find file by name or show all files with their URLs
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import FileDocument

def find_files(search_term=None):
    """Find files by name or show all files"""
    print("📁 File Database Search\n")
    
    if search_term:
        files = FileDocument.objects.filter(name__icontains=search_term)
        print(f"Searching for files containing: '{search_term}'")
    else:
        files = FileDocument.objects.all()
        print("All files in database:")
    
    print(f"Found {files.count()} file(s)\n")
    
    for file_doc in files:
        print(f"📄 {file_doc.name}")
        print(f"   ID: {file_doc.id}")
        print(f"   Type: {file_doc.file_type}")
        print(f"   Size: {file_doc.get_file_size_display()}")
        print(f"   Owner: {file_doc.uploaded_by.get_full_name()}")
        print(f"   Created: {file_doc.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   URL: http://127.0.0.1:8000/employee/files/view/{file_doc.id}/")
        print(f"   Public URL: https://onecomputerconcepts.com/employee/files/view/{file_doc.id}/")
        
        # Check if file exists on disk
        file_path = file_doc.get_file_path()
        if file_path and os.path.exists(file_path):
            print(f"   Status: ✅ File exists on disk")
        else:
            print(f"   Status: ❌ File missing on disk")
        print()

def main():
    import sys
    
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
        find_files(search_term)
    else:
        find_files()
        
        print("\n💡 Tips:")
        print("   - To search for specific files: python find_files.py search_term")
        print("   - File IDs are used in URLs: /employee/files/view/{file_id}/")
        print("   - If a file is missing, check if it was deleted or moved")

if __name__ == "__main__":
    main()
