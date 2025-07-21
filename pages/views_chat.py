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
    ChatMessageRead, ChatNotification, ChatBoardShare, ChatFileShare,
    Board, FileDocument
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
    
    # Get recent direct messages - organized by conversation
    # Find all users who have had DM conversations with current employee
    dm_conversations = []
    
    # Get all users who have either sent to or received from current employee
    dm_participants = Employee.objects.filter(
        Q(sent_messages__recipient=employee, sent_messages__channel__isnull=True) |
        Q(received_messages__sender=employee, received_messages__channel__isnull=True)
    ).distinct().exclude(id=employee.id)
    
    for participant in dm_participants:
        # Get the latest message between current employee and this participant
        latest_message = ChatMessage.objects.filter(
            Q(sender=employee, recipient=participant, channel__isnull=True) |
            Q(sender=participant, recipient=employee, channel__isnull=True)
        ).order_by('-created_at').first()
        
        if latest_message:
            # Count unread messages from this participant
            unread_count = ChatMessage.objects.filter(
                sender=participant,
                recipient=employee,
                channel__isnull=True
            ).exclude(
                read_receipts__reader=employee
            ).count()
            
            dm_conversations.append({
                'participant': participant,
                'latest_message': latest_message,
                'unread_count': unread_count
            })
    
    # Sort by latest message time
    dm_conversations.sort(key=lambda x: x['latest_message'].created_at, reverse=True)
    recent_dms = dm_conversations[:10]  # Show top 10 recent conversations
    
    # Get online employees (simplified - could be enhanced with WebSockets)
    online_employees = Employee.objects.filter(
        user__last_login__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).exclude(id=employee.id)[:20]
    
    # Get all employees for DM selection
    all_employees = Employee.objects.exclude(id=employee.id).select_related('user').order_by('user__first_name', 'user__last_name')
    
    context = {
        'employee': employee,
        'channels': channels,
        'recent_dms': recent_dms,
        'online_employees': online_employees,
        'all_employees': all_employees,
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
    
    # Get initial message from URL parameter (if any)
    initial_message = request.GET.get('msg', '')
    
    context = {
        'employee': employee,
        'recipient': recipient,
        'messages': messages_page,
        'initial_message': initial_message,
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
    
    # New: Handle board and file sharing
    shared_board_id = data.get('shared_board_id')
    shared_file_id = data.get('shared_file_id')
    
    if not content and not shared_board_id and not shared_file_id:
        return JsonResponse({'error': 'Message content, board, or file required'}, status=400)
    
    # Create the message
    message_data = {
        'sender': employee,
        'content': content or '',
        'message_type': 'text'
    }
    
    # Handle board sharing
    if shared_board_id:
        try:
            board = Board.objects.get(id=shared_board_id)
            # Check if user has access to this board
            if not (board.created_by == employee or board.members.filter(id=employee.id).exists()):
                return JsonResponse({'error': 'Access denied to this board'}, status=403)
            
            message_data['shared_board'] = board
            message_data['message_type'] = 'board'
            message_data['content'] = content or f"Shared board: {board.title}"
        except Board.DoesNotExist:
            return JsonResponse({'error': 'Board not found'}, status=404)
    
    # Handle file sharing
    if shared_file_id:
        try:
            file_doc = FileDocument.objects.get(id=shared_file_id)
            # Check if user has access to this file
            if not (file_doc.uploaded_by == employee or file_doc.shared_with.filter(id=employee.id).exists() or file_doc.is_public):
                return JsonResponse({'error': 'Access denied to this file'}, status=403)
            
            message_data['shared_file'] = file_doc
            message_data['message_type'] = 'file'
            message_data['content'] = content or f"Shared file: {file_doc.name}"
        except FileDocument.DoesNotExist:
            return JsonResponse({'error': 'File not found'}, status=404)
    
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
    
    # Handle board sharing integration
    if shared_board_id and channel_id:
        # Create board share record
        board_share, created = ChatBoardShare.objects.get_or_create(
            channel=channel,
            board=message_data['shared_board'],
            defaults={
                'shared_by': employee,
                'message': content or f"Board shared by {employee.user.get_full_name()}"
            }
        )
        
        # Add all channel members to the board
        channel.add_board_access_to_members(message_data['shared_board'])
    
    # Handle file sharing integration
    if shared_file_id:
        # Create file share record
        share_type = 'channel' if channel_id else 'message'
        ChatFileShare.objects.create(
            channel=channel if channel_id else None,
            message=message,
            file_document=message_data['shared_file'],
            shared_by=employee,
            share_type=share_type,
            share_message=content or f"File shared by {employee.user.get_full_name()}"
        )
        
        # If sharing to channel, give all members access to the file
        if channel_id:
            for member in channel.members.all():
                if not message_data['shared_file'].shared_with.filter(id=member.id).exists():
                    message_data['shared_file'].shared_with.add(member)
    
    # Create notifications for relevant users
    notification_content = content
    notification_type = 'message'
    
    if shared_board_id:
        notification_content = f"Shared board '{message_data['shared_board'].title}'"
        notification_type = 'board_shared'
    elif shared_file_id:
        notification_content = f"Shared file '{message_data['shared_file'].name}'"
        notification_type = 'file_shared'
    
    if channel_id:
        # Notify all channel members except sender
        for member in channel.members.exclude(id=employee.id):
            ChatNotification.objects.create(
                recipient=member,
                sender=employee,
                notification_type=notification_type,
                message=message,
                channel=channel,
                content=f"#{channel.name}: {notification_content[:100]}..."
            )
    else:
        # Notify the direct message recipient
        ChatNotification.objects.create(
            recipient=recipient,
            sender=employee,
            notification_type=notification_type,
            message=message,
            content=f"Direct message: {notification_content[:100]}..."
        )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': str(message.id),
            'content': message.content,
            'sender': message.sender.user.get_full_name(),
            'created_at': message.created_at.isoformat(),
            'message_type': message.message_type,
            'attachments': message.get_attachment_info(),
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


@login_required
def get_user_boards(request):
    """Get boards accessible by the current user for sharing in chat"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    # Get boards created by user or where user is a member
    boards = Board.objects.filter(
        Q(created_by=employee) | Q(members=employee),
        is_archived=False
    ).distinct().values('id', 'title', 'description', 'created_at')
    
    return JsonResponse({
        'success': True,
        'boards': list(boards)
    })


@login_required
def get_user_files(request):
    """Get files accessible by the current user for sharing in chat"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    # Get files uploaded by user, shared with user, or public files
    files = FileDocument.objects.filter(
        Q(uploaded_by=employee) | Q(shared_with=employee) | Q(is_public=True)
    ).distinct().values('id', 'name', 'file_type', 'file_size', 'created_at')
    
    return JsonResponse({
        'success': True,
        'files': list(files)
    })


@login_required
def share_board_to_channel(request, channel_id, board_id):
    """Share a board to a specific channel"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
    board = get_object_or_404(Board, id=board_id)
    
    # Check if user has access to the board
    if not (board.created_by == employee or board.members.filter(id=employee.id).exists()):
        return JsonResponse({'error': 'Access denied to this board'}, status=403)
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
        # Create or update board share
        board_share, created = ChatBoardShare.objects.get_or_create(
            channel=channel,
            board=board,
            defaults={
                'shared_by': employee,
                'message': message
            }
        )
        
        if not created:
            board_share.shared_by = employee
            board_share.message = message
            board_share.is_active = True
            board_share.save()
        
        # Add all channel members to the board
        channel.add_board_access_to_members(board)
        
        # Create a chat message about the board share
        chat_message = ChatMessage.objects.create(
            channel=channel,
            sender=employee,
            content=message or f"Shared board: {board.title}",
            message_type='board',
            shared_board=board
        )
        
        # Notify channel members
        for member in channel.members.exclude(id=employee.id):
            ChatNotification.objects.create(
                recipient=member,
                sender=employee,
                notification_type='board_shared',
                message=chat_message,
                channel=channel,
                content=f"#{channel.name}: Board '{board.title}' shared"
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Board shared successfully',
            'board_share_id': str(board_share.id)
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def share_file_to_channel(request, channel_id, file_id):
    """Share a file to a specific channel"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
    file_doc = get_object_or_404(FileDocument, id=file_id)
    
    # Check if user has access to the file
    if not (file_doc.uploaded_by == employee or file_doc.shared_with.filter(id=employee.id).exists() or file_doc.is_public):
        return JsonResponse({'error': 'Access denied to this file'}, status=403)
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
        # Create file share
        file_share = ChatFileShare.objects.create(
            channel=channel,
            file_document=file_doc,
            shared_by=employee,
            share_type='channel',
            share_message=message
        )
        
        # Give all channel members access to the file
        for member in channel.members.all():
            if not file_doc.shared_with.filter(id=member.id).exists():
                file_doc.shared_with.add(member)
        
        # Create a chat message about the file share
        chat_message = ChatMessage.objects.create(
            channel=channel,
            sender=employee,
            content=message or f"Shared file: {file_doc.name}",
            message_type='file',
            shared_file=file_doc
        )
        
        # Notify channel members
        for member in channel.members.exclude(id=employee.id):
            ChatNotification.objects.create(
                recipient=member,
                sender=employee,
                notification_type='file_shared',
                message=chat_message,
                channel=channel,
                content=f"#{channel.name}: File '{file_doc.name}' shared"
            )
        
        return JsonResponse({
            'success': True,
            'message': 'File shared successfully',
            'file_share_id': str(file_share.id)
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def channel_boards(request, channel_id):
    """View all boards shared in a channel"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
    shared_boards = ChatBoardShare.objects.filter(
        channel=channel,
        is_active=True
    ).select_related('board', 'shared_by').order_by('-shared_at')
    
    context = {
        'employee': employee,
        'channel': channel,
        'shared_boards': shared_boards,
    }
    
    return render(request, 'employee/chat/channel_boards.html', context)


@login_required
def channel_files(request, channel_id):
    """View all files shared in a channel"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
    shared_files = ChatFileShare.objects.filter(
        channel=channel,
        is_active=True
    ).select_related('file_document', 'shared_by').order_by('-shared_at')
    
    context = {
        'employee': employee,
        'channel': channel,
        'shared_files': shared_files,
    }
    
    return render(request, 'employee/chat/channel_files.html', context)


@login_required
def download_shared_file(request, file_share_id):
    """Download a file shared in chat with tracking"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=400)
    
    file_share = get_object_or_404(ChatFileShare, id=file_share_id)
    
    # Check if user has access to this shared file
    if file_share.channel:
        if not file_share.channel.members.filter(id=employee.id).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)
    elif file_share.message:
        # Check if user is part of the direct message
        message = file_share.message
        if not (message.sender == employee or message.recipient == employee):
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Increment download count
    file_share.download_count += 1
    file_share.save()
    
    # Update file's last accessed and download count
    file_doc = file_share.file_document
    file_doc.last_accessed = timezone.now()
    file_doc.download_count += 1
    file_doc.save()
    
    # Redirect to actual file
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(file_doc.file.url)


@login_required
@require_http_methods(["GET"])
def poll_messages(request, channel_id):
    """Poll for new messages in a channel - PythonAnywhere compatible"""
    try:
        employee = Employee.objects.get(user=request.user)
        channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
        
        # Get the timestamp of the last message client has
        last_message_time = request.GET.get('last_message_time')
        
        if last_message_time:
            try:
                from django.utils.dateparse import parse_datetime
                last_time = parse_datetime(last_message_time)
                # Get messages newer than the last message client has
                new_messages = ChatMessage.objects.filter(
                    channel=channel,
                    is_deleted=False,
                    created_at__gt=last_time
                ).select_related('sender').order_by('created_at')
            except (ValueError, TypeError):
                # If timestamp is invalid, just return recent messages
                new_messages = ChatMessage.objects.filter(
                    channel=channel,
                    is_deleted=False
                ).select_related('sender').order_by('-created_at')[:5]
        else:
            # If no timestamp provided, return recent messages
            new_messages = ChatMessage.objects.filter(
                channel=channel,
                is_deleted=False
            ).select_related('sender').order_by('-created_at')[:5]
        
        messages_data = []
        for message in new_messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender_name': message.sender.user.get_full_name(),
                'sender_initial': message.sender.user.first_name[0].upper() if message.sender.user.first_name else 'U',
                'created_at': message.created_at.strftime('%b %d, %H:%M'),
                'created_at_iso': message.created_at.isoformat(),
                'is_own': message.sender == employee,
                'shared_board': {
                    'title': message.shared_board.title,
                    'description': message.shared_board.description,
                    'id': message.shared_board.id
                } if message.shared_board else None,
                'shared_file': {
                    'name': message.shared_file.name,
                    'file_type': message.shared_file.file_type,
                    'file_size': message.shared_file.get_file_size_display(),
                    'download_url': f'/employee/chat/download-shared-file/{message.id}/'
                } if message.shared_file else None
            })
        
        # Mark channel as read
        membership, _ = ChatChannelMembership.objects.get_or_create(
            channel=channel, 
            employee=employee
        )
        membership.last_read_at = timezone.now()
        membership.save()
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'latest_timestamp': new_messages.last().created_at.isoformat() if new_messages else None
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def send_message_ajax(request):
    """Enhanced send message endpoint for AJAX polling"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        content = data.get('content', '').strip()
        channel_id = data.get('channel_id')
        
        if not content or not channel_id:
            return JsonResponse({'error': 'Content and channel ID are required'}, status=400)
        
        channel = get_object_or_404(ChatChannel, id=channel_id, members=employee)
        
        # Create the message
        message = ChatMessage.objects.create(
            channel=channel,
            sender=employee,
            content=content,
            created_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender_name': message.sender.user.get_full_name(),
                'sender_initial': message.sender.user.first_name[0].upper() if message.sender.user.first_name else 'U',
                'created_at': message.created_at.strftime('%b %d, %H:%M'),
                'created_at_iso': message.created_at.isoformat(),
                'is_own': True
            }
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def invite_channel_members(request, channel_id):
    """Invite new members to a chat channel"""
    try:
        employee = Employee.objects.get(user=request.user)
        channel = get_object_or_404(ChatChannel, id=channel_id)
        
        # Check if user is a member of the channel (basic permission check)
        if not channel.members.filter(id=employee.id).exists():
            return JsonResponse({'error': 'You are not a member of this channel'}, status=403)
        
        data = json.loads(request.body)
        member_ids = data.get('member_ids', [])
        
        if not member_ids:
            return JsonResponse({'error': 'No members to invite'}, status=400)
        
        # Get employees to invite
        employees_to_invite = Employee.objects.filter(id__in=member_ids)
        
        invited_count = 0
        for emp in employees_to_invite:
            # Add employee to channel if not already a member
            if not channel.members.filter(id=emp.id).exists():
                channel.members.add(emp)
                invited_count += 1
                
                # Create membership record
                ChatChannelMembership.objects.get_or_create(
                    channel=channel,
                    employee=emp,
                    defaults={'joined_at': timezone.now()}
                )
                
                # Create notification
                ChatNotification.objects.create(
                    recipient=emp,
                    notification_type='channel_invite',
                    related_channel=channel,
                    content=f"You've been invited to join #{channel.name}"
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully invited {invited_count} member(s) to the channel'
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=403)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
