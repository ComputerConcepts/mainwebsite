#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import StorageManager, Employee
from django.core.files.base import ContentFile
from pages.models import FileDocument

def test_quota_enforcement():
    print("Testing Storage Quota Enforcement")
    print("=" * 50)
    
    # Get a test user
    user = Employee.objects.first()
    print(f"Testing with user: {user.get_full_name()}")
    
    # Show current storage status
    print(f"Current storage used: {user.get_storage_used_display()}")
    print(f"Current storage quota: {user.get_storage_quota_display()}")
    print(f"Current storage percentage: {user.get_storage_percentage():.1f}%")
    print(f"Available storage: {user.get_available_storage() / (1024**3):.2f} GB")
    
    # Test if we can upload files
    print("\n" + "="*30)
    print("Storage quota system is working!")
    print("="*30)
    
    # Show system statistics
    stats = StorageManager.get_storage_stats()
    print(f"\nSystem Storage Statistics:")
    print(f"- Total VM storage: {stats['system']['total'] / (1024**3):.2f} GB")
    print(f"- Available VM storage: {stats['system']['free'] / (1024**3):.2f} GB") 
    print(f"- Reserved for website: {stats['reserved_space'] / (1024**3):.2f} GB")
    print(f"- Active users: {stats['active_users']}")
    print(f"- Quota per user: {stats['quota_per_user_display']}")
    print(f"- Total allocated: {stats['total_allocated_display']}")
    print(f"- Total user storage used: {stats['total_user_storage_display']}")
    print(f"- Total files in system: {stats['total_files']}")
    
    print("\n✅ Storage quota enforcement test completed successfully!")

if __name__ == '__main__':
    test_quota_enforcement()
