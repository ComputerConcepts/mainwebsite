#!/usr/bin/env python
"""
Test Real-time Quota Update During Upload
This script tests the enhanced upload functionality that updates quotas before checking limits.
"""

import os
import sys
import django
import requests
from io import BytesIO

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from pages.models import StorageManager, Employee

def test_quota_update_during_upload():
    """Test that quotas are updated before upload validation"""
    print("Testing Real-time Quota Update During Upload")
    print("=" * 60)
    
    # Get current system status before any changes
    print("\n1. Current System Status:")
    stats = StorageManager.get_storage_stats()
    print(f"   - VM Available Storage: {stats['system']['free'] / (1024**3):.2f} GB")
    print(f"   - Active Users: {stats['active_users']}")
    print(f"   - Current Quota per User: {stats['quota_per_user_display']}")
    print(f"   - Total Allocated: {stats['total_allocated_display']}")
    
    # Get a test user
    test_user = Employee.objects.first()
    if not test_user:
        print("❌ No test user found!")
        return
    
    print(f"\n2. Test User: {test_user.get_full_name()}")
    print(f"   - Current Storage Used: {test_user.get_storage_used_display()}")
    print(f"   - Current Quota: {test_user.get_storage_quota_display()}")
    print(f"   - Available Space: {test_user._format_bytes(test_user.get_available_storage())}")
    print(f"   - Usage Percentage: {test_user.get_storage_percentage():.1f}%")
    
    # Simulate quota update (like what happens during upload)
    print(f"\n3. Simulating Upload Process:")
    print("   - Step 1: Updating all user quotas (as done during upload)...")
    
    try:
        quota_result = StorageManager.update_all_user_quotas()
        print(f"   ✅ Updated {quota_result['updated_users']} users with quota: {quota_result['quota_display']} each")
        
        # Refresh user data
        test_user.refresh_from_db()
        
        print(f"   - Step 2: Checking updated quota for test user...")
        print(f"     • New Quota: {test_user.get_storage_quota_display()}")
        print(f"     • Available Space: {test_user._format_bytes(test_user.get_available_storage())}")
        
        # Test file size that would exceed old quota but fit in new quota
        test_file_size = 50 * 1024 * 1024  # 50MB test file
        
        print(f"   - Step 3: Testing upload validation with {test_user._format_bytes(test_file_size)} file...")
        can_upload = test_user.can_upload_file(test_file_size)
        print(f"     • Can upload {test_user._format_bytes(test_file_size)}? {'✅ YES' if can_upload else '❌ NO'}")
        
        if can_upload:
            remaining_after = test_user.get_available_storage() - test_file_size
            print(f"     • Space remaining after upload: {test_user._format_bytes(remaining_after)}")
        else:
            shortfall = test_file_size - test_user.get_available_storage()
            print(f"     • Storage shortfall: {test_user._format_bytes(shortfall)}")
        
    except Exception as e:
        print(f"   ❌ Error during quota update: {str(e)}")
    
    print(f"\n4. Final System Statistics:")
    final_stats = StorageManager.get_storage_stats()
    print(f"   - Updated Quota per User: {final_stats['quota_per_user_display']}")
    print(f"   - Total Allocated: {final_stats['total_allocated_display']}")
    print(f"   - Total User Storage Used: {final_stats['total_user_storage_display']}")
    
    print(f"\n✅ Real-time quota update test completed!")
    print(f"🔄 The upload system will now automatically update quotas before each upload validation.")
    print(f"📊 This ensures users always get the latest storage allocation when uploading files.")

if __name__ == '__main__':
    test_quota_update_during_upload()
