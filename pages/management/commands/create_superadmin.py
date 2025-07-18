from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import Employee
from django.db import transaction
import uuid

class Command(BaseCommand):
    help = 'Create a super admin user with employee record'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the super admin')
        parser.add_argument('--email', type=str, help='Email for the super admin')
        parser.add_argument('--password', type=str, help='Password for the super admin')
        parser.add_argument('--first-name', type=str, help='First name')
        parser.add_argument('--last-name', type=str, help='Last name')

    def handle(self, *args, **options):
        username = options.get('username') or input('Enter username: ')
        email = options.get('email') or input('Enter email: ')
        password = options.get('password') or input('Enter password: ')
        first_name = options.get('first_name') or input('Enter first name: ')
        last_name = options.get('last_name') or input('Enter last name: ')

        try:
            with transaction.atomic():
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.ERROR(f'User with username "{username}" already exists')
                    )
                    return

                if User.objects.filter(email=email).exists():
                    self.stdout.write(
                        self.style.ERROR(f'User with email "{email}" already exists')
                    )
                    return

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,
                    is_superuser=True
                )

                # Generate employee ID
                employee_id = f"ADMIN{str(uuid.uuid4())[:8].upper()}"

                # Create employee record
                employee = Employee.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department='Management',
                    position='Super Administrator',
                    role='super_admin',
                    is_active=True,
                    is_email_verified=True,
                    phone='000-000-0000',  # Default phone
                    notes='Super administrator account created via management command'
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Super admin created successfully!\n'
                        f'Username: {username}\n'
                        f'Email: {email}\n'
                        f'Employee ID: {employee_id}\n'
                        f'Role: {employee.get_role_display()}\n'
                        f'Department: {employee.department}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating super admin: {str(e)}')
            )
