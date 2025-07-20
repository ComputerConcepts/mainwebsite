"""
AI Workflow Management Views
Interface for managing AI workflows, notifications, and analytics
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import json

from .models import (
    Employee, AIWorkflowRule, AIWorkflowExecution, AINotification, 
    AINotificationPreference, AIFileAnalysis, FileDocument
)
from .ai_workflow_service import get_ai_workflow_service


@login_required
def ai_dashboard(request):
    """Main AI dashboard showing workflows, notifications, and analytics"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    ai_service = get_ai_workflow_service()
    
    # Get user's notifications
    recent_notifications = ai_service.get_user_notifications(employee, unread_only=False)[:10]
    unread_count = AINotification.objects.filter(user=employee, is_read=False).count()
    
    # Get workflow analytics
    analytics = ai_service.get_workflow_analytics(employee)
    
    # Get recent file analyses (completed)
    recent_analyses = AIFileAnalysis.objects.filter(
        document__uploaded_by=employee,
        status='completed'
    ).order_by('-analysis_completed_at')[:5]
    
    # Get pending analyses (queued or processing)
    pending_analyses = AIFileAnalysis.objects.filter(
        document__uploaded_by=employee,
        status__in=['queued', 'processing']
    ).order_by('-queued_at')[:5]
    
    # Get workflow suggestions
    suggestions = ai_service.suggest_workflow_optimizations(employee)
    
    # Get storage usage for threshold monitoring
    storage_percentage = employee.get_storage_percentage()
    storage_warning = storage_percentage >= 80
    
    context = {
        'employee': employee,
        'recent_notifications': recent_notifications,
        'unread_notifications_count': unread_count,
        'analytics': analytics,
        'recent_analyses': recent_analyses,
        'pending_analyses': pending_analyses,
        'workflow_suggestions': suggestions[:3],  # Top 3 suggestions
        'storage_percentage': storage_percentage,
        'storage_warning': storage_warning,
        'ai_features': {
            'workflows_active': analytics['active_rules'],
            'total_executions': analytics.get('user_workflow_executions', 0),
            'files_analyzed': AIFileAnalysis.objects.filter(
                document__uploaded_by=employee,
                status='completed'
            ).count(),
            'notifications_sent': analytics.get('user_notifications', 0)
        }
    }
    
    return render(request, 'employee/ai_dashboard.html', context)


@login_required
def ai_notifications(request):
    """View and manage AI notifications"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    # Filter parameters
    category_filter = request.GET.get('category', 'all')
    priority_filter = request.GET.get('priority', 'all')
    unread_only = request.GET.get('unread') == 'true'
    
    # Build query
    notifications = AINotification.objects.filter(user=employee)
    
    if category_filter != 'all':
        notifications = notifications.filter(category=category_filter)
    
    if priority_filter != 'all':
        notifications = notifications.filter(priority=priority_filter)
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary stats
    summary = {
        'total': AINotification.objects.filter(user=employee).count(),
        'unread': AINotification.objects.filter(user=employee, is_read=False).count(),
        'urgent': AINotification.objects.filter(user=employee, priority='urgent', is_read=False).count(),
        'high': AINotification.objects.filter(user=employee, priority='high', is_read=False).count(),
    }
    
    # Category breakdown
    categories = AINotification.objects.filter(user=employee).values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'employee': employee,
        'page_obj': page_obj,
        'summary': summary,
        'categories': categories,
        'current_category': category_filter,
        'current_priority': priority_filter,
        'unread_only': unread_only,
        'category_choices': AINotification.CATEGORY_CHOICES,
        'priority_choices': AINotification.PRIORITY_CHOICES,
    }
    
    return render(request, 'employee/ai_notifications.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        employee = Employee.objects.get(user=request.user)
        notification = get_object_or_404(AINotification, id=notification_id, user=employee)
        
        notification.mark_as_read()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read'
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Employee profile not found'
        }, status=403)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the user"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        unread_notifications = AINotification.objects.filter(user=employee, is_read=False)
        count = unread_notifications.count()
        
        unread_notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Marked {count} notifications as read'
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Employee profile not found'
        }, status=403)


@login_required
def ai_workflows(request):
    """View and manage AI workflow rules"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    # Get workflow rules (user's own + system defaults)
    workflows = AIWorkflowRule.objects.filter(
        Q(created_by=employee) | Q(created_by__user__username='admin')
    ).order_by('-created_at')
    
    # Get recent executions
    recent_executions = AIWorkflowExecution.objects.filter(
        triggered_by=employee
    ).order_by('-started_at')[:10]
    
    # Get execution statistics
    execution_stats = {
        'total': AIWorkflowExecution.objects.filter(triggered_by=employee).count(),
        'successful': AIWorkflowExecution.objects.filter(
            triggered_by=employee, 
            status='completed'
        ).count(),
        'failed': AIWorkflowExecution.objects.filter(
            triggered_by=employee, 
            status='failed'
        ).count(),
        'last_24h': AIWorkflowExecution.objects.filter(
            triggered_by=employee,
            started_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
    }
    
    context = {
        'employee': employee,
        'workflows': workflows,
        'recent_executions': recent_executions,
        'execution_stats': execution_stats,
        'trigger_choices': AIWorkflowRule.TRIGGER_CHOICES,
    }
    
    return render(request, 'employee/ai_workflows.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_workflow_rule(request, rule_id):
    """Enable/disable a workflow rule"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Only allow toggling user's own rules or admin rules
        workflow_rule = get_object_or_404(
            AIWorkflowRule,
            id=rule_id
        )
        
        # Check permissions
        if workflow_rule.created_by != employee and workflow_rule.created_by.user.username != 'admin':
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        workflow_rule.enabled = not workflow_rule.enabled
        workflow_rule.save()
        
        # Update in AI service
        ai_service = get_ai_workflow_service()
        if workflow_rule.enabled:
            ai_service.enable_rule(str(rule_id))
        else:
            ai_service.disable_rule(str(rule_id))
        
        return JsonResponse({
            'success': True,
            'enabled': workflow_rule.enabled,
            'message': f'Workflow {"enabled" if workflow_rule.enabled else "disabled"}'
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Employee profile not found'
        }, status=403)


@login_required
def ai_analytics(request):
    """View AI analytics and insights"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    ai_service = get_ai_workflow_service()
    
    # Time range filter
    time_range = request.GET.get('range', '30')  # days
    start_date = timezone.now() - timedelta(days=int(time_range))
    
    # Analytics data
    analytics = {
        'workflow_executions': AIWorkflowExecution.objects.filter(
            triggered_by=employee,
            started_at__gte=start_date
        ).count(),
        'files_analyzed': AIFileAnalysis.objects.filter(
            document__uploaded_by=employee,
            analysis_started_at__gte=start_date,
            analysis_completed=True
        ).count(),
        'notifications_received': AINotification.objects.filter(
            user=employee,
            created_at__gte=start_date
        ).count(),
        'storage_optimization': employee.get_storage_percentage(),
    }
    
    # File analysis insights
    file_categories = AIFileAnalysis.objects.filter(
        document__uploaded_by=employee,
        analysis_completed=True,
        category__isnull=False
    ).exclude(category='').values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Security insights
    security_files = AIFileAnalysis.objects.filter(
        document__uploaded_by=employee,
        contains_sensitive_info=True
    ).count()
    
    # Quality insights
    quality_analysis = AIFileAnalysis.objects.filter(
        document__uploaded_by=employee,
        analysis_completed=True,
        quality_score__isnull=False
    ).aggregate(
        avg_quality=Count('quality_score'),
        high_quality=Count('id', filter=Q(quality_score__gte=4)),
        low_quality=Count('id', filter=Q(quality_score__lt=3))
    )
    
    # Workflow performance
    workflow_performance = AIWorkflowExecution.objects.filter(
        triggered_by=employee,
        started_at__gte=start_date
    ).values('workflow_rule__name').annotate(
        executions=Count('id'),
        success_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
    ).order_by('-executions')[:5]
    
    context = {
        'employee': employee,
        'analytics': analytics,
        'file_categories': file_categories,
        'security_files_count': security_files,
        'quality_analysis': quality_analysis,
        'workflow_performance': workflow_performance,
        'time_range': time_range,
        'time_range_options': [
            ('7', '7 days'),
            ('30', '30 days'),
            ('90', '90 days'),
            ('365', '1 year')
        ]
    }
    
    return render(request, 'employee/ai_analytics.html', context)


@login_required
def ai_settings(request):
    """AI notification and workflow preferences"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    # Get or create notification preferences
    preferences, created = AINotificationPreference.objects.get_or_create(
        user=employee,
        defaults={
            'email_notifications': True,
            'push_notifications': True,
            'priority_threshold': 'medium'
        }
    )
    
    if request.method == 'POST':
        # Update preferences
        preferences.email_notifications = request.POST.get('email_notifications') == 'on'
        preferences.push_notifications = request.POST.get('push_notifications') == 'on'
        preferences.priority_threshold = request.POST.get('priority_threshold', 'medium')
        
        # Quiet hours
        quiet_start = request.POST.get('quiet_hours_start')
        quiet_end = request.POST.get('quiet_hours_end')
        
        if quiet_start:
            preferences.quiet_hours_start = quiet_start
        if quiet_end:
            preferences.quiet_hours_end = quiet_end
        
        # Category preferences
        preferences.security_notifications = request.POST.get('security_notifications') == 'on'
        preferences.storage_notifications = request.POST.get('storage_notifications') == 'on'
        preferences.collaboration_notifications = request.POST.get('collaboration_notifications') == 'on'
        preferences.duplicate_notifications = request.POST.get('duplicate_notifications') == 'on'
        preferences.quality_notifications = request.POST.get('quality_notifications') == 'on'
        preferences.file_management_notifications = request.POST.get('file_management_notifications') == 'on'
        preferences.workflow_notifications = request.POST.get('workflow_notifications') == 'on'
        
        preferences.save()
        
        # Update notification engine preferences
        ai_service = get_ai_workflow_service()
        ai_service.notification_engine.set_user_preferences(
            employee.user.username,
            {
                'email_notifications': preferences.email_notifications,
                'push_notifications': preferences.push_notifications,
                'quiet_hours': {
                    'start': preferences.quiet_hours_start.strftime('%H:%M'),
                    'end': preferences.quiet_hours_end.strftime('%H:%M')
                },
                'priority_threshold': preferences.priority_threshold,
                'categories': preferences.get_category_preferences()
            }
        )
        
        messages.success(request, 'AI preferences updated successfully.')
        return redirect('ai_settings')
    
    context = {
        'employee': employee,
        'preferences': preferences,
        'priority_choices': AINotification.PRIORITY_CHOICES,
    }
    
    return render(request, 'employee/ai_settings.html', context)


@login_required
def file_analysis_detail(request, analysis_id):
    """View detailed AI analysis of a file"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    analysis = get_object_or_404(
        AIFileAnalysis,
        id=analysis_id,
        document__uploaded_by=employee
    )
    
    context = {
        'employee': employee,
        'analysis': analysis,
        'document': analysis.document,
    }
    
    return render(request, 'employee/ai_file_analysis.html', context)


@login_required
@require_http_methods(["POST"])
def trigger_manual_analysis(request, file_id):
    """Queue AI analysis for a file"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id, uploaded_by=employee)
        
        # Get or create analysis record
        analysis, created = AIFileAnalysis.objects.get_or_create(
            document=file_doc,
            defaults={'status': 'queued'}
        )
        
        if analysis.status == 'completed':
            return JsonResponse({
                'success': True,
                'message': 'Analysis already completed',
                'status': 'completed'
            })
        elif analysis.status in ['queued', 'processing']:
            return JsonResponse({
                'success': True,
                'message': f'Analysis is {analysis.status}',
                'status': analysis.status
            })
        else:
            # Queue for processing
            analysis.status = 'queued'
            analysis.save()
            return JsonResponse({
                'success': True,
                'message': 'Analysis queued for processing',
                'status': 'queued'
            })
            
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Employee profile not found'
        }, status=403)


@login_required
def check_analysis_status(request, analysis_id):
    """Check the status of an AI analysis"""
    try:
        employee = Employee.objects.get(user=request.user)
        analysis = get_object_or_404(
            AIFileAnalysis, 
            id=analysis_id, 
            document__uploaded_by=employee
        )
        
        return JsonResponse({
            'success': True,
            'analysis_id': analysis.id,
            'status': analysis.status,
            'queued_at': analysis.queued_at.isoformat() if analysis.queued_at else None,
            'processing_started_at': analysis.processing_started_at.isoformat() if analysis.processing_started_at else None,
            'completed_at': analysis.analysis_completed_at.isoformat() if analysis.analysis_completed_at else None,
            'retry_count': analysis.retry_count,
            'error_message': analysis.error_message if analysis.status == 'failed' else None,
            'file_name': analysis.document.name
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Employee profile not found'
        }, status=403)
    except AIFileAnalysis.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Analysis not found'
        }, status=404)


@login_required
def ai_workflow_execution_detail(request, execution_id):
    """View details of a workflow execution"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    execution = get_object_or_404(
        AIWorkflowExecution,
        id=execution_id,
        triggered_by=employee
    )
    
    context = {
        'employee': employee,
        'execution': execution,
        'workflow_rule': execution.workflow_rule,
        'context_data': json.dumps(execution.context_data, indent=2),
        'result_data': json.dumps(execution.result_data, indent=2),
    }
    
    return render(request, 'employee/ai_workflow_execution.html', context)


@login_required 
def ai_queue_dashboard(request):
    """Dashboard view for AI processing queue"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Only allow admins and AI staff to see queue dashboard
        if not (employee.is_admin() or employee.department.lower() in ['it', 'ai', 'tech']):
            messages.error(request, 'Access denied. Only administrators can view the AI queue dashboard.')
            return redirect('ai_dashboard')
        
        # Get queue statistics
        queue_stats = {}
        for stat in AIFileAnalysis.get_queue_stats():
            queue_stats[stat['status']] = stat['count']
        
        # Get recent analyses
        recent_analyses = AIFileAnalysis.objects.select_related('document', 'document__uploaded_by').order_by('-queued_at')[:20]
        
        # Get currently processing
        processing_analyses = AIFileAnalysis.objects.filter(status='processing').select_related('document')
        
        # Get failed analyses that can be retried
        from django.db import models
        failed_analyses = AIFileAnalysis.objects.filter(status='failed', retry_count__lt=models.F('max_retries')).select_related('document')[:10]
        
        context = {
            'employee': employee,
            'queue_stats': queue_stats,
            'recent_analyses': recent_analyses,
            'processing_analyses': processing_analyses,
            'failed_analyses': failed_analyses,
            'total_queued': queue_stats.get('queued', 0),
            'total_processing': queue_stats.get('processing', 0),
            'total_completed': queue_stats.get('completed', 0),
            'total_failed': queue_stats.get('failed', 0),
        }
        
        return render(request, 'employee/ai_queue_dashboard.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')


@login_required
@require_http_methods(["POST"])
def retry_failed_analysis(request, analysis_id):
    """Retry a failed AI analysis"""
    try:
        employee = Employee.objects.get(user=request.user)
        analysis = get_object_or_404(AIFileAnalysis, id=analysis_id)
        
        # Check permissions - admin or file owner
        if not (employee.is_admin() or 
                employee.department.lower() in ['it', 'ai', 'tech'] or
                analysis.document.uploaded_by == employee):
            return JsonResponse({
                'success': False,
                'error': 'Access denied'
            }, status=403)
        
        # Check if analysis can be retried
        if analysis.status != 'failed':
            return JsonResponse({
                'success': False,
                'error': 'Analysis is not in failed state'
            })
        
        if analysis.retry_count >= analysis.max_retries:
            return JsonResponse({
                'success': False,
                'error': 'Maximum retry attempts exceeded'
            })
        
        # Reset analysis for retry
        analysis.status = 'queued'
        analysis.error_message = ''
        analysis.queued_at = timezone.now()
        analysis.processing_started_at = None
        analysis.analysis_completed_at = None
        analysis.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Analysis has been queued for retry',
            'analysis_id': analysis.id,
            'status': 'queued'
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Employee profile not found'
        }, status=403)
