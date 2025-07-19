#!/usr/bin/env python
"""
Storage Quota Update Script
This script updates storage quotas for all users based on current VM capacity.
Run this script hourly to maintain optimal storage allocation.

Usage:
    python update_storage_quotas.py
    python update_storage_quotas.py --dry-run
    python update_storage_quotas.py --verbose
"""

import os
import sys
import django
from datetime import datetime
import logging

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import StorageManager, Employee

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage_quota_updates.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to update storage quotas"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update storage quotas for all users')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be updated without making changes')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    
    args = parser.parse_args()
    
    try:
        logger.info("Starting storage quota update...")
        
        # Get current storage statistics
        stats = StorageManager.get_storage_stats()
        
        if args.verbose or args.dry_run:
            print(f"Current System Status:")
            print(f"  - VM Total Storage: {stats['system']['total'] / (1024**3):.2f} GB")
            print(f"  - VM Available Storage: {stats['system']['free'] / (1024**3):.2f} GB")
            print(f"  - Active Users: {stats['active_users']}")
            print(f"  - Current Quota per User: {stats['quota_per_user_display']}")
            print(f"  - Total Allocated: {stats['total_allocated_display']}")
            print(f"  - Total User Storage Used: {stats['total_user_storage_display']}")
        
        if args.dry_run:
            # Calculate what the new quota would be
            new_quota = StorageManager.calculate_user_quota()
            new_quota_display = Employee._format_bytes(new_quota)
            print(f"DRY RUN: Would update {stats['active_users']} users to {new_quota_display} each")
            logger.info(f"DRY RUN: Would update {stats['active_users']} users to {new_quota_display} each")
            return
        
        # Update quotas
        result = StorageManager.update_all_user_quotas()
        
        success_msg = f"Successfully updated {result['updated_users']} users with quota: {result['quota_display']} each"
        print(f"✅ {success_msg}")
        logger.info(success_msg)
        
        if args.verbose:
            # Show updated statistics
            updated_stats = StorageManager.get_storage_stats()
            print(f"Updated System Status:")
            print(f"  - New Quota per User: {updated_stats['quota_per_user_display']}")
            print(f"  - New Total Allocated: {updated_stats['total_allocated_display']}")
        
        logger.info("Storage quota update completed successfully")
        
    except Exception as e:
        error_msg = f"Error updating storage quotas: {str(e)}"
        print("ERROR: " + error_msg)
        logger.error(error_msg)
        sys.exit(1)

if __name__ == '__main__':
    main()
