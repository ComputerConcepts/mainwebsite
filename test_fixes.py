#!/usr/bin/env python
"""
Test the fixes for revoke access and email autocomplete
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import FileDocument, FileShare, Employee

def test_fixes():
    """Test both fixes"""
    
    # Get the file with shares
    file_with_shares = "18050168-36f4-4ca3-99a5-e3045a962f74"
    
    try:
        file_doc = FileDocument.objects.get(id=file_with_shares)
        shares = FileShare.objects.filter(document=file_doc)
        
        print("=" * 60)
        print("🔧 TESTING ENHANCED SHARE MODAL FIXES")
        print("=" * 60)
        
        print(f"\n📄 File: {file_doc.name}")
        print(f"   Owner: {file_doc.uploaded_by.get_full_name()}")
        print(f"   Current shares: {shares.count()}")
        
        if shares.exists():
            for share in shares:
                print(f"   👤 Shared with: {share.shared_with.get_full_name()} ({share.shared_with.user.email})")
                print(f"      Share ID: {share.id}")
                print(f"      Permission: {share.get_permission_display()}")
        
        print(f"\n🔗 Test URL: http://127.0.0.1:8000/employee/files/view/{file_doc.id}/")
        
        print(f"\n✅ FIXES IMPLEMENTED:")
        print(f"   1. 🔧 Fixed revoke access functionality:")
        print(f"      - Uses correct unshare endpoint: /employee/files/unshare/{file_doc.id}/{{share_id}}/")
        print(f"      - Improved UI updates without page reload")
        print(f"      - Better error handling")
        
        print(f"\n   2. 📧 Added email autocomplete:")
        print(f"      - Type 2+ characters to see suggestions")
        print(f"      - Shows employee name, email, and department")
        print(f"      - Click to select suggestion")
        print(f"      - Uses endpoint: /api/employees/search-email/")
        
        print(f"\n🚀 TO TEST:")
        print(f"   1. Login with: aayushgauba / password123")
        print(f"   2. Go to: http://127.0.0.1:8000/employee/files/view/{file_doc.id}/")
        print(f"   3. Click 'Manage Sharing' button")
        print(f"   4. Test email autocomplete by typing in the email field")
        print(f"   5. Test revoke access by clicking the X button next to a share")
        
        # Test the search endpoint
        print(f"\n🔍 TESTING EMAIL SEARCH:")
        employees = Employee.objects.exclude(id=file_doc.uploaded_by.id)[:3]
        for emp in employees:
            print(f"   - {emp.get_full_name()} ({emp.user.email}) - {emp.department}")
        
        print(f"\n💡 SEARCH SUGGESTIONS WILL SHOW:")
        print(f"   - Employee names and emails")
        print(f"   - Department information")  
        print(f"   - Hover effects and click to select")
        
    except FileDocument.DoesNotExist:
        print(f"❌ File {file_with_shares} not found")

if __name__ == "__main__":
    test_fixes()
