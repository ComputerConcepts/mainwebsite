"""
Django Integration Service for AI Workflows
Connects AI workflow engine with Django models and views
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.contrib.auth.models import User

from .models import (
    Employee, FileDocument, FileFolder, FileActivity, FileShare,
    AIWorkflowRule, AIWorkflowExecution, AINotification, AINotificationPreference,
    AIFileAnalysis
)
from .ai_workflows import (
    AutomatedWorkflowEngine, SmartNotificationEngine, WorkflowTrigger, NotificationPriority
)
from .ai_file_analysis import AIFileAnalyzer


class AIWorkflowService:
    """Django service for managing AI workflows"""
    
    def __init__(self):
        self.workflow_engine = AutomatedWorkflowEngine()
        self.notification_engine = SmartNotificationEngine()
        self.file_analyzer = AIFileAnalyzer()
        self._load_existing_rules()
    
    def load_user_notification_preferences(self, user: Employee):
        """Ensure notification engine is aware of a user's stored preferences"""
        try:
            prefs = user.notification_preferences
        except AINotificationPreference.DoesNotExist:
            # No stored preferences yet - register defaults so engine can use them
            self.notification_engine.set_user_preferences(
                user.user.username,
                {
                    'email_notifications': True,
                    'push_notifications': True,
                    'priority_threshold': 'medium',
                    'quiet_hours': {'start': '22:00', 'end': '08:00'},
                    'categories': {
                        'security': True,
                        'storage_management': True,
                        'collaboration': True,
                        'duplicate_detection': False,
                        'content_quality': False,
                        'file_management': True,
                        'workflow': True,
                    },
                }
            )
            return
        
        quiet_start = prefs.quiet_hours_start.strftime('%H:%M') if prefs.quiet_hours_start else '22:00'
        quiet_end = prefs.quiet_hours_end.strftime('%H:%M') if prefs.quiet_hours_end else '08:00'
        
        self.notification_engine.set_user_preferences(
            user.user.username,
            {
                'email_notifications': prefs.email_notifications,
                'push_notifications': prefs.push_notifications,
                'priority_threshold': prefs.priority_threshold,
                'quiet_hours': {
                    'start': quiet_start,
                    'end': quiet_end,
                },
                'categories': prefs.get_category_preferences(),
            }
        )
    
    def _load_existing_rules(self):
        """Load existing workflow rules from database"""
        try:
            for rule_model in AIWorkflowRule.objects.filter(enabled=True):
                self.workflow_engine.workflow_rules[str(rule_model.id)] = self._model_to_workflow_rule(rule_model)
        except Exception as e:
            print(f"Error loading workflow rules: {e}")
    
    def _model_to_workflow_rule(self, rule_model: AIWorkflowRule):
        """Convert Django model to workflow rule"""
        from .ai_workflows import WorkflowRule, WorkflowTrigger
        
        return WorkflowRule(
            id=str(rule_model.id),
            name=rule_model.name,
            description=rule_model.description,
            trigger=WorkflowTrigger(rule_model.trigger),
            conditions=rule_model.conditions,
            actions=rule_model.actions,
            enabled=rule_model.enabled,
            created_at=rule_model.created_at.isoformat(),
            last_executed=rule_model.last_executed.isoformat() if rule_model.last_executed else None,
            execution_count=rule_model.execution_count
        )
    
    def handle_file_upload(self, file_document: FileDocument, user: Employee) -> Dict:
        """Handle AI workflow triggers for file upload"""
        try:
            # Prepare context for workflow processing
            context = self._prepare_file_context(file_document, user, 'upload')
            
            # Trigger AI analysis
            analysis_result = self._analyze_file(file_document)
            context.update(analysis_result)
            
            # Process workflow triggers
            executed_workflows = self.workflow_engine.process_trigger(
                WorkflowTrigger.FILE_UPLOAD, context
            )
            
            # Save execution results to database
            self._save_workflow_executions(executed_workflows, file_document, user)
            
            # Process any generated notifications
            self._process_notifications(executed_workflows, user)
            
            return {
                'success': True,
                'executed_workflows': len(executed_workflows),
                'notifications_created': sum(len(w['execution_result'].get('notifications_created', [])) for w in executed_workflows),
                'analysis_completed': analysis_result.get('analysis_completed', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'executed_workflows': 0,
                'notifications_created': 0
            }
    
    def handle_file_modification(self, file_document: FileDocument, user: Employee) -> Dict:
        """Handle AI workflow triggers for file modification"""
        context = self._prepare_file_context(file_document, user, 'modify')
        
        executed_workflows = self.workflow_engine.process_trigger(
            WorkflowTrigger.FILE_MODIFIED, context
        )
        
        self._save_workflow_executions(executed_workflows, file_document, user)
        self._process_notifications(executed_workflows, user)
        
        return {
            'success': True,
            'executed_workflows': len(executed_workflows)
        }
    
    def handle_file_sharing(self, file_document: FileDocument, shared_by: Employee, shared_with: Employee) -> Dict:
        """Handle AI workflow triggers for file sharing"""
        context = self._prepare_file_context(file_document, shared_by, 'share')
        context.update({
            'shared_with_user': shared_with.user.username,
            'shared_with_email': shared_with.user.email,
            'sharing_date': timezone.now().isoformat()
        })
        
        executed_workflows = self.workflow_engine.process_trigger(
            WorkflowTrigger.FILE_SHARED, context
        )
        
        self._save_workflow_executions(executed_workflows, file_document, shared_by)
        self._process_notifications(executed_workflows, shared_by)
        
        return {
            'success': True,
            'executed_workflows': len(executed_workflows)
        }
    
    def handle_storage_threshold(self, user: Employee, usage_percentage: float) -> Dict:
        """Handle storage threshold workflow triggers"""
        context = {
            'user_id': user.user.username,
            'storage_usage_percent': usage_percentage,
            'storage_used_bytes': user.storage_used,
            'storage_quota_bytes': user.storage_quota,
            'threshold_exceeded': usage_percentage >= 80
        }
        
        executed_workflows = self.workflow_engine.process_trigger(
            WorkflowTrigger.THRESHOLD_REACHED, context
        )
        
        self._save_workflow_executions(executed_workflows, None, user)
        self._process_notifications(executed_workflows, user)
        
        return {
            'success': True,
            'executed_workflows': len(executed_workflows)
        }
    
    def handle_user_action(self, action: str, file_document: FileDocument, user: Employee, **kwargs) -> Dict:
        """Handle user action workflow triggers"""
        context = self._prepare_file_context(file_document, user, action)
        context.update(kwargs)
        
        # Add activity tracking
        context.update({
            'files_deleted_today': self._get_user_activity_count(user, 'delete', days=1),
            'files_downloaded_hour': self._get_user_activity_count(user, 'download', hours=1),
            'files_shared_week': self._get_user_activity_count(user, 'share', days=7)
        })
        
        executed_workflows = self.workflow_engine.process_trigger(
            WorkflowTrigger.USER_ACTION, context
        )
        
        self._save_workflow_executions(executed_workflows, file_document, user)
        self._process_notifications(executed_workflows, user)
        
        return {
            'success': True,
            'executed_workflows': len(executed_workflows)
        }
    
    def _prepare_file_context(self, file_document: FileDocument, user: Employee, action: str) -> Dict:
        """Prepare context data for workflow processing"""
        context = {
            'action': action,
            'user_id': user.user.username,
            'uploaded_by': user.user.username,
            'filename': file_document.name,
            'file_size': file_document.file_size,
            'file_type': file_document.file_type,
            'mime_type': file_document.mime_type,
            'current_file_id': str(file_document.id),
            'upload_time': file_document.created_at.isoformat(),
            'last_accessed': file_document.last_accessed.isoformat() if file_document.last_accessed else None,
            'folder_name': file_document.folder.name if file_document.folder else 'Root',
            'is_shared': file_document.shared_with.exists(),
            'download_count': file_document.download_count,
            'tags': file_document.tags.split(',') if file_document.tags else []
        }
        
        # Add file hash for duplicate detection
        if file_document.file and os.path.exists(file_document.file.path):
            try:
                context['file_hash'] = self._calculate_file_hash(file_document.file.path)
            except:
                context['file_hash'] = ''
        
        return context
    
    def _analyze_file(self, file_document: FileDocument) -> Dict:
        """Perform AI analysis on the file"""
        try:
            # Get or create AI analysis record
            ai_analysis, created = AIFileAnalysis.objects.get_or_create(
                document=file_document,
                defaults={'analysis_completed': False}
            )
            
            if ai_analysis.analysis_completed and not created:
                # Return existing analysis
                return self._format_analysis_result(ai_analysis)
            
            # Perform analysis
            if file_document.file and os.path.exists(file_document.file.path):
                start_time = timezone.now()
                
                # Use AI file analyzer
                analysis_result = self.file_analyzer.analyze_file(file_document.file.path)
                
                # Update AI analysis record
                processing_time = (timezone.now() - start_time).total_seconds() * 1000
                
                ai_analysis.content_type = analysis_result.get('file_info', {}).get('type', '')
                ai_analysis.language = analysis_result.get('language', '')
                ai_analysis.word_count = analysis_result.get('word_count')
                ai_analysis.page_count = analysis_result.get('page_count')
                ai_analysis.category = analysis_result.get('category', '')
                ai_analysis.key_topics = analysis_result.get('key_topics', [])
                ai_analysis.entities = analysis_result.get('entities', [])
                ai_analysis.sentiment_score = analysis_result.get('sentiment', {}).get('compound', 0)
                ai_analysis.sentiment_label = analysis_result.get('sentiment', {}).get('label', '')
                ai_analysis.readability_score = analysis_result.get('readability_score', 0)
                ai_analysis.complexity_score = analysis_result.get('complexity_score', 0)
                ai_analysis.quality_score = analysis_result.get('content_quality', {}).get('overall_score', 0)
                ai_analysis.contains_sensitive_info = analysis_result.get('security_check', {}).get('has_sensitive_info', False)
                ai_analysis.sensitive_info_types = analysis_result.get('security_check', {}).get('sensitive_types', [])
                ai_analysis.security_risk_level = analysis_result.get('security_check', {}).get('risk_level', 'low')
                ai_analysis.has_images = analysis_result.get('structure', {}).get('has_images', False)
                ai_analysis.has_tables = analysis_result.get('structure', {}).get('has_tables', False)
                ai_analysis.has_links = analysis_result.get('structure', {}).get('has_links', False)
                ai_analysis.ai_recommendations = analysis_result.get('recommendations', [])
                ai_analysis.suggested_tags = analysis_result.get('suggested_tags', [])
                ai_analysis.suggested_category = analysis_result.get('suggested_category', '')
                ai_analysis.mark_completed(int(processing_time))
                
                return self._format_analysis_result(ai_analysis, analysis_result)
            else:
                ai_analysis.error_message = "File not found or inaccessible"
                ai_analysis.save()
                return {'analysis_completed': False, 'error': 'File not accessible'}
                
        except Exception as e:
            return {'analysis_completed': False, 'error': str(e)}
    
    def _format_analysis_result(self, ai_analysis: AIFileAnalysis, raw_result: Dict = None) -> Dict:
        """Format AI analysis result for workflow context"""
        result = {
            'analysis_completed': ai_analysis.analysis_completed,
            'category': ai_analysis.category,
            'key_topics': ai_analysis.key_topics,
            'entities': ai_analysis.entities,
            'sentiment_score': ai_analysis.sentiment_score,
            'readability_score': ai_analysis.readability_score,
            'complexity_score': ai_analysis.complexity_score,
            'content_quality': {
                'overall_score': ai_analysis.quality_score
            },
            'security_check': {
                'has_sensitive_info': ai_analysis.contains_sensitive_info,
                'sensitive_types': ai_analysis.sensitive_info_types,
                'risk_level': ai_analysis.security_risk_level
            },
            'recommendations': ai_analysis.ai_recommendations,
            'suggested_tags': ai_analysis.suggested_tags
        }
        
        if raw_result:
            result['file_analysis'] = raw_result
        
        return result
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""
    
    def _get_user_activity_count(self, user: Employee, action: str, days: int = None, hours: int = None) -> int:
        """Get count of user activities within time period"""
        try:
            query = FileActivity.objects.filter(user=user, action=action)
            
            if days:
                since_date = timezone.now() - timedelta(days=days)
                query = query.filter(created_at__gte=since_date)
            elif hours:
                since_date = timezone.now() - timedelta(hours=hours)
                query = query.filter(created_at__gte=since_date)
            
            return query.count()
        except:
            return 0
    
    def _save_workflow_executions(self, executed_workflows: List[Dict], 
                                 file_document: Optional[FileDocument], user: Employee):
        """Save workflow execution results to database"""
        for workflow_data in executed_workflows:
            try:
                rule_id = workflow_data['rule_id']
                execution_result = workflow_data['execution_result']
                
                # Get the workflow rule
                try:
                    rule_model = AIWorkflowRule.objects.get(id=rule_id)
                except AIWorkflowRule.DoesNotExist:
                    continue
                
                # Create execution record
                execution = AIWorkflowExecution.objects.create(
                    workflow_rule=rule_model,
                    triggered_by=user,
                    document=file_document,
                    status='completed' if not execution_result.get('errors') else 'failed',
                    context_data=workflow_data.get('context', {}),
                    result_data=execution_result,
                    error_message='; '.join([e.get('error', '') for e in execution_result.get('errors', [])]),
                    completed_at=timezone.now(),
                    execution_time_ms=execution_result.get('execution_time_ms', 100)
                )
                
                # Update rule statistics
                rule_model.execution_count += 1
                rule_model.last_executed = timezone.now()
                rule_model.save(update_fields=['execution_count', 'last_executed'])
                
            except Exception as e:
                print(f"Error saving workflow execution: {e}")
    
    def _process_notifications(self, executed_workflows: List[Dict], user: Employee):
        """Process and save notifications generated by workflows"""
        # Ensure the notification engine is aware of the user's current preferences
        self.load_user_notification_preferences(user)
        
        for workflow_data in executed_workflows:
            execution_result = workflow_data['execution_result']
            
            for notification_id in execution_result.get('notifications_created', []):
                try:
                    # Find the notification in the workflow engine
                    notification = None
                    for notif in self.workflow_engine.notification_queue:
                        if notif.id == notification_id:
                            notification = notif
                            break
                    
                    if notification:
                        # Check if notification should be sent
                        send_decision = self.notification_engine.should_send_notification(notification)
                        
                        if send_decision['send']:
                            # Create Django notification
                            ai_notification = AINotification.objects.create(
                                title=notification.title,
                                message=notification.message,
                                priority=notification.priority.value,
                                category=notification.category,
                                user=user,
                                data=notification.data,
                                workflow_execution_id=workflow_data.get('execution_id')
                            )
                            
                            # Send notification through configured channels
                            self._send_notification(ai_notification, send_decision['channels'])
                        
                except Exception as e:
                    print(f"Error processing notification: {e}")
    
    def _send_notification(self, notification: AINotification, channels: List[str]):
        """Send notification through specified channels"""
        # This would integrate with your notification system
        # For now, we'll just mark it as created
        pass
    
    def create_workflow_rule(self, name: str, description: str, trigger: str, 
                           conditions: Dict, actions: List[Dict], user: Employee) -> AIWorkflowRule:
        """Create a new workflow rule"""
        rule = AIWorkflowRule.objects.create(
            name=name,
            description=description,
            trigger=trigger,
            conditions=conditions,
            actions=actions,
            created_by=user
        )
        
        # Add to workflow engine
        self.workflow_engine.workflow_rules[str(rule.id)] = self._model_to_workflow_rule(rule)
        
        return rule
    
    def get_user_notifications(self, user: Employee, unread_only: bool = False) -> List[AINotification]:
        """Get notifications for a user"""
        query = AINotification.objects.filter(user=user)
        
        if unread_only:
            query = query.filter(is_read=False)
        
        return query.order_by('-created_at')[:50]  # Last 50 notifications
    
    def get_workflow_analytics(self, user: Employee = None) -> Dict:
        """Get workflow analytics"""
        analytics = {
            'total_rules': AIWorkflowRule.objects.count(),
            'active_rules': AIWorkflowRule.objects.filter(enabled=True).count(),
            'total_executions': AIWorkflowExecution.objects.count(),
            'successful_executions': AIWorkflowExecution.objects.filter(status='completed').count(),
            'total_notifications': AINotification.objects.count(),
            'unread_notifications': AINotification.objects.filter(is_read=False).count(),
        }
        
        if user:
            analytics.update({
                'user_notifications': AINotification.objects.filter(user=user).count(),
                'user_unread_notifications': AINotification.objects.filter(user=user, is_read=False).count(),
                'user_workflow_executions': AIWorkflowExecution.objects.filter(triggered_by=user).count(),
            })
        
        # Recent activity
        recent_executions = AIWorkflowExecution.objects.filter(
            started_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        analytics['recent_executions'] = recent_executions
        
        return analytics
    
    def suggest_workflow_optimizations(self, user: Employee) -> List[Dict]:
        """Suggest workflow optimizations for a user"""
        # Get user's recent activities
        recent_activities = FileActivity.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).values('action', 'document__name', 'created_at')
        
        # Convert to format expected by workflow engine
        activities = []
        for activity in recent_activities:
            activities.append({
                'action': activity['action'],
                'filename': activity['document__name'] or '',
                'timestamp': activity['created_at'].isoformat()
            })
        
        return self.workflow_engine.suggest_workflow_optimizations(activities)
    
    def run_scheduled_workflows(self):
        """Run scheduled workflow checks (called by cron job)"""
        executed_count = 0
        
        try:
            # Check for inactive files
            inactive_threshold = timezone.now() - timedelta(days=90)
            inactive_files = FileDocument.objects.filter(
                last_accessed__lt=inactive_threshold
            ).select_related('uploaded_by')
            
            for file_doc in inactive_files[:100]:  # Process in batches
                context = self._prepare_file_context(file_doc, file_doc.uploaded_by, 'schedule_check')
                context['last_accessed'] = file_doc.last_accessed.isoformat() if file_doc.last_accessed else None
                
                executed_workflows = self.workflow_engine.process_trigger(
                    WorkflowTrigger.SCHEDULE_BASED, context
                )
                
                if executed_workflows:
                    self._save_workflow_executions(executed_workflows, file_doc, file_doc.uploaded_by)
                    self._process_notifications(executed_workflows, file_doc.uploaded_by)
                    executed_count += len(executed_workflows)
            
            # Check storage thresholds
            for employee in Employee.objects.all():
                usage_percentage = employee.get_storage_percentage()
                if usage_percentage >= 80:  # 80% threshold
                    self.handle_storage_threshold(employee, usage_percentage)
                    executed_count += 1
            
        except Exception as e:
            print(f"Error running scheduled workflows: {e}")
        
        return executed_count


# Global service instance
ai_workflow_service = AIWorkflowService()


def get_ai_workflow_service() -> AIWorkflowService:
    """Get the global AI workflow service instance"""
    return ai_workflow_service
