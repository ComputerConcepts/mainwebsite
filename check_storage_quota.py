#!/usr/bin/env python
"""
Storage Quota Helper for Shared VM Environments
This script helps configure storage quotas for shared hosting like PythonAnywhere.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import StorageManager, Employee

def detect_shared_vm_quota():
    """Detect if we're on a shared VM and suggest appropriate quotas"""
    print("🔍 Shared VM Storage Quota Detection")
    print("=" * 50)
    
    # Get current project directory size
    project_dir = os.getcwd()
    project_size = get_directory_size(project_dir)
    project_size_mb = project_size / (1024**2)
    
    print(f"📁 Current project directory: {project_dir}")
    print(f"📊 Project size: {project_size_mb:.1f} MB")
    
    # Estimate reasonable quotas for different environments
    print(f"\n🎯 Recommended Storage Limits for Different Environments:")
    print(f"")
    
    # PythonAnywhere quotas
    pa_quotas = {
        'PythonAnywhere Free': 0.5,      # 512 MiB
        'PythonAnywhere Hacker': 3.0,    # 3GB  
        'PythonAnywhere Web Dev': 10.0,  # 10GB
        'Shared Hosting (5GB)': 5.0,
        'Shared Hosting (10GB)': 10.0,
        'VPS/Dedicated': None
    }
    
    for env_name, quota_gb in pa_quotas.items():
        if quota_gb is None:
            print(f"  🖥️  {env_name:.<25} No limit (use full disk)")
            continue
            
        quota_mb = quota_gb * 1024
        
        # Reserve space for system files, temp files, etc.
        reserved_mb = 200  # 200MB for system overhead
        available_for_users_mb = quota_mb - reserved_mb
        
        # Calculate per-user quota
        active_users = Employee.objects.filter(is_active=True).count()
        if active_users > 0:
            quota_per_user_mb = available_for_users_mb / active_users
            quota_per_user_gb = quota_per_user_mb / 1024
            
            # Check if it's viable
            if quota_per_user_mb > 50:  # At least 50MB per user
                status = "✅"
            elif quota_per_user_mb > 10:  # At least 10MB per user
                status = "⚠️ "
            else:
                status = "❌"
                
            print(f"  {status} {env_name:.<25} {quota_per_user_gb:.2f}GB per user ({active_users} users)")
        else:
            print(f"  ❓ {env_name:.<25} No active users to calculate")

def get_directory_size(directory):
    """Get directory size in bytes (optimized for project directories)"""
    total_size = 0
    try:
        # Only scan specific project directories to avoid huge home directory scans
        if 'computer concepts' in directory.lower():
            for file_path in Path(directory).rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        continue
        else:
            # For other directories, use a simpler approach
            for root, dirs, files in os.walk(directory):
                # Skip common large directories that aren't user files
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue
                        
                # Limit scanning depth to avoid infinite recursion
                if root.count(os.sep) - directory.count(os.sep) > 3:
                    dirs.clear()
                    
    except Exception as e:
        print(f"   ⚠️  Error scanning {directory}: {str(e)}")
    
    return total_size

def suggest_quota_setting():
    """Suggest appropriate quota setting"""
    print(f"\n💡 How to Configure Storage Quota:")
    print(f"")
    print(f"1. For PythonAnywhere Free (512MB quota):")
    print(f"   Add to settings.py: APPLICATION_STORAGE_LIMIT_GB = 0.5")
    print(f"")
    print(f"2. For PythonAnywhere Hacker (3GB quota):")
    print(f"   Add to settings.py: APPLICATION_STORAGE_LIMIT_GB = 3")
    print(f"")
    print(f"3. For other shared hosting:")
    print(f"   Add to settings.py: APPLICATION_STORAGE_LIMIT_GB = <your_quota_in_gb>")
    print(f"")
    print(f"4. For VPS/Dedicated servers:")
    print(f"   Keep: APPLICATION_STORAGE_LIMIT_GB = None")
    print(f"")
    print(f"⚡ After setting, run: python update_storage_quotas.py")
    print(f"   This will recalculate user quotas based on your actual limit.")

def main():
    print("🚀 Storage Quota Configuration Helper")
    print("=" * 60)
    
    # Current system status
    stats = StorageManager.get_storage_stats()
    current_limit = getattr(__import__('django.conf', fromlist=['settings']).settings, 
                           'APPLICATION_STORAGE_LIMIT_GB', None)
    
    if current_limit:
        print(f"✅ Current configured limit: {current_limit} GB")
    else:
        print(f"⚠️  No storage limit configured (using full VM disk)")
        print(f"   This may be inaccurate on shared hosting platforms!")
    
    print(f"📊 Current usage: {stats['total_user_storage_display']} by {stats['active_users']} users")
    print(f"📝 Current quota per user: {stats['quota_per_user_display']}")
    
    print()
    detect_shared_vm_quota()
    suggest_quota_setting()

if __name__ == '__main__':
    main()
