#!/usr/bin/env python
"""
Create sample file shares for testing the enhanced share modal
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import FileDocument, FileShare, Employee

def create_sample_shares():
    """Create sample file shares for testing"""
    print("📄 Creating sample file shares...\n")
    
    # Get the first file that exists
    file_doc = FileDocument.objects.first()
    if not file_doc:
        print("❌ No files found in database")
        return
    
    print(f"Using file: {file_doc.name} (Owner: {file_doc.uploaded_by.get_full_name()})")
    
    # Get all employees except the owner
    available_employees = Employee.objects.exclude(id=file_doc.uploaded_by.id)
    
    if not available_employees.exists():
        print("❌ No other employees found to share with")
        return
    
    # Create shares with different permission levels
    permissions = ['view', 'edit', 'full']
    
    for i, employee in enumerate(available_employees[:3]):  # Limit to 3 shares
        permission = permissions[i % len(permissions)]
        
        # Check if share already exists
        existing_share = FileShare.objects.filter(
            document=file_doc,
            shared_with=employee
        ).first()
        
        if existing_share:
            print(f"✅ Share already exists: {employee.get_full_name()} ({existing_share.permission})")
        else:
            share = FileShare.objects.create(
                document=file_doc,
                shared_with=employee,
                shared_by=file_doc.uploaded_by,
                permission=permission
            )
            print(f"✅ Created share: {employee.get_full_name()} ({permission})")
    
    print(f"\n📊 File sharing summary:")
    print(f"   File: {file_doc.name}")
    print(f"   Owner: {file_doc.uploaded_by.get_full_name()}")
    
    shares = FileShare.objects.filter(document=file_doc)
    if shares.exists():
        print(f"   Shared with {shares.count()} person(s):")
        for share in shares:
            print(f"     - {share.shared_with.get_full_name()} ({share.get_permission_display()})")
    else:
        print("   Not shared with anyone")
    
    print(f"\n🔗 Test URL: http://127.0.0.1:8000/employee/files/view/{file_doc.id}/")
    print(f"🌐 Public URL: https://onecomputerconcepts.com/employee/files/view/{file_doc.id}/")

if __name__ == "__main__":
    create_sample_shares()
