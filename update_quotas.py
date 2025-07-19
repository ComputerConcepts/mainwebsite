#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import StorageManager

# Update all user quotas
result = StorageManager.update_all_user_quotas()
print(f"Updated {result['updated_users']} users with quota: {result['quota_display']} each")
print(f"Total quota per user: {result['quota_per_user']} bytes")
