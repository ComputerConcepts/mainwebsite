"""
Django management command to setup default AI workflow templates
Usage: python manage.py setup_ai_workflows
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import Employee, AIWorkflowRule
from pages.ai_workflow_service import get_ai_workflow_service


class Command(BaseCommand):
    help = 'Setup default AI workflow templates and rules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-user',
            type=str,
            help='Admin username to assign as creator of default workflows',
            default='admin'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate workflows even if they exist',
        )
    
    def handle(self, *args, **options):
        admin_username = options['admin_user']
        force = options['force']
        
        self.stdout.write("Setting up default AI workflow templates...")
        
        try:
            # Get admin user
            try:
                admin_user = User.objects.get(username=admin_username)
                admin_employee = Employee.objects.get(user=admin_user)
            except (User.DoesNotExist, Employee.DoesNotExist):
                self.stdout.write(
                    self.style.ERROR(
                        f"Admin user '{admin_username}' or corresponding Employee not found. "
                        "Please create an admin user first or specify a different username."
                    )
                )
                return
            
            ai_service = get_ai_workflow_service()
            
            # Default workflow templates
            default_workflows = [
                {
                    'name': 'Auto-categorize uploaded files',
                    'description': 'Automatically categorize and organize files based on content',
                    'trigger': 'file_upload',
                    'conditions': {'file_types': ['pdf', 'doc', 'docx', 'txt']},
                    'actions': [
                        {'type': 'analyze_content', 'params': {}},
                        {'type': 'create_folder_if_needed', 'params': {}},
                        {'type': 'move_to_category_folder', 'params': {}},
                        {'type': 'add_tags', 'params': {}}
                    ]
                },
                {
                    'name': 'Detect and notify about duplicates',
                    'description': 'Identify potential duplicate files and notify user',
                    'trigger': 'file_upload',
                    'conditions': {'check_duplicates': True},
                    'actions': [
                        {'type': 'scan_for_duplicates', 'params': {}},
                        {'type': 'notify_if_duplicates', 'params': {'priority': 'medium'}}
                    ]
                },
                {
                    'name': 'Monitor storage usage',
                    'description': 'Alert when storage usage reaches certain thresholds',
                    'trigger': 'threshold_reached',
                    'conditions': {'storage_threshold': 80},
                    'actions': [
                        {'type': 'send_storage_alert', 'params': {'priority': 'high'}},
                        {'type': 'suggest_cleanup', 'params': {}}
                    ]
                },
                {
                    'name': 'Archive inactive files',
                    'description': 'Identify and suggest archiving files not accessed for 90 days',
                    'trigger': 'schedule_based',
                    'conditions': {'schedule': 'weekly', 'inactive_days': 90},
                    'actions': [
                        {'type': 'find_inactive_files', 'params': {}},
                        {'type': 'suggest_archival', 'params': {'priority': 'low'}}
                    ]
                },
                {
                    'name': 'Collaboration reminders',
                    'description': 'Remind users about pending shared file responses',
                    'trigger': 'time_based',
                    'conditions': {'check_interval': 'daily'},
                    'actions': [
                        {'type': 'check_pending_collaborations', 'params': {}},
                        {'type': 'send_reminders', 'params': {'priority': 'medium'}}
                    ]
                },
                {
                    'name': 'Security monitoring',
                    'description': 'Monitor for suspicious file activities',
                    'trigger': 'user_action',
                    'conditions': {'monitor_actions': ['delete', 'share', 'download']},
                    'actions': [
                        {'type': 'analyze_activity_pattern', 'params': {}},
                        {'type': 'flag_suspicious_activity', 'params': {'priority': 'urgent'}}
                    ]
                },
                {
                    'name': 'Content quality assessment',
                    'description': 'Analyze uploaded documents for quality and suggest improvements',
                    'trigger': 'file_upload',
                    'conditions': {'file_types': ['doc', 'docx', 'pdf'], 'min_size': 1000},
                    'actions': [
                        {'type': 'analyze_content_quality', 'params': {}},
                        {'type': 'suggest_improvements', 'params': {'priority': 'low'}}
                    ]
                }
            ]
            
            created_count = 0
            updated_count = 0
            
            for workflow_data in default_workflows:
                # Check if workflow already exists
                existing = AIWorkflowRule.objects.filter(
                    name=workflow_data['name']
                ).first()
                
                if existing and not force:
                    self.stdout.write(f"  Skipping '{workflow_data['name']}' - already exists")
                    continue
                
                if existing and force:
                    # Update existing workflow
                    existing.description = workflow_data['description']
                    existing.trigger = workflow_data['trigger']
                    existing.conditions = workflow_data['conditions']
                    existing.actions = workflow_data['actions']
                    existing.enabled = True
                    existing.save()
                    updated_count += 1
                    self.stdout.write(f"  Updated '{workflow_data['name']}'")
                else:
                    # Create new workflow
                    ai_service.create_workflow_rule(
                        name=workflow_data['name'],
                        description=workflow_data['description'],
                        trigger=workflow_data['trigger'],
                        conditions=workflow_data['conditions'],
                        actions=workflow_data['actions'],
                        user=admin_employee
                    )
                    created_count += 1
                    self.stdout.write(f"  Created '{workflow_data['name']}'")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSetup completed: {created_count} created, {updated_count} updated"
                )
            )
            
            # Show current analytics
            analytics = ai_service.get_workflow_analytics()
            self.stdout.write(f"\nCurrent Status:")
            self.stdout.write(f"  Total Rules: {analytics['total_rules']}")
            self.stdout.write(f"  Active Rules: {analytics['active_rules']}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error setting up AI workflows: {str(e)}")
            )
            raise e
