from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import Employee
from django.db import transaction

class Command(BaseCommand):
    help = 'Promote an existing user to superuser by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to promote')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            with transaction.atomic():
                # Find the user
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'User with email {email} not found')
                    )
                    return
                
                # Promote to superuser
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
                
                # Update employee record if exists
                try:
                    employee = Employee.objects.get(user=user)
                    employee.role = 'super_admin'
                    employee.is_active = True
                    employee.is_email_verified = True
                    if employee.department == 'Other':
                        employee.department = 'Management'
                    if not employee.position or employee.position == '':
                        employee.position = 'Administrator'
                    employee.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Successfully promoted {user.first_name} {user.last_name} to Super Administrator!\n'
                            f'📧 Email: {email}\n'
                            f'🆔 Employee ID: {employee.employee_id}\n'
                            f'🏢 Department: {employee.department}\n'
                            f'💼 Position: {employee.position}\n'
                            f'🔐 Role: {employee.get_role_display()}\n'
                        )
                    )
                    
                except Employee.DoesNotExist:
                    self.stdout.write(
                        self.style.SUCCESS(f'User promoted to superuser, but no employee record found')
                    )
                    self.stdout.write(
                        self.style.WARNING(f'Please create an employee record for full functionality')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error promoting user: {str(e)}')
            )
