"""
AI-Powered Automated Workflows and Smart Notifications Engine
Automates repetitive tasks and provides intelligent notifications
"""

import os
import json
from typing import Dict, List, Tuple, Optional, Callable
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
from enum import Enum


class WorkflowTrigger(Enum):
    FILE_UPLOAD = "file_upload"
    FILE_MODIFIED = "file_modified"
    FILE_SHARED = "file_shared"
    SCHEDULE_BASED = "schedule_based"
    THRESHOLD_REACHED = "threshold_reached"
    USER_ACTION = "user_action"
    TIME_BASED = "time_based"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class WorkflowRule:
    id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    conditions: Dict
    actions: List[Dict]
    enabled: bool = True
    created_at: str = None
    last_executed: str = None
    execution_count: int = 0


@dataclass
class SmartNotification:
    id: str
    title: str
    message: str
    priority: NotificationPriority
    category: str
    user_id: str
    data: Dict
    created_at: str
    read: bool = False
    action_taken: bool = False


class AutomatedWorkflowEngine:
    """AI-powered workflow automation engine"""
    
    def __init__(self):
        self.workflow_rules = {}
        self.notification_queue = []
        self.execution_history = []
        self.user_preferences = {}
        self.template_library = self._load_workflow_templates()
        
    def _load_workflow_templates(self) -> Dict:
        """Load predefined workflow templates"""
        return {
            'auto_categorize_files': {
                'name': 'Auto-categorize uploaded files',
                'description': 'Automatically categorize and organize files based on content',
                'trigger': WorkflowTrigger.FILE_UPLOAD,
                'conditions': {'file_types': ['pdf', 'doc', 'docx', 'txt']},
                'actions': [
                    {'type': 'analyze_content', 'params': {}},
                    {'type': 'create_folder_if_needed', 'params': {}},
                    {'type': 'move_to_category_folder', 'params': {}},
                    {'type': 'add_tags', 'params': {}}
                ]
            },
            'duplicate_detection': {
                'name': 'Detect and notify about duplicates',
                'description': 'Identify potential duplicate files and notify user',
                'trigger': WorkflowTrigger.FILE_UPLOAD,
                'conditions': {'check_duplicates': True},
                'actions': [
                    {'type': 'scan_for_duplicates', 'params': {}},
                    {'type': 'notify_if_duplicates', 'params': {'priority': 'medium'}}
                ]
            },
            'storage_monitoring': {
                'name': 'Monitor storage usage',
                'description': 'Alert when storage usage reaches certain thresholds',
                'trigger': WorkflowTrigger.THRESHOLD_REACHED,
                'conditions': {'storage_threshold': 80},
                'actions': [
                    {'type': 'send_storage_alert', 'params': {'priority': 'high'}},
                    {'type': 'suggest_cleanup', 'params': {}}
                ]
            },
            'inactive_file_archival': {
                'name': 'Archive inactive files',
                'description': 'Identify and suggest archiving files not accessed for 90 days',
                'trigger': WorkflowTrigger.SCHEDULE_BASED,
                'conditions': {'schedule': 'weekly', 'inactive_days': 90},
                'actions': [
                    {'type': 'find_inactive_files', 'params': {}},
                    {'type': 'suggest_archival', 'params': {'priority': 'low'}}
                ]
            },
            'collaboration_reminders': {
                'name': 'Collaboration reminders',
                'description': 'Remind users about pending shared file responses',
                'trigger': WorkflowTrigger.TIME_BASED,
                'conditions': {'check_interval': 'daily'},
                'actions': [
                    {'type': 'check_pending_collaborations', 'params': {}},
                    {'type': 'send_reminders', 'params': {'priority': 'medium'}}
                ]
            },
            'security_monitoring': {
                'name': 'Security monitoring',
                'description': 'Monitor for suspicious file activities',
                'trigger': WorkflowTrigger.USER_ACTION,
                'conditions': {'monitor_actions': ['delete', 'share', 'download']},
                'actions': [
                    {'type': 'analyze_activity_pattern', 'params': {}},
                    {'type': 'flag_suspicious_activity', 'params': {'priority': 'urgent'}}
                ]
            },
            'content_quality_check': {
                'name': 'Content quality assessment',
                'description': 'Analyze uploaded documents for quality and suggest improvements',
                'trigger': WorkflowTrigger.FILE_UPLOAD,
                'conditions': {'file_types': ['doc', 'docx', 'pdf'], 'min_size': 1000},
                'actions': [
                    {'type': 'analyze_content_quality', 'params': {}},
                    {'type': 'suggest_improvements', 'params': {'priority': 'low'}}
                ]
            }
        }
    
    def create_workflow_rule(self, rule_data: Dict) -> str:
        """Create a new workflow rule"""
        rule_id = f"rule_{len(self.workflow_rules) + 1}_{int(datetime.now().timestamp())}"
        
        rule = WorkflowRule(
            id=rule_id,
            name=rule_data.get('name', 'Unnamed Rule'),
            description=rule_data.get('description', ''),
            trigger=WorkflowTrigger(rule_data.get('trigger')),
            conditions=rule_data.get('conditions', {}),
            actions=rule_data.get('actions', []),
            created_at=datetime.now().isoformat()
        )
        
        self.workflow_rules[rule_id] = rule
        return rule_id
    
    def create_from_template(self, template_name: str, user_id: str, custom_params: Dict = None) -> str:
        """Create workflow rule from template"""
        if template_name not in self.template_library:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.template_library[template_name].copy()
        
        # Apply custom parameters if provided
        if custom_params:
            template.update(custom_params)
        
        rule_data = {
            'name': template['name'],
            'description': template['description'],
            'trigger': template['trigger'].value,
            'conditions': template['conditions'],
            'actions': template['actions'],
            'user_id': user_id
        }
        
        return self.create_workflow_rule(rule_data)
    
    def process_trigger(self, trigger: WorkflowTrigger, context: Dict) -> List[Dict]:
        """Process workflow triggers and execute matching rules"""
        executed_workflows = []
        
        for rule_id, rule in self.workflow_rules.items():
            if not rule.enabled or rule.trigger != trigger:
                continue
            
            # Check if conditions are met
            if self._evaluate_conditions(rule.conditions, context):
                execution_result = self._execute_workflow(rule, context)
                executed_workflows.append({
                    'rule_id': rule_id,
                    'rule_name': rule.name,
                    'execution_result': execution_result,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Update rule execution stats
                rule.last_executed = datetime.now().isoformat()
                rule.execution_count += 1
        
        return executed_workflows
    
    def _evaluate_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Evaluate if workflow conditions are met"""
        for condition_key, condition_value in conditions.items():
            
            if condition_key == 'file_types':
                filename = context.get('filename', '')
                if filename:
                    file_ext = filename.split('.')[-1].lower()
                    if file_ext not in condition_value:
                        return False
            
            elif condition_key == 'storage_threshold':
                storage_usage = context.get('storage_usage_percent', 0)
                if storage_usage < condition_value:
                    return False
            
            elif condition_key == 'min_size':
                file_size = context.get('file_size', 0)
                if file_size < condition_value:
                    return False
            
            elif condition_key == 'inactive_days':
                last_accessed = context.get('last_accessed')
                if last_accessed:
                    days_inactive = (datetime.now() - datetime.fromisoformat(last_accessed)).days
                    if days_inactive < condition_value:
                        return False
            
            elif condition_key == 'check_duplicates':
                if not condition_value:
                    return False
            
            elif condition_key == 'monitor_actions':
                action = context.get('action', '')
                if action not in condition_value:
                    return False
        
        return True
    
    def _execute_workflow(self, rule: WorkflowRule, context: Dict) -> Dict:
        """Execute workflow actions"""
        execution_result = {
            'rule_id': rule.id,
            'actions_executed': [],
            'notifications_created': [],
            'errors': []
        }
        
        for action in rule.actions:
            try:
                result = self._execute_action(action, context)
                execution_result['actions_executed'].append({
                    'action_type': action['type'],
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                # If action created a notification, add it to the queue
                if result.get('notification'):
                    notification = self._create_notification(result['notification'], context)
                    execution_result['notifications_created'].append(notification.id)
                
            except Exception as e:
                execution_result['errors'].append({
                    'action_type': action['type'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Store execution history
        self.execution_history.append(execution_result)
        
        return execution_result
    
    def _execute_action(self, action: Dict, context: Dict) -> Dict:
        """Execute a specific workflow action"""
        action_type = action['type']
        params = action.get('params', {})
        
        if action_type == 'analyze_content':
            return self._action_analyze_content(context, params)
        
        elif action_type == 'create_folder_if_needed':
            return self._action_create_folder(context, params)
        
        elif action_type == 'move_to_category_folder':
            return self._action_move_to_category(context, params)
        
        elif action_type == 'add_tags':
            return self._action_add_tags(context, params)
        
        elif action_type == 'scan_for_duplicates':
            return self._action_scan_duplicates(context, params)
        
        elif action_type == 'notify_if_duplicates':
            return self._action_notify_duplicates(context, params)
        
        elif action_type == 'send_storage_alert':
            return self._action_send_storage_alert(context, params)
        
        elif action_type == 'suggest_cleanup':
            return self._action_suggest_cleanup(context, params)
        
        elif action_type == 'find_inactive_files':
            return self._action_find_inactive_files(context, params)
        
        elif action_type == 'suggest_archival':
            return self._action_suggest_archival(context, params)
        
        elif action_type == 'check_pending_collaborations':
            return self._action_check_collaborations(context, params)
        
        elif action_type == 'send_reminders':
            return self._action_send_reminders(context, params)
        
        elif action_type == 'analyze_activity_pattern':
            return self._action_analyze_activity(context, params)
        
        elif action_type == 'flag_suspicious_activity':
            return self._action_flag_suspicious(context, params)
        
        elif action_type == 'analyze_content_quality':
            return self._action_analyze_quality(context, params)
        
        elif action_type == 'suggest_improvements':
            return self._action_suggest_improvements(context, params)
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _action_analyze_content(self, context: Dict, params: Dict) -> Dict:
        """Analyze file content for categorization"""
        filename = context.get('filename', '')
        file_analysis = context.get('file_analysis', {})
        
        category = file_analysis.get('category', 'general')
        topics = file_analysis.get('key_topics', [])
        
        return {
            'status': 'completed',
            'category': category,
            'topics': topics,
            'message': f'Content analyzed for {filename}'
        }
    
    def _action_create_folder(self, context: Dict, params: Dict) -> Dict:
        """Create folder if needed for file organization"""
        category = context.get('category', 'general')
        
        # Simulate folder creation (would integrate with actual file system)
        folder_name = f"{category.title()} Documents"
        
        return {
            'status': 'completed',
            'folder_created': folder_name,
            'message': f'Folder "{folder_name}" prepared for organization'
        }
    
    def _action_move_to_category(self, context: Dict, params: Dict) -> Dict:
        """Move file to appropriate category folder"""
        filename = context.get('filename', '')
        category = context.get('category', 'general')
        
        return {
            'status': 'completed',
            'action_taken': f'Move {filename} to {category} folder',
            'message': f'File organized into {category} category'
        }
    
    def _action_add_tags(self, context: Dict, params: Dict) -> Dict:
        """Add intelligent tags to file"""
        topics = context.get('topics', [])
        category = context.get('category', 'general')
        
        tags = [category] + topics[:3]  # Category + top 3 topics
        
        return {
            'status': 'completed',
            'tags_added': tags,
            'message': f'Added {len(tags)} intelligent tags'
        }
    
    def _action_scan_duplicates(self, context: Dict, params: Dict) -> Dict:
        """Scan for potential duplicate files"""
        filename = context.get('filename', '')
        file_size = context.get('file_size', 0)
        file_hash = context.get('file_hash', '')
        uploaded_by = context.get('uploaded_by')
        
        duplicates_found = []
        
        # Real duplicate detection using Django models
        try:
            from django.apps import apps
            FileDocument = apps.get_model('pages', 'FileDocument')
            Employee = apps.get_model('pages', 'Employee')
            
            # Get the current user's employee record
            current_user = None
            if uploaded_by:
                try:
                    current_user = Employee.objects.get(user__username=uploaded_by)
                except Employee.DoesNotExist:
                    pass
            
            # Find potential duplicates by different criteria
            potential_duplicates = []
            
            # 1. Exact filename match (different folders)
            if current_user:
                same_name_files = FileDocument.objects.filter(
                    name=filename,
                    uploaded_by=current_user
                ).exclude(id=context.get('current_file_id'))
                
                for file_doc in same_name_files:
                    potential_duplicates.append({
                        'id': str(file_doc.id),
                        'filename': file_doc.name,
                        'similarity': 90,
                        'reason': 'exact filename match',
                        'file_size': file_doc.file_size,
                        'folder': file_doc.folder.name if file_doc.folder else 'Root',
                        'created_at': file_doc.created_at.isoformat()
                    })
            
            # 2. Same file size and similar name
            if file_size > 0:
                size_range_files = FileDocument.objects.filter(
                    file_size=file_size
                ).exclude(id=context.get('current_file_id'))
                
                if current_user:
                    size_range_files = size_range_files.filter(uploaded_by=current_user)
                
                for file_doc in size_range_files[:10]:  # Limit to 10 results
                    # Calculate name similarity
                    name_similarity = self._calculate_filename_similarity(filename, file_doc.name)
                    if name_similarity > 0.7:  # 70% similarity threshold
                        potential_duplicates.append({
                            'id': str(file_doc.id),
                            'filename': file_doc.name,
                            'similarity': int(name_similarity * 100),
                            'reason': 'same size + similar name',
                            'file_size': file_doc.file_size,
                            'folder': file_doc.folder.name if file_doc.folder else 'Root',
                            'created_at': file_doc.created_at.isoformat()
                        })
            
            # 3. Files with 'copy' or 'duplicate' patterns
            base_filename = filename.lower()
            for pattern in ['copy', 'duplicate', '(1)', '(2)', '(3)', '_copy', '_duplicate']:
                if pattern in base_filename:
                    clean_name = base_filename.replace(pattern, '').strip()
                    similar_files = FileDocument.objects.filter(
                        name__icontains=clean_name
                    ).exclude(id=context.get('current_file_id'))
                    
                    if current_user:
                        similar_files = similar_files.filter(uploaded_by=current_user)
                    
                    for file_doc in similar_files[:5]:  # Limit results
                        potential_duplicates.append({
                            'id': str(file_doc.id),
                            'filename': file_doc.name,
                            'similarity': 85,
                            'reason': 'copy/duplicate pattern detected',
                            'file_size': file_doc.file_size,
                            'folder': file_doc.folder.name if file_doc.folder else 'Root',
                            'created_at': file_doc.created_at.isoformat()
                        })
                    break
            
            # Remove duplicates and sort by similarity
            seen_ids = set()
            for duplicate in potential_duplicates:
                if duplicate['id'] not in seen_ids:
                    duplicates_found.append(duplicate)
                    seen_ids.add(duplicate['id'])
            
            # Sort by similarity score
            duplicates_found.sort(key=lambda x: x['similarity'], reverse=True)
            duplicates_found = duplicates_found[:5]  # Top 5 matches
            
        except Exception as e:
            # Fallback to simple pattern matching if Django models aren't available
            if 'copy' in filename.lower() or 'duplicate' in filename.lower():
                duplicates_found.append({
                    'filename': filename.replace('copy', '').replace('duplicate', '').strip(),
                    'similarity': 95,
                    'reason': 'filename similarity',
                    'file_size': file_size,
                    'folder': 'Unknown',
                    'created_at': context.get('upload_time', '')
                })
        
        return {
            'status': 'completed',
            'duplicates_found': duplicates_found,
            'scan_count': len(duplicates_found),
            'message': f'Scanned for duplicates of {filename} - found {len(duplicates_found)} potential matches'
        }
    
    def _calculate_filename_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two filenames"""
        import difflib
        
        # Remove extensions for comparison
        name1_base = name1.rsplit('.', 1)[0] if '.' in name1 else name1
        name2_base = name2.rsplit('.', 1)[0] if '.' in name2 else name2
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, name1_base.lower(), name2_base.lower()).ratio()
        return similarity
    
    def _action_notify_duplicates(self, context: Dict, params: Dict) -> Dict:
        """Send notification about potential duplicates"""
        duplicates = context.get('duplicates_found', [])
        
        if duplicates:
            return {
                'status': 'completed',
                'notification': {
                    'title': 'Potential Duplicate Files Detected',
                    'message': f'Found {len(duplicates)} potential duplicate files. Review to avoid redundancy.',
                    'priority': params.get('priority', 'medium'),
                    'category': 'duplicate_detection',
                    'data': {'duplicates': duplicates}
                }
            }
        
        return {
            'status': 'completed',
            'message': 'No duplicates found'
        }
    
    def _action_send_storage_alert(self, context: Dict, params: Dict) -> Dict:
        """Send storage usage alert"""
        storage_usage = context.get('storage_usage_percent', 0)
        
        return {
            'status': 'completed',
            'notification': {
                'title': 'Storage Usage Alert',
                'message': f'Storage is {storage_usage}% full. Consider cleaning up or upgrading.',
                'priority': params.get('priority', 'high'),
                'category': 'storage_management',
                'data': {'usage_percent': storage_usage}
            }
        }
    
    def _action_suggest_cleanup(self, context: Dict, params: Dict) -> Dict:
        """Suggest cleanup actions"""
        return {
            'status': 'completed',
            'suggestions': [
                'Delete files in Trash folder',
                'Archive files older than 6 months',
                'Compress large image files',
                'Remove duplicate files'
            ],
            'message': 'Generated cleanup suggestions'
        }
    
    def _action_find_inactive_files(self, context: Dict, params: Dict) -> Dict:
        """Find files that haven't been accessed recently"""
        inactive_days = params.get('inactive_days', 90)
        
        # Mock inactive files (would integrate with actual file system)
        inactive_files = [
            {'filename': 'old_document.pdf', 'last_accessed': '2024-01-15', 'size_gb': 0.5},
            {'filename': 'archived_presentation.pptx', 'last_accessed': '2024-02-10', 'size_gb': 0.3}
        ]
        
        return {
            'status': 'completed',
            'inactive_files': inactive_files,
            'count': len(inactive_files),
            'total_size_gb': sum(f['size_gb'] for f in inactive_files),
            'message': f'Found {len(inactive_files)} files inactive for {inactive_days}+ days'
        }
    
    def _action_suggest_archival(self, context: Dict, params: Dict) -> Dict:
        """Suggest files for archival"""
        inactive_files = context.get('inactive_files', [])
        
        if inactive_files:
            return {
                'status': 'completed',
                'notification': {
                    'title': 'Files Suggested for Archival',
                    'message': f'{len(inactive_files)} inactive files could be archived to free up space.',
                    'priority': params.get('priority', 'low'),
                    'category': 'file_management',
                    'data': {'inactive_files': inactive_files}
                }
            }
        
        return {
            'status': 'completed',
            'message': 'No files need archival at this time'
        }
    
    def _action_check_collaborations(self, context: Dict, params: Dict) -> Dict:
        """Check for pending collaborations"""
        # Mock pending collaborations
        pending_collaborations = [
            {
                'file': 'project_proposal.docx',
                'shared_with': 'john@company.com',
                'shared_date': '2024-07-15',
                'days_pending': 4
            }
        ]
        
        return {
            'status': 'completed',
            'pending_collaborations': pending_collaborations,
            'count': len(pending_collaborations),
            'message': f'Found {len(pending_collaborations)} pending collaborations'
        }
    
    def _action_send_reminders(self, context: Dict, params: Dict) -> Dict:
        """Send collaboration reminders"""
        pending = context.get('pending_collaborations', [])
        
        if pending:
            return {
                'status': 'completed',
                'notification': {
                    'title': 'Pending Collaboration Reminders',
                    'message': f'You have {len(pending)} files waiting for collaboration response.',
                    'priority': params.get('priority', 'medium'),
                    'category': 'collaboration',
                    'data': {'pending_collaborations': pending}
                }
            }
        
        return {
            'status': 'completed',
            'message': 'No pending collaborations found'
        }
    
    def _action_analyze_activity(self, context: Dict, params: Dict) -> Dict:
        """Analyze user activity patterns for anomalies"""
        user_id = context.get('user_id', '')
        action = context.get('action', '')
        
        # Mock activity analysis
        is_suspicious = False
        
        # Simple rules for suspicious activity
        if action == 'delete' and context.get('files_deleted_today', 0) > 10:
            is_suspicious = True
        elif action == 'download' and context.get('files_downloaded_hour', 0) > 20:
            is_suspicious = True
        
        return {
            'status': 'completed',
            'is_suspicious': is_suspicious,
            'analysis': {
                'action': action,
                'user_id': user_id,
                'risk_score': 75 if is_suspicious else 25
            },
            'message': f'Analyzed activity pattern for {action}'
        }
    
    def _action_flag_suspicious(self, context: Dict, params: Dict) -> Dict:
        """Flag suspicious activity"""
        analysis = context.get('analysis', {})
        
        if analysis.get('risk_score', 0) > 50:
            return {
                'status': 'completed',
                'notification': {
                    'title': 'Suspicious Activity Detected',
                    'message': f'Unusual {analysis.get("action", "activity")} pattern detected for user.',
                    'priority': params.get('priority', 'urgent'),
                    'category': 'security',
                    'data': analysis
                }
            }
        
        return {
            'status': 'completed',
            'message': 'No suspicious activity detected'
        }
    
    def _action_analyze_quality(self, context: Dict, params: Dict) -> Dict:
        """Analyze content quality"""
        file_analysis = context.get('file_analysis', {})
        
        quality_score = file_analysis.get('content_quality', {}).get('overall_score', 3)
        readability = file_analysis.get('readability_score', 50)
        complexity = file_analysis.get('complexity_score', 50)
        
        return {
            'status': 'completed',
            'quality_analysis': {
                'quality_score': quality_score,
                'readability_score': readability,
                'complexity_score': complexity,
                'overall_rating': 'good' if quality_score > 3 else 'needs_improvement'
            },
            'message': 'Content quality analyzed'
        }
    
    def _action_suggest_improvements(self, context: Dict, params: Dict) -> Dict:
        """Suggest content improvements"""
        quality_analysis = context.get('quality_analysis', {})
        
        suggestions = []
        
        if quality_analysis.get('readability_score', 50) < 40:
            suggestions.append('Consider simplifying language for better readability')
        
        if quality_analysis.get('complexity_score', 50) > 80:
            suggestions.append('Content is very complex - consider breaking into sections')
        
        if quality_analysis.get('quality_score', 3) < 3:
            suggestions.append('Consider adding more detail and structure to the document')
        
        if suggestions:
            return {
                'status': 'completed',
                'notification': {
                    'title': 'Content Improvement Suggestions',
                    'message': f'Found {len(suggestions)} ways to improve your document quality.',
                    'priority': params.get('priority', 'low'),
                    'category': 'content_quality',
                    'data': {'suggestions': suggestions}
                }
            }
        
        return {
            'status': 'completed',
            'message': 'Content quality is good - no improvements needed'
        }
    
    def _create_notification(self, notification_data: Dict, context: Dict) -> SmartNotification:
        """Create a smart notification"""
        notification_id = f"notif_{len(self.notification_queue) + 1}_{int(datetime.now().timestamp())}"
        
        notification = SmartNotification(
            id=notification_id,
            title=notification_data['title'],
            message=notification_data['message'],
            priority=NotificationPriority(notification_data.get('priority', 'medium')),
            category=notification_data.get('category', 'general'),
            user_id=context.get('user_id', 'unknown'),
            data=notification_data.get('data', {}),
            created_at=datetime.now().isoformat()
        )
        
        self.notification_queue.append(notification)
        return notification
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[SmartNotification]:
        """Get notifications for a specific user"""
        user_notifications = [
            notif for notif in self.notification_queue 
            if notif.user_id == user_id
        ]
        
        if unread_only:
            user_notifications = [notif for notif in user_notifications if not notif.read]
        
        # Sort by priority and creation time
        priority_order = {
            NotificationPriority.URGENT: 4,
            NotificationPriority.HIGH: 3,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 1
        }
        
        user_notifications.sort(
            key=lambda x: (priority_order[x.priority], x.created_at),
            reverse=True
        )
        
        return user_notifications
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        for notification in self.notification_queue:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    def get_workflow_analytics(self) -> Dict:
        """Get analytics about workflow execution"""
        analytics = {
            'total_rules': len(self.workflow_rules),
            'active_rules': sum(1 for rule in self.workflow_rules.values() if rule.enabled),
            'total_executions': sum(rule.execution_count for rule in self.workflow_rules.values()),
            'notifications_created': len(self.notification_queue),
            'execution_history': len(self.execution_history),
            'rule_performance': {},
            'notification_breakdown': defaultdict(int),
            'most_triggered_rules': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Rule performance
        for rule_id, rule in self.workflow_rules.items():
            analytics['rule_performance'][rule.name] = {
                'execution_count': rule.execution_count,
                'last_executed': rule.last_executed,
                'enabled': rule.enabled
            }
        
        # Notification breakdown by category
        for notification in self.notification_queue:
            analytics['notification_breakdown'][notification.category] += 1
        
        # Most triggered rules
        rule_counts = [(rule.name, rule.execution_count) for rule in self.workflow_rules.values()]
        analytics['most_triggered_rules'] = sorted(rule_counts, key=lambda x: x[1], reverse=True)[:5]
        
        return analytics
    
    def suggest_workflow_optimizations(self, user_activities: List[Dict]) -> List[Dict]:
        """Suggest workflow optimizations based on user activity patterns"""
        suggestions = []
        
        # Analyze activity patterns
        activity_counts = Counter(activity.get('action', '') for activity in user_activities)
        file_type_counts = Counter()
        
        for activity in user_activities:
            filename = activity.get('filename', '')
            if filename and '.' in filename:
                file_ext = filename.split('.')[-1].lower()
                file_type_counts[file_ext] += 1
        
        # Suggest based on patterns
        
        # High upload activity
        if activity_counts.get('upload', 0) > 20:
            suggestions.append({
                'type': 'automation',
                'title': 'Auto-organize uploaded files',
                'description': 'High upload activity detected. Consider enabling automatic file organization.',
                'template': 'auto_categorize_files',
                'priority': 'medium',
                'potential_time_savings': '10-15 minutes per day'
            })
        
        # Frequent file sharing
        if activity_counts.get('share', 0) > 10:
            suggestions.append({
                'type': 'collaboration',
                'title': 'Collaboration monitoring',
                'description': 'Frequent sharing detected. Enable collaboration reminders to track responses.',
                'template': 'collaboration_reminders',
                'priority': 'low',
                'potential_time_savings': '5-10 minutes per day'
            })
        
        # Many document files
        if file_type_counts.get('pdf', 0) + file_type_counts.get('doc', 0) + file_type_counts.get('docx', 0) > 15:
            suggestions.append({
                'type': 'quality',
                'title': 'Content quality monitoring',
                'description': 'Many documents uploaded. Enable quality assessment for better content.',
                'template': 'content_quality_check',
                'priority': 'low',
                'potential_time_savings': 'Improved document quality'
            })
        
        # Storage usage
        storage_activities = sum(1 for activity in user_activities if activity.get('action') == 'upload')
        if storage_activities > 30:
            suggestions.append({
                'type': 'storage',
                'title': 'Storage monitoring',
                'description': 'High file activity. Enable storage monitoring to prevent issues.',
                'template': 'storage_monitoring',
                'priority': 'medium',
                'potential_time_savings': 'Prevent storage issues'
            })
        
        return suggestions
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a workflow rule"""
        if rule_id in self.workflow_rules:
            self.workflow_rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a workflow rule"""
        if rule_id in self.workflow_rules:
            self.workflow_rules[rule_id].enabled = False
            return True
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a workflow rule"""
        if rule_id in self.workflow_rules:
            del self.workflow_rules[rule_id]
            return True
        return False
    
    def get_rule_details(self, rule_id: str) -> Optional[Dict]:
        """Get detailed information about a workflow rule"""
        if rule_id not in self.workflow_rules:
            return None
        
        rule = self.workflow_rules[rule_id]
        
        # Get execution history for this rule
        rule_executions = [
            exec_history for exec_history in self.execution_history
            if exec_history.get('rule_id') == rule_id
        ]
        
        return {
            'rule': {
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'trigger': rule.trigger.value,
                'conditions': rule.conditions,
                'actions': rule.actions,
                'enabled': rule.enabled,
                'created_at': rule.created_at,
                'last_executed': rule.last_executed,
                'execution_count': rule.execution_count
            },
            'execution_history': rule_executions[-10:],  # Last 10 executions
            'performance_metrics': {
                'success_rate': self._calculate_success_rate(rule_executions),
                'avg_execution_time': self._calculate_avg_execution_time(rule_executions),
                'notifications_generated': sum(
                    len(exec.get('notifications_created', [])) for exec in rule_executions
                )
            }
        }
    
    def _calculate_success_rate(self, executions: List[Dict]) -> float:
        """Calculate success rate for rule executions"""
        if not executions:
            return 0.0
        
        successful = sum(1 for exec in executions if not exec.get('errors'))
        return (successful / len(executions)) * 100
    
    def _calculate_avg_execution_time(self, executions: List[Dict]) -> float:
        """Calculate average execution time (mock implementation)"""
        # In real implementation, would track actual execution times
        return 0.5  # Mock: 0.5 seconds average


class SmartNotificationEngine:
    """AI-powered smart notification system"""
    
    def __init__(self):
        self.notification_preferences = {}
        self.notification_history = []
        self.ml_preferences = {}  # Machine learning based preferences
        
    def set_user_preferences(self, user_id: str, preferences: Dict):
        """Set notification preferences for a user"""
        self.notification_preferences[user_id] = {
            'email_notifications': preferences.get('email_notifications', True),
            'push_notifications': preferences.get('push_notifications', True),
            'quiet_hours': preferences.get('quiet_hours', {'start': '22:00', 'end': '08:00'}),
            'priority_threshold': preferences.get('priority_threshold', 'medium'),
            'categories': preferences.get('categories', {
                'security': True,
                'storage_management': True,
                'collaboration': True,
                'duplicate_detection': False,
                'content_quality': False,
                'file_management': True
            })
        }
    
    def should_send_notification(self, notification: SmartNotification) -> Dict:
        """Determine if and how to send a notification"""
        user_prefs = self.notification_preferences.get(notification.user_id, {})
        
        result = {
            'send': True,
            'channels': [],
            'delay_until': None,
            'reason': ''
        }
        
        # Check category preferences
        categories = user_prefs.get('categories', {})
        if not categories.get(notification.category, True):
            result['send'] = False
            result['reason'] = f'Category {notification.category} disabled by user'
            return result
        
        # Check priority threshold
        priority_threshold = user_prefs.get('priority_threshold', 'medium')
        priority_levels = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        
        if priority_levels.get(notification.priority.value, 2) < priority_levels.get(priority_threshold, 2):
            result['send'] = False
            result['reason'] = f'Priority {notification.priority.value} below threshold {priority_threshold}'
            return result
        
        # Check quiet hours
        current_time = datetime.now().time()
        quiet_hours = user_prefs.get('quiet_hours', {})
        
        if quiet_hours and self._is_quiet_time(current_time, quiet_hours):
            # Delay non-urgent notifications
            if notification.priority != NotificationPriority.URGENT:
                result['delay_until'] = self._calculate_next_active_time(quiet_hours)
                result['reason'] = 'Delayed due to quiet hours'
        
        # Determine channels
        if user_prefs.get('email_notifications', True):
            result['channels'].append('email')
        
        if user_prefs.get('push_notifications', True):
            result['channels'].append('push')
        
        # High priority notifications always go through
        if notification.priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
            result['channels'].extend(['email', 'push'])
            result['delay_until'] = None
        
        return result
    
    def _is_quiet_time(self, current_time, quiet_hours: Dict) -> bool:
        """Check if current time is within quiet hours"""
        try:
            start_time = datetime.strptime(quiet_hours['start'], '%H:%M').time()
            end_time = datetime.strptime(quiet_hours['end'], '%H:%M').time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:  # Quiet hours span midnight
                return current_time >= start_time or current_time <= end_time
        except:
            return False
    
    def _calculate_next_active_time(self, quiet_hours: Dict) -> str:
        """Calculate when to send delayed notifications"""
        try:
            end_time = datetime.strptime(quiet_hours['end'], '%H:%M').time()
            tomorrow = datetime.now().replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
            
            if tomorrow <= datetime.now():
                tomorrow += timedelta(days=1)
            
            return tomorrow.isoformat()
        except:
            # Default to 8 AM next day
            return (datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
    
    def learn_from_user_actions(self, user_id: str, notification_id: str, action: str):
        """Learn from user actions to improve future notifications"""
        if user_id not in self.ml_preferences:
            self.ml_preferences[user_id] = {
                'category_engagement': defaultdict(list),
                'priority_response': defaultdict(list),
                'time_preferences': defaultdict(list)
            }
        
        # Find the notification
        notification = None
        for notif in self.notification_history:
            if notif.get('id') == notification_id:
                notification = notif
                break
        
        if not notification:
            return
        
        # Record engagement
        engagement_score = {
            'dismissed': 0,
            'read': 1,
            'clicked': 2,
            'acted_upon': 3
        }.get(action, 0)
        
        prefs = self.ml_preferences[user_id]
        prefs['category_engagement'][notification['category']].append(engagement_score)
        prefs['priority_response'][notification['priority']].append(engagement_score)
        
        # Learn time preferences
        notification_time = datetime.fromisoformat(notification['created_at']).hour
        prefs['time_preferences'][notification_time].append(engagement_score)
    
    def get_personalized_recommendations(self, user_id: str) -> Dict:
        """Get personalized notification recommendations"""
        if user_id not in self.ml_preferences:
            return {'message': 'Insufficient data for personalized recommendations'}
        
        prefs = self.ml_preferences[user_id]
        recommendations = {
            'category_adjustments': [],
            'timing_suggestions': [],
            'priority_adjustments': []
        }
        
        # Analyze category engagement
        for category, scores in prefs['category_engagement'].items():
            if len(scores) >= 3:
                avg_engagement = sum(scores) / len(scores)
                if avg_engagement < 0.5:
                    recommendations['category_adjustments'].append({
                        'category': category,
                        'suggestion': 'disable',
                        'reason': f'Low engagement ({avg_engagement:.1f}/3)'
                    })
                elif avg_engagement > 2.5:
                    recommendations['category_adjustments'].append({
                        'category': category,
                        'suggestion': 'prioritize',
                        'reason': f'High engagement ({avg_engagement:.1f}/3)'
                    })
        
        # Analyze timing preferences
        time_engagement = {}
        for hour, scores in prefs['time_preferences'].items():
            if len(scores) >= 2:
                time_engagement[hour] = sum(scores) / len(scores)
        
        if time_engagement:
            best_hours = sorted(time_engagement.items(), key=lambda x: x[1], reverse=True)[:3]
            recommendations['timing_suggestions'] = [
                f"Best notification times: {', '.join([f'{hour}:00' for hour, _ in best_hours])}"
            ]
        
        return recommendations


def create_workflow_engine():
    """Factory function to create automated workflow engine"""
    return AutomatedWorkflowEngine()


def create_notification_engine():
    """Factory function to create smart notification engine"""
    return SmartNotificationEngine()
