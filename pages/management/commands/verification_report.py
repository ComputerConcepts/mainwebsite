from django.core.management.base import BaseCommand
from pages.models import Employee
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Display employee email verification status report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--unverified-only',
            action='store_true',
            help='Show only unverified employees',
        )
        parser.add_argument(
            '--missing-tokens',
            action='store_true',
            help='Show only unverified employees without tokens',
        )

    def handle(self, *args, **options):
        """Generate verification status report"""
        
        self.stdout.write(
            self.style.SUCCESS('Employee Email Verification Status Report')
        )
        self.stdout.write('=' * 60)
        
        employees = Employee.objects.all().select_related('user')
        
        if options['unverified_only']:
            employees = employees.filter(is_email_verified=False)
            self.stdout.write('\nShowing only UNVERIFIED employees:\n')
        elif options['missing_tokens']:
            employees = employees.filter(is_email_verified=False, email_verification_token__isnull=True)
            self.stdout.write('\nShowing only unverified employees WITHOUT tokens:\n')
        else:
            self.stdout.write('\nAll employees:\n')
        
        verified_count = 0
        unverified_count = 0
        missing_tokens = 0
        
        for employee in employees:
            status = "✓ VERIFIED" if employee.is_email_verified else "✗ UNVERIFIED"
            token_status = ""
            
            if not employee.is_email_verified:
                unverified_count += 1
                if employee.email_verification_token:
                    token_status = f" (Token: {employee.email_verification_token[:10]}...)"
                else:
                    token_status = " (NO TOKEN)"
                    missing_tokens += 1
            else:
                verified_count += 1
            
            self.stdout.write(
                f"{employee.employee_id:<15} {employee.user.email:<30} {status}{token_status}"
            )
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f"SUMMARY:")
        self.stdout.write(f"Total employees: {employees.count()}")
        if not options['unverified_only'] and not options['missing_tokens']:
            self.stdout.write(f"Verified: {verified_count}")
            self.stdout.write(f"Unverified: {unverified_count}")
            self.stdout.write(f"Unverified without tokens: {missing_tokens}")
        
        if missing_tokens > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\nWARNING: {missing_tokens} unverified employees are missing verification tokens!"
                )
            )
            self.stdout.write("Run 'python manage.py fix_employee_verification' to fix this.")
