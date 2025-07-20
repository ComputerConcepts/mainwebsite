"""
Django management command to run scheduled AI workflows
Usage: python manage.py run_ai_workflows
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from pages.ai_workflow_service import get_ai_workflow_service


class Command(BaseCommand):
    help = 'Run scheduled AI workflows and maintenance tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually executing workflows',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY RUN] ' if dry_run else ''}Starting AI workflow scheduler at {timezone.now()}"
            )
        )
        
        try:
            ai_service = get_ai_workflow_service()
            
            if not dry_run:
                executed_count = ai_service.run_scheduled_workflows()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully executed {executed_count} scheduled workflows"
                    )
                )
                
                # Get analytics
                analytics = ai_service.get_workflow_analytics()
                
                if verbose:
                    self.stdout.write("\n--- Workflow Analytics ---")
                    self.stdout.write(f"Total Rules: {analytics['total_rules']}")
                    self.stdout.write(f"Active Rules: {analytics['active_rules']}")
                    self.stdout.write(f"Total Executions: {analytics['total_executions']}")
                    self.stdout.write(f"Successful Executions: {analytics['successful_executions']}")
                    self.stdout.write(f"Total Notifications: {analytics['total_notifications']}")
                    self.stdout.write(f"Unread Notifications: {analytics['unread_notifications']}")
                    self.stdout.write(f"Recent Executions (7 days): {analytics['recent_executions']}")
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "DRY RUN: Would check for inactive files and storage thresholds"
                    )
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error running AI workflows: {str(e)}")
            )
            raise e
        
        self.stdout.write(
            self.style.SUCCESS("AI workflow scheduler completed successfully")
        )
