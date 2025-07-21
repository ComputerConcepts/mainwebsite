#!/usr/bin/env python
"""
Django shell test script to debug transfer ownership
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from pages.models import Employee, FileDocument, FileActivity
from django.contrib.auth.models import User

def debug_transfer_ownership():
    print("🔧 TRANSFER OWNERSHIP DEBUG")
    print("=" * 50)
    
    # Check database content
    employee_count = Employee.objects.count()
    file_count = FileDocument.objects.count()
    
    print(f"\n📊 DATABASE CONTENT:")
    print(f"   Employees: {employee_count}")
    print(f"   Files: {file_count}")
    
    if employee_count < 2:
        print(f"❌ Need at least 2 employees for testing transfer")
        return False
    
    if file_count == 0:
        print(f"❌ Need at least 1 file for testing transfer")
        return False
    
    # Get some sample data
    employees = Employee.objects.all()[:5]
    files = FileDocument.objects.all()[:5]
    
    print(f"\n👥 SAMPLE EMPLOYEES:")
    for i, emp in enumerate(employees, 1):
        print(f"   {i}. {emp.get_full_name()} (ID: {emp.id}) - User: {emp.user.username}")
    
    print(f"\n📁 SAMPLE FILES:")
    for i, file_doc in enumerate(files, 1):
        print(f"   {i}. {file_doc.name} (ID: {file_doc.id})")
        print(f"      Owner: {file_doc.uploaded_by.get_full_name()} (ID: {file_doc.uploaded_by.id})")
    
    # Test transfer simulation
    if len(employees) >= 2 and files:
        print(f"\n🧪 TESTING TRANSFER SIMULATION:")
        
        test_file = files[0]
        current_owner = test_file.uploaded_by
        
        # Find a different employee to transfer to
        new_owner = None
        for emp in employees:
            if emp.id != current_owner.id:
                new_owner = emp
                break
        
        if new_owner:
            print(f"   File: {test_file.name}")
            print(f"   Current owner: {current_owner.get_full_name()} (ID: {current_owner.id})")
            print(f"   Transfer to: {new_owner.get_full_name()} (ID: {new_owner.id})")
            
            # Simulate the transfer
            print(f"   🔄 Simulating transfer...")
            
            original_owner_id = test_file.uploaded_by.id
            test_file.uploaded_by = new_owner
            test_file.save()
            
            # Check if it worked
            test_file.refresh_from_db()
            new_owner_id = test_file.uploaded_by.id
            
            print(f"   📊 Transfer result:")
            print(f"      Original owner ID: {original_owner_id}")
            print(f"      New owner ID: {new_owner_id}")
            print(f"      Transfer successful: {new_owner_id == new_owner.id}")
            
            # Create activity log
            FileActivity.objects.create(
                document=test_file,
                user=current_owner,
                action='transfer_ownership',
                details=f'DEBUG: transferred ownership from {current_owner.get_full_name()} to {new_owner.get_full_name()}',
            )
            print(f"   ✅ Activity logged")
            
            # Transfer back to original owner
            test_file.uploaded_by = current_owner
            test_file.save()
            print(f"   🔄 Reverted transfer for testing")
            
            return True
        else:
            print(f"   ❌ Could not find different employee for transfer test")
            return False
    
    return True

if __name__ == "__main__":
    debug_transfer_ownership()
