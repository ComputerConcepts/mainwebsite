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

def test_storage_system():
    print("Testing Storage Management System")
    print("=" * 50)
    
    # Test StorageManager methods
    print("\n1. Testing StorageManager utility class:")
    
    # Get system storage info
    storage_info = StorageManager.get_system_storage_info()
    print(f"VM Total storage: {storage_info['total'] / (1024**3):.2f} GB")
    print(f"VM Used storage: {storage_info['used'] / (1024**3):.2f} GB")
    print(f"VM Free storage: {storage_info['free'] / (1024**3):.2f} GB")
    
    # Get user count
    user_count = Employee.objects.count()
    print(f"Total users: {user_count}")
    
    # Get dynamic quota per user
    if user_count > 0:
        dynamic_quota = StorageManager.calculate_user_quota()
        print(f"Dynamic quota per user: {dynamic_quota / (1024**3):.2f} GB")
    
    # Test storage calculations for users
    print("\n2. Testing user storage calculations:")
    users = Employee.objects.all()[:5]  # Test first 5 users
    
    for user in users:
        storage_percentage = user.get_storage_percentage()
        available_storage = user.get_available_storage()
        
        print(f"\nUser: {user.user.first_name} {user.user.last_name}")
        print(f"  Storage Used: {user.storage_used / (1024**2):.2f} MB")
        print(f"  Storage Available: {available_storage / (1024**3):.2f} GB")
        print(f"  Storage Percentage: {storage_percentage:.1f}%")
        print(f"  Storage Quota: {user.storage_quota / (1024**3):.2f} GB")
    
    print("\n3. Testing storage system integrity:")
    
    # Check if all users have proper quotas
    users_without_quota = Employee.objects.filter(storage_quota=0).count()
    print(f"Users without quota set: {users_without_quota}")
    
    # Total storage allocated
    total_allocated = sum(user.storage_quota for user in Employee.objects.all())
    print(f"Total storage allocated: {total_allocated / (1024**3):.2f} GB")
    
    # System storage usage
    total_used = sum(user.storage_used for user in Employee.objects.all())
    print(f"Total storage used by users: {total_used / (1024**3):.2f} GB")
    
    # Get comprehensive storage stats
    print("\n4. Testing comprehensive storage statistics:")
    storage_stats = StorageManager.get_storage_stats()
    print(f"Active users: {storage_stats['active_users']}")
    print(f"Total files: {storage_stats['total_files']}")
    print(f"Quota per user: {storage_stats['quota_per_user_display']}")
    print(f"Total allocated storage: {storage_stats['total_allocated_display']}")
    print(f"Total user storage used: {storage_stats['total_user_storage_display']}")
    
    print("\n✅ Storage system test completed!")

if __name__ == '__main__':
    test_storage_system()
