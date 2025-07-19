from django.core.management.base import BaseCommand
from pages.models import StorageManager, Employee
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Updates storage quotas for all users based on current VM capacity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting storage quota update...')
        )
        
        try:
            # Get current storage statistics
            stats = StorageManager.get_storage_stats()
            
            if options['verbose'] or options['dry_run']:
                self.stdout.write(f"Current System Status:")
                self.stdout.write(f"  - VM Total Storage: {stats['system']['total'] / (1024**3):.2f} GB")
                self.stdout.write(f"  - VM Available Storage: {stats['system']['free'] / (1024**3):.2f} GB")
                self.stdout.write(f"  - Active Users: {stats['active_users']}")
                self.stdout.write(f"  - Current Quota per User: {stats['quota_per_user_display']}")
                self.stdout.write(f"  - Total Allocated: {stats['total_allocated_display']}")
                self.stdout.write(f"  - Total User Storage Used: {stats['total_user_storage_display']}")
            
            if options['dry_run']:
                # Calculate what the new quota would be
                new_quota = StorageManager.calculate_user_quota()
                new_quota_display = Employee._format_bytes(new_quota)
                self.stdout.write(
                    self.style.WARNING(f"DRY RUN: Would update {stats['active_users']} users to {new_quota_display} each")
                )
                return
            
            # Update quotas
            result = StorageManager.update_all_user_quotas()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully updated {result['updated_users']} users with quota: {result['quota_display']} each"
                )
            )
            
            if options['verbose']:
                # Show updated statistics
                updated_stats = StorageManager.get_storage_stats()
                self.stdout.write(f"Updated System Status:")
                self.stdout.write(f"  - New Quota per User: {updated_stats['quota_per_user_display']}")
                self.stdout.write(f"  - New Total Allocated: {updated_stats['total_allocated_display']}")
            
            # Log the update
            logger.info(f"Storage quotas updated: {result['updated_users']} users, {result['quota_display']} each")
            
        except Exception as e:
            error_msg = f"Error updating storage quotas: {str(e)}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise
