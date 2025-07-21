#!/usr/bin/env python
"""
Create a test user login and show login credentials
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.contrib.auth.models import User
from pages.models import Employee

def show_login_info():
    """Show available login credentials"""
    print("🔐 Available Login Credentials:\n")
    
    users = User.objects.all()
    
    for user in users:
        try:
            employee = Employee.objects.get(user=user)
            print(f"👤 {employee.get_full_name()}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            if user.check_password('admin123'):
                print(f"   Password: admin123 ✅")
            elif user.check_password('password123'):
                print(f"   Password: password123 ✅")
            else:
                print(f"   Password: [unknown] ❌")
            print(f"   Is Admin: {employee.is_admin}")
            print()
        except Employee.DoesNotExist:
            print(f"👤 {user.username} (No employee profile)")
            print(f"   Email: {user.email}")
            print()
    
    print("🔗 Login URL: http://127.0.0.1:8000/employee/login/")
    print("📄 Test File URL: http://127.0.0.1:8000/employee/files/view/18050168-36f4-4ca3-99a5-e3045a962f74/")

if __name__ == "__main__":
    show_login_info()
