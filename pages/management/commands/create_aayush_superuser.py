from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import Employee
from django.db import transaction
import uuid

class Command(BaseCommand):
    help = 'Create or promote aayushgauba@onecomputerconcepts.com to superuser'

    def handle(self, *args, **options):
        email = 'aayushgauba@onecomputerconcepts.com'
        
        try:
            with transaction.atomic():
                # Check if user already exists
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': 'aayushgauba',
                        'first_name': 'Aayush',
                        'last_name': 'Gauba',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True
                    }
                )
                
                if not created:
                    # User exists, update to superuser
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'User {email} promoted to superuser')
                    )
                else:
                    # Set a default password for new user
                    user.set_password('TempPassword123!')
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'New superuser created: {email}')
                    )
                
                # Create or update employee record
                employee, emp_created = Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        'employee_id': f"ADMIN{str(uuid.uuid4())[:8].upper()}",
                        'department': 'Management',
                        'position': 'Chief Executive Officer',
                        'role': 'super_admin',
                        'is_active': True,
                        'is_email_verified': True,
                        'phone': '000-000-0000',
                        'first_name': 'Aayush',
                        'last_name': 'Gauba',
                        'notes': 'CEO - Super Administrator account'
                    }
                )
                
                if not emp_created:
                    # Update existing employee to super admin
                    employee.role = 'super_admin'
                    employee.department = 'Management'
                    employee.position = 'Chief Executive Officer'
                    employee.is_active = True
                    employee.is_email_verified = True
                    employee.notes = 'CEO - Super Administrator account'
                    employee.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Employee record updated to super admin')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Employee record created')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ SUCCESS! Aayush Gauba is now a Super Administrator\n'
                        f'📧 Email: {email}\n'
                        f'🆔 Employee ID: {employee.employee_id}\n'
                        f'🏢 Department: {employee.department}\n'
                        f'💼 Position: {employee.position}\n'
                        f'🔐 Role: {employee.get_role_display()}\n'
                        f'{"🆕 Default Password: TempPassword123!" if created else "🔓 Existing password retained"}\n'
                        f'\n🎯 Access URLs:\n'
                        f'   - Admin Dashboard: /employee/admin/\n'
                        f'   - Django Admin: /admin/\n'
                        f'   - Employee Portal: /employee/dashboard/\n'
                        f'   - Project Boards: /employee/boards/\n'
                    )
                )
                
                if created:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  IMPORTANT: Please change the default password on first login!'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
