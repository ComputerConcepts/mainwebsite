from django.core.management.base import BaseCommand
from pages.models import Employee
import secrets


class Command(BaseCommand):
    help = 'Fix employee email verification tokens'

    def handle(self, *args, **options):
        """Fix employee verification token issues"""
        
        # Clear tokens for verified employees
        verified_with_tokens = Employee.objects.filter(
            is_email_verified=True,
            email_verification_token__isnull=False
        )
        
        count_cleared = 0
        for employee in verified_with_tokens:
            employee.email_verification_token = None
            employee.save()
            count_cleared += 1
            self.stdout.write(f"Cleared token for verified employee: {employee.user.email}")
        
        # Generate tokens for unverified employees without tokens
        unverified_without_tokens = Employee.objects.filter(
            is_email_verified=False,
            email_verification_token__isnull=True
        )
        
        count_generated = 0
        for employee in unverified_without_tokens:
            employee.email_verification_token = secrets.token_urlsafe(32)
            employee.save()
            count_generated += 1
            self.stdout.write(f"Generated token for unverified employee: {employee.user.email}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fixed {count_cleared} verified employees and {count_generated} unverified employees'
            )
        )
