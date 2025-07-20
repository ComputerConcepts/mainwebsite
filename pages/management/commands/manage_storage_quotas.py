from django.core.management.base import BaseCommand
from pages.models import Employee
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Manually configure storage quotas via command line'

    def add_arguments(self, parser):
        parser.add_argument(
            '--set-global-quota',
            type=float,
            help='Set quota for all active users in GB (e.g., --set-global-quota 1.5)',
        )
        parser.add_argument(
            '--set-user-quota',
            nargs=2,
            metavar=('USERNAME', 'QUOTA_GB'),
            help='Set quota for specific user (e.g., --set-user-quota admin 2.0)',
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all users and their current quotas',
        )
        parser.add_argument(
            '--reset-quotas',
            action='store_true',
            help='Reset all quotas to default (1GB)',
        )

    def handle(self, *args, **options):
        if options['list_users']:
            self.list_users()
        elif options['set_global_quota']:
            self.set_global_quota(options['set_global_quota'])
        elif options['set_user_quota']:
            username, quota_gb = options['set_user_quota']
            self.set_user_quota(username, float(quota_gb))
        elif options['reset_quotas']:
            self.reset_quotas()
        else:
            self.show_help()

    def list_users(self):
        """List all users and their storage quotas"""
        self.stdout.write(self.style.SUCCESS("Current User Storage Quotas"))
        self.stdout.write("=" * 60)
        
        employees = Employee.objects.all().order_by('user__username')
        
        if not employees.exists():
            self.stdout.write("No employees found.")
            return
        
        # Header
        self.stdout.write(f"{'Username':<15} {'Name':<20} {'Quota':<10} {'Used':<10} {'%':<5} {'Active'}")
        self.stdout.write("-" * 60)
        
        for emp in employees:
            username = emp.user.username
            name = f"{emp.user.first_name} {emp.user.last_name}".strip() or "N/A"
            quota_display = emp.get_storage_quota_display()
            used_display = emp.get_storage_used_display()
            percentage = emp.get_storage_percentage()
            active = "Yes" if emp.is_active else "No"
            
            self.stdout.write(
                f"{username:<15} {name:<20} {quota_display:<10} {used_display:<10} "
                f"{percentage:>4.1f}% {active}"
            )
        
        # Summary
        total_quota = sum(emp.storage_quota or 0 for emp in employees if emp.is_active)
        total_used = sum(emp.storage_used or 0 for emp in employees if emp.is_active)
        active_count = employees.filter(is_active=True).count()
        
        self.stdout.write("-" * 60)
        self.stdout.write(f"Active users: {active_count}")
        self.stdout.write(f"Total quota allocated: {self.format_bytes(total_quota)}")
        self.stdout.write(f"Total storage used: {self.format_bytes(total_used)}")

    def set_global_quota(self, quota_gb):
        """Set the same quota for all active users"""
        quota_bytes = int(quota_gb * 1024 * 1024 * 1024)  # Convert GB to bytes
        
        active_employees = Employee.objects.filter(is_active=True)
        count = active_employees.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("No active employees found."))
            return
        
        # Confirm action
        self.stdout.write(f"Setting quota to {quota_gb}GB for {count} active users...")
        
        # Update quotas
        updated = active_employees.update(storage_quota=quota_bytes)
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully updated {updated} users with {quota_gb}GB quota")
        )
        
        # Show summary
        total_allocated = quota_bytes * count
        self.stdout.write(f"Total allocated: {self.format_bytes(total_allocated)}")

    def set_user_quota(self, username, quota_gb):
        """Set quota for a specific user"""
        try:
            user = User.objects.get(username=username)
            employee = Employee.objects.get(user=user)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User '{username}' not found"))
            return
        except Employee.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Employee profile for '{username}' not found"))
            return
        
        quota_bytes = int(quota_gb * 1024 * 1024 * 1024)  # Convert GB to bytes
        old_quota = employee.storage_quota or 0
        
        employee.storage_quota = quota_bytes
        employee.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Updated {username}'s quota: "
                f"{self.format_bytes(old_quota)} → {self.format_bytes(quota_bytes)}"
            )
        )

    def reset_quotas(self):
        """Reset all quotas to 1GB default"""
        default_quota = 1024 * 1024 * 1024  # 1GB in bytes
        
        employees = Employee.objects.all()
        count = employees.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("No employees found."))
            return
        
        self.stdout.write(f"Resetting quota to 1GB for {count} users...")
        
        updated = employees.update(storage_quota=default_quota)
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Reset {updated} users to 1GB quota")
        )

    def show_help(self):
        """Show usage examples"""
        self.stdout.write(self.style.SUCCESS("Storage Quota Management Commands"))
        self.stdout.write("=" * 50)
        self.stdout.write("Usage examples:")
        self.stdout.write("")
        self.stdout.write("1. List all users and quotas:")
        self.stdout.write("   python manage.py manage_storage_quotas --list-users")
        self.stdout.write("")
        self.stdout.write("2. Set 1.5GB quota for all active users:")
        self.stdout.write("   python manage.py manage_storage_quotas --set-global-quota 1.5")
        self.stdout.write("")
        self.stdout.write("3. Set 2GB quota for specific user:")
        self.stdout.write("   python manage.py manage_storage_quotas --set-user-quota admin 2.0")
        self.stdout.write("")
        self.stdout.write("4. Reset all quotas to 1GB:")
        self.stdout.write("   python manage.py manage_storage_quotas --reset-quotas")
        self.stdout.write("")
        self.stdout.write("💡 For PythonAnywhere:")
        self.stdout.write("   Free (512MB): --set-global-quota 0.4")
        self.stdout.write("   Hacker (3GB): --set-global-quota 1.4")
        self.stdout.write("   Web Dev (10GB): --set-global-quota 4.5")

    def format_bytes(self, bytes_value):
        """Format bytes in human readable format"""
        if bytes_value == 0:
            return "0B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        
        return f"{bytes_value:.1f}TB"
