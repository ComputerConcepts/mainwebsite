from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import Employee
from django.db import transaction

class Command(BaseCommand):
    help = 'Create a superuser employee account'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the superuser')
        parser.add_argument('--email', type=str, help='Email for the superuser')
        parser.add_argument('--password', type=str, help='Password for the superuser')
        parser.add_argument('--employee-id', type=str, help='Employee ID')
        parser.add_argument('--first-name', type=str, help='First name')
        parser.add_argument('--last-name', type=str, help='Last name')
        parser.add_argument('--department', type=str, default='IT', help='Department')
        parser.add_argument('--position', type=str, default='System Administrator', help='Position')
        parser.add_argument('--phone', type=str, help='Phone number')

    def handle(self, *args, **options):
        username = options.get('username') or input('Username: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')
        employee_id = options.get('employee_id') or input('Employee ID: ')
        first_name = options.get('first_name') or input('First Name: ')
        last_name = options.get('last_name') or input('Last Name: ')
        department = options.get('department') or input('Department (default: IT): ') or 'IT'
        position = options.get('position') or input('Position (default: System Administrator): ') or 'System Administrator'
        phone = options.get('phone') or input('Phone: ')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username "{username}" already exists.'))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User with email "{email}" already exists.'))
            return

        if Employee.objects.filter(employee_id=employee_id).exists():
            self.stdout.write(self.style.ERROR(f'Employee with ID "{employee_id}" already exists.'))
            return

        try:
            with transaction.atomic():
                # Create superuser
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                # Create employee profile
                employee = Employee.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department=department,
                    position=position,
                    phone=phone,
                    is_active=True,
                    is_email_verified=True  # Auto-verify for superuser
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created superuser employee account:\n'
                        f'Username: {username}\n'
                        f'Email: {email}\n'
                        f'Employee ID: {employee_id}\n'
                        f'Department: {department}\n'
                        f'Position: {position}'
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser employee: {str(e)}'))
