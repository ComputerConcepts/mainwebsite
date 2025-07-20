from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, Max, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import json
from .models import (
    Employee, ChatChannel, ChatChannelMembership, ChatMessage, 
    ChatMessageRead, ChatNotification
)


@login_required
def chat_dashboard(request):
    """Main chat dashboard view"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    # Get user's channels with latest message info
    channels = ChatChannel.objects.filter(
        members=employee,
        is_active=True
    ).annotate(
        latest_message_time=Max('messages__created_at')
    ).order_by('-latest_message_time')
    
    # Get recent direct messages
    recent_dms = ChatMessage.objects.filter(
        Q(sender=employee, channel__isnull=True) | 
        Q(recipient=employee, channel__isnull=True)
    ).values('sender', 'recipient').annotate(
        latest_time=Max('created_at')
    ).order_by('-latest_time')[:10]
    
    # Get online employees (simplified - could be enhanced with WebSockets)
    online_employees = Employee.objects.filter(
        user__last_login__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).exclude(id=employee.id)[:20]
    
    context = {
        'employee': employee,
        'channels': channels,
        'recent_dms': recent_dms,
        'online_employees': online_employees,
    }
    
    return render(request, 'employee/chat/dashboard.html', context)


@login_required
def chat_channel(request, channel_id):
    """View for individual chat channel"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
    
    # Mark channel as read
    membership, _ = ChatChannelMembership.objects.get_or_create(
        channel=channel, 
        employee=employee
    )
    membership.last_read_at = timezone.now()
    membership.save()
    
    # Get messages with pagination
    messages_list = ChatMessage.objects.filter(
        channel=channel,
        is_deleted=False
    ).select_related('sender', 'reply_to').order_by('created_at')
    
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page', 1)
    messages_page = paginator.get_page(page_number)
    
    # Get channel members
    members = channel.members.all().order_by('user__first_name', 'user__last_name')
    
    context = {
        'employee': employee,
        'channel': channel,
        'messages': messages_page,
        'members': members,
        'is_admin': membership.is_admin or employee.is_admin(),
    }
    
    return render(request, 'employee/chat/channel.html', context)


@login_required
def chat_direct_message(request, recipient_id):
    """View for direct messages with another employee"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    recipient = get_object_or_404(Employee, id=recipient_id)
    
    # Get direct messages between these two users
    messages_list = ChatMessage.objects.filter(
        Q(sender=employee, recipient=recipient) |
        Q(sender=recipient, recipient=employee),
        channel__isnull=True,
        is_deleted=False
    ).select_related('sender', 'reply_to').order_by('created_at')
    
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page', 1)
    messages_page = paginator.get_page(page_number)
    
    # Mark messages as read
    unread_messages = ChatMessage.objects.filter(
        sender=recipient,
        recipient=employee,
        channel__isnull=True
    ).exclude(
        read_receipts__reader=employee
    )
    
    for msg in unread_messages:
        ChatMessageRead.objects.get_or_create(
            message=msg, reader=employee
        )
    
    context = {
        'employee': employee,
        'recipient': recipient,
        'messages': messages_page,
    }
    
    return render(request, 'employee/chat/direct_message.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request):
    """Send a chat message (AJAX endpoint)"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    channel_id = data.get('channel_id')
    recipient_id = data.get('recipient_id')
    reply_to_id = data.get('reply_to_id')
    
    if not content:
        return JsonResponse({'error': 'Message content cannot be empty'}, status=400)
    
    # Create the message
    message_data = {
        'sender': employee,
        'content': content,
        'message_type': 'text'
    }
    
    if reply_to_id:
        reply_to = get_object_or_404(ChatMessage, id=reply_to_id)
        message_data['reply_to'] = reply_to
    
    if channel_id:
        # Channel message
        channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
        message_data['channel'] = channel
    elif recipient_id:
        # Direct message
        recipient = get_object_or_404(Employee, id=recipient_id)
        message_data['recipient'] = recipient
    else:
        return JsonResponse({'error': 'Must specify either channel or recipient'}, status=400)
    
    message = ChatMessage.objects.create(**message_data)
    
    # Create notifications for relevant users
    if channel_id:
        # Notify all channel members except sender
        for member in channel.members.exclude(id=employee.id):
            ChatNotification.objects.create(
                recipient=member,
                sender=employee,
                notification_type='message',
                message=message,
                channel=channel,
                content=f"New message in #{channel.name}: {content[:100]}..."
            )
    else:
        # Notify the direct message recipient
        ChatNotification.objects.create(
            recipient=recipient,
            sender=employee,
            notification_type='message',
            message=message,
            content=f"New direct message: {content[:100]}..."
        )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': str(message.id),
            'content': message.content,
            'sender': message.sender.user.get_full_name(),
            'created_at': message.created_at.isoformat(),
        }
    })


@login_required
def create_channel(request):
    """Create a new chat channel"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        channel_type = request.POST.get('channel_type', 'general')
        member_ids = request.POST.getlist('members')
        
        if not name:
            messages.error(request, 'Channel name is required.')
            return redirect('chat_dashboard')
        
        # Create the channel
        channel = ChatChannel.objects.create(
            name=name,
            description=description,
            channel_type=channel_type,
            created_by=employee
        )
        
        # Add creator as admin member
        ChatChannelMembership.objects.create(
            channel=channel,
            employee=employee,
            is_admin=True
        )
        
        # Add selected members
        for member_id in member_ids:
            try:
                member = Employee.objects.get(id=member_id)
                ChatChannelMembership.objects.create(
                    channel=channel,
                    employee=member
                )
                
                # Send invitation notification
                ChatNotification.objects.create(
                    recipient=member,
                    sender=employee,
                    notification_type='channel_invite',
                    channel=channel,
                    content=f"You've been invited to join #{channel.name}"
                )
            except Employee.DoesNotExist:
                continue
        
        messages.success(request, f'Channel "#{name}" created successfully!')
        return redirect('chat_channel', channel_id=channel.id)
    
    # GET request - show create form
    all_employees = Employee.objects.exclude(id=employee.id).order_by(
        'user__first_name', 'user__last_name'
    )
    
    context = {
        'employee': employee,
        'all_employees': all_employees,
        'channel_types': ChatChannel.CHANNEL_TYPES,
    }
    
    return render(request, 'employee/chat/create_channel.html', context)


@login_required
def chat_notifications(request):
    """Get chat notifications (AJAX endpoint)"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    notifications = ChatNotification.objects.filter(
        recipient=employee,
        is_read=False
    ).order_by('-created_at')[:20]
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': str(notification.id),
            'type': notification.notification_type,
            'content': notification.content,
            'sender': notification.sender.user.get_full_name(),
            'created_at': notification.created_at.isoformat(),
            'channel_id': str(notification.channel.id) if notification.channel else None,
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'unread_count': len(notification_data)
    })


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a chat notification as read"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    notification = get_object_or_404(
        ChatNotification, 
        id=notification_id, 
        recipient=employee
    )
    
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})
