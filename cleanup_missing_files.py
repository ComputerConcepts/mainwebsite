#!/usr/bin/env python
"""
Clean up database entries for missing files
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import FileDocument, FileActivity, FileShare

def cleanup_missing_files():
    """Remove database entries for files that don't exist on disk"""
    print("🧹 Cleaning up missing files...\n")
    
    missing_files = []
    total_files = FileDocument.objects.count()
    
    for file_doc in FileDocument.objects.all():
        file_path = file_doc.get_file_path()
        if not file_path or not os.path.exists(file_path):
            missing_files.append(file_doc)
            print(f"❌ Missing: {file_doc.name} (ID: {file_doc.id})")
    
    if missing_files:
        print(f"\nFound {len(missing_files)} missing files out of {total_files} total files.")
        
        response = input("\nDo you want to remove these entries from the database? (y/N): ")
        
        if response.lower() == 'y':
            for file_doc in missing_files:
                print(f"Removing: {file_doc.name}")
                
                # Remove related records first
                FileActivity.objects.filter(document=file_doc).delete()
                FileShare.objects.filter(document=file_doc).delete()
                
                # Remove the file document
                file_doc.delete()
            
            print(f"\n✅ Removed {len(missing_files)} missing file entries.")
        else:
            print("\n❌ Cleanup cancelled.")
    else:
        print(f"✅ All {total_files} files have valid disk files.")

def main():
    cleanup_missing_files()

if __name__ == "__main__":
    main()
