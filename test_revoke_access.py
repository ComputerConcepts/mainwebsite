#!/usr/bin/env python
"""
Test revoke access functionality locally
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from pages.models import FileDocument, FileShare, Employee
import json

def test_revoke_access():
    print("🔧 TESTING REVOKE ACCESS FUNCTIONALITY")
    print("=" * 50)
    
    # Get the file with shares
    try:
        file_doc = FileDocument.objects.get(id="18050168-36f4-4ca3-99a5-e3045a962f74")
        shares = FileShare.objects.filter(document=file_doc)
        
        print(f"📄 File: {file_doc.name}")
        print(f"   Owner: {file_doc.uploaded_by.get_full_name()}")
        print(f"   Current shares: {shares.count()}")
        
        if shares.exists():
            share = shares.first()
            print(f"\n👤 Testing revoke for:")
            print(f"   User: {share.shared_with.get_full_name()}")
            print(f"   Email: {share.shared_with.user.email}")
            print(f"   Share ID: {share.id}")
            print(f"   Permission: {share.get_permission_display()}")
            
            # Test the endpoint
            client = Client()
            
            # Login as file owner
            owner_user = file_doc.uploaded_by.user
            client.force_login(owner_user)
            
            print(f"\n🧪 Testing unshare endpoint...")
            url = f"/employee/files/unshare/{file_doc.id}/{share.id}/"
            print(f"   URL: {url}")
            
            # Test the request
            response = client.post(url, content_type='application/json')
            
            print(f"\n📡 Response:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = json.loads(response.content)
                    print(f"   Data: {data}")
                    
                    if data.get('success'):
                        print("   ✅ Success: Revoke access working correctly!")
                        
                        # Check if share was actually deleted
                        remaining_shares = FileShare.objects.filter(document=file_doc)
                        print(f"   Remaining shares: {remaining_shares.count()}")
                    else:
                        print(f"   ❌ Error: {data.get('error', 'Unknown error')}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response: {response.content.decode()}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.content.decode()}")
                
        else:
            print("   ℹ️ No shares found to test with")
            
        print(f"\n🔗 Test in browser:")
        print(f"   1. Go to: http://127.0.0.1:8000/employee/files/view/{file_doc.id}/")
        print(f"   2. Click 'Manage Sharing'")
        print(f"   3. Click the red X button to test revoke")
        print(f"   4. Check browser console for debug messages")
        
    except FileDocument.DoesNotExist:
        print("❌ Test file not found")

if __name__ == "__main__":
    test_revoke_access()
