#!/usr/bin/env python
"""
Reset user passwords for testing
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.contrib.auth.models import User

def reset_passwords():
    """Reset passwords for testing"""
    print("🔑 Resetting passwords for testing...\n")
    
    # Update admin user
    try:
        admin_user = User.objects.get(username='admin')
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✅ Admin password reset: admin / admin123")
    except User.DoesNotExist:
        print("❌ Admin user not found")
    
    # Update aayushgauba user
    try:
        aayush_user = User.objects.get(username='aayushgauba')
        aayush_user.set_password('password123')
        aayush_user.save()
        print(f"✅ Aayush password reset: aayushgauba / password123")
    except User.DoesNotExist:
        print("❌ Aayush user not found")
    
    print(f"\n🔗 Login URL: http://127.0.0.1:8000/employee/login/")
    print(f"📄 Test File URL (login as aayushgauba to see share modal): http://127.0.0.1:8000/employee/files/view/18050168-36f4-4ca3-99a5-e3045a962f74/")

if __name__ == "__main__":
    reset_passwords()
