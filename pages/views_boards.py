from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db import models
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Board, BoardList, Card, CardComment, CardAttachment, Employee, BoardShare, BoardActivity
from .forms import BoardShareForm
from .views import is_employee_authenticated
import json


def reorder_cards_in_list(board_list):
    """Utility function to fix position conflicts in a list"""
    cards = board_list.cards.all().order_by('position', 'created_at')
    for index, card in enumerate(cards, 1):
        if card.position != index:
            card.position = index
            card.save()


def reorder_lists(board):
    """Ensure board lists have sequential positions"""
    lists = board.lists.all().order_by('position', 'created_at')
    for index, board_list in enumerate(lists, 1):
        if board_list.position != index:
            board_list.position = index
            board_list.save(update_fields=['position'])


@login_required
def project_boards(request):
    """Display all project boards for the authenticated employee"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found. Please complete your employee profile before accessing project boards.')
        return redirect('employee_dashboard')
    
    # Get URL parameters
    search_query = request.GET.get('search', '').strip()
    
    # Base querysets
    created_boards = Board.objects.filter(created_by=employee, is_archived=False)
    member_boards = Board.objects.filter(members=employee, is_archived=False).exclude(created_by=employee)
    
    # Get shared boards (boards shared via BoardShare)
    shared_board_ids = BoardShare.objects.filter(shared_with=employee).values_list('board_id', flat=True)
    shared_boards = Board.objects.filter(id__in=shared_board_ids, is_archived=False)
    
    # For regular view, remove shared boards from member_boards to avoid duplication
    member_boards = member_boards.exclude(id__in=shared_board_ids)
    
    # Apply search filter
    if search_query:
        from django.db.models import Q
        search_filter = Q(title__icontains=search_query) | Q(description__icontains=search_query)
        created_boards = created_boards.filter(search_filter)
        member_boards = member_boards.filter(search_filter)
        shared_boards = shared_boards.filter(search_filter)
    
    # Order by update time
    created_boards = created_boards.order_by('-updated_at')
    member_boards = member_boards.order_by('-updated_at')
    shared_boards = shared_boards.order_by('-updated_at')
    
    context = {
        'created_boards': created_boards,
        'member_boards': member_boards,
        'shared_boards': shared_boards,
        'total_boards': created_boards.count() + member_boards.count() + shared_boards.count(),
        'search_query': search_query,
    }
    
    return render(request, 'employee/boards/boards_list.html', context)


@login_required
def create_board(request):
    """Create a new project board"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        if title:
            employee = Employee.objects.get(user=request.user)
            
            board = Board.objects.create(
                title=title,
                description=description,
                created_by=employee
            )
            
            # Add creator as member
            board.members.add(employee)
            
            # Create default lists
            BoardList.objects.create(title="To Do", board=board, position=1)
            BoardList.objects.create(title="In Progress", board=board, position=2)
            BoardList.objects.create(title="Done", board=board, position=3)
            
            messages.success(request, f'Board "{title}" created successfully!')
            return redirect('board_detail', board_id=board.id)
        else:
            messages.error(request, 'Board title is required.')
    
    return render(request, 'employee/boards/create_board.html')


@login_required
def board_detail(request, board_id):
    """Display board detail with lists and cards"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    employee = Employee.objects.get(user=request.user)
    
    try:
        board = Board.objects.get(id=board_id)
        
        # Check if user has access to this board
        has_direct_access = board.created_by == employee or employee in board.members.all()
        board_share = BoardShare.objects.filter(board=board, shared_with=employee).first()
        
        if not (has_direct_access or board_share):
            messages.error(request, 'You do not have access to this board.')
            return redirect('project_boards')
        
        # Get all lists with their cards
        lists = board.lists.prefetch_related('cards__assigned_to').all()
        
        # Get all employees for assignment dropdown
        all_employees = Employee.objects.all()
        
        # Determine user permissions
        user_permission = 'admin' if board.created_by == employee else (board_share.permission if board_share else 'view')
        
        # Get sharing information
        board_shares = BoardShare.objects.filter(board=board).select_related('shared_with', 'shared_by')
        
        # Get recent activity
        recent_activities = BoardActivity.objects.filter(board=board).select_related('user').order_by('-created_at')[:10]
        
        context = {
            'board': board,
            'lists': lists,
            'all_employees': all_employees,
            'is_board_owner': board.created_by == employee,
            'user_permission': user_permission,
            'can_edit': user_permission in ['edit', 'admin'],
            'can_share': user_permission == 'admin' or board.created_by == employee,
            'board_shares': board_shares,
            'recent_activities': recent_activities,
        }
        
        return render(request, 'employee/boards/board_detail.html', context)
        
    except Board.DoesNotExist:
        messages.error(request, 'Board not found.')
        return redirect('project_boards')


@login_required
@require_http_methods(["POST"])
def create_list(request, board_id):
    """Create a new list in a board"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        board = Board.objects.get(id=board_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check access
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        title = request.POST.get('title')
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        # Get next position
        last_list = board.lists.last()
        position = (last_list.position + 1) if last_list else 1
        
        board_list = BoardList.objects.create(
            title=title,
            board=board,
            position=position
        )
        
        return JsonResponse({
            'success': True,
            'list': {
                'id': str(board_list.id),
                'title': board_list.title,
                'position': board_list.position
            }
        })
        
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_card(request, list_id):
    """Create a new card in a list"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        board_list = BoardList.objects.get(id=list_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check access to board
        board = board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        title = request.POST.get('title')
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        # Get next position
        last_card = board_list.cards.last()
        position = (last_card.position + 1) if last_card else 1
        
        card = Card.objects.create(
            title=title,
            board_list=board_list,
            created_by=employee,
            position=position
        )
        
        return JsonResponse({
            'success': True,
            'card': {
                'id': str(card.id),
                'title': card.title,
                'position': card.position,
                'priority': card.priority,
                'created_by': f"{card.created_by.user.first_name} {card.created_by.user.last_name}"
            }
        })
        
    except BoardList.DoesNotExist:
        return JsonResponse({'error': 'List not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def card_detail(request, card_id):
    """Display card detail modal content"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        card = Card.objects.get(id=card_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check access to board
        board = card.board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get card data
        card_data = {
            'id': str(card.id),
            'title': card.title,
            'description': card.description,
            'priority': card.priority,
            'due_date': card.due_date.isoformat() if card.due_date else None,
            'is_completed': card.is_completed,
            'created_by': f"{card.created_by.user.first_name} {card.created_by.user.last_name}",
            'assigned_to': [
                {
                    'id': str(emp.id),
                    'name': f"{emp.user.first_name} {emp.user.last_name}"
                } for emp in card.assigned_to.all()
            ],
            'comments': [
                {
                    'id': str(comment.id),
                    'content': comment.content,
                    'author': f"{comment.author.user.first_name} {comment.author.user.last_name}",
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                } for comment in card.comments.all()
            ]
        }
        
        return JsonResponse({'success': True, 'card': card_data})
        
    except Card.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_card(request, card_id):
    """Update card details"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        card = Card.objects.get(id=card_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check access to board
        board = card.board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Update card fields
        if 'title' in request.POST:
            card.title = request.POST['title']
        if 'description' in request.POST:
            card.description = request.POST['description']
        if 'priority' in request.POST:
            card.priority = request.POST['priority']
        if 'is_completed' in request.POST:
            card.is_completed = request.POST['is_completed'].lower() == 'true'
        
        card.save()
        
        return JsonResponse({'success': True, 'message': 'Card updated successfully'})
        
    except Card.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def move_card(request):
    """Move card between lists or change position"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        new_list_id = data.get('new_list_id')
        new_position = data.get('new_position', 1)
        
        card = Card.objects.get(id=card_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check access to board
        board = card.board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Validate and sanitize position
        new_list = BoardList.objects.get(id=new_list_id)
        max_position = new_list.cards.count()
        
        # If moving to the same list, don't count the card itself
        if card.board_list.id == new_list.id:
            max_position -= 1
            
        # Ensure position is within valid range
        new_position = max(1, min(new_position, max_position + 1))
        
        with transaction.atomic():
            old_list = card.board_list
            new_list = BoardList.objects.get(id=new_list_id)
            
            if old_list.id == new_list.id:
                # Moving within the same list - just reorder
                old_position = card.position
                if new_position < old_position:
                    # Moving up - shift cards down
                    old_list.cards.filter(
                        position__gte=new_position,
                        position__lt=old_position
                    ).update(position=models.F('position') + 1)
                elif new_position > old_position:
                    # Moving down - shift cards up
                    old_list.cards.filter(
                        position__gt=old_position,
                        position__lte=new_position
                    ).update(position=models.F('position') - 1)
                    
                card.position = new_position
                card.save()
            else:
                # Moving between different lists
                # Step 1: Remove card from old list and compact positions
                old_list.cards.filter(position__gt=card.position).update(
                    position=models.F('position') - 1
                )
                
                # Step 2: Make space in new list
                new_list.cards.filter(position__gte=new_position).update(
                    position=models.F('position') + 1
                )
                
                # Step 3: Move card to new list
                card.board_list = new_list
                card.position = new_position
                card.save()
        
        return JsonResponse({'success': True, 'message': 'Card moved successfully'})
        
    except (Card.DoesNotExist, BoardList.DoesNotExist):
        return JsonResponse({'error': 'Card or list not found'}, status=404)
    except Exception as e:
        # If we get a position conflict, try to fix it and retry
        if 'unique constraint' in str(e).lower() and 'position' in str(e).lower():
            try:
                with transaction.atomic():
                    # Fix positions in both lists
                    old_list = card.board_list
                    new_list = BoardList.objects.get(id=new_list_id)
                    
                    reorder_cards_in_list(old_list)
                    if old_list.id != new_list.id:
                        reorder_cards_in_list(new_list)
                    
                    # Now try the move again with position at end
                    max_position = new_list.cards.count()
                    if old_list.id == new_list.id:
                        max_position -= 1
                    
                    card.board_list = new_list
                    card.position = max_position + 1
                    card.save()
                    
                    # Reorder again to clean up
                    reorder_cards_in_list(new_list)
                    
                return JsonResponse({'success': True, 'message': 'Card moved successfully (position corrected)'})
            except Exception as retry_error:
                return JsonResponse({'error': f'Failed to move card after position correction: {str(retry_error)}'}, status=500)
        else:
            return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_card(request, card_id):
    """Delete a card from a list"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        card = Card.objects.get(id=card_id)
        employee = Employee.objects.get(user=request.user)

        board = card.board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)

        board_list = card.board_list
        card_title = card.title
        card.delete()

        reorder_cards_in_list(board_list)

        BoardActivity.objects.create(
            board=board,
            user=employee,
            action='delete',
            details=f'deleted card "{card_title}" from {board_list.title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        return JsonResponse({'success': True})

    except Card.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_board_list(request, list_id):
    """Delete a board list (and its cards)"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        board_list = BoardList.objects.get(id=list_id)
        employee = Employee.objects.get(user=request.user)

        board = board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)

        list_title = board_list.title
        board_list.delete()

        reorder_lists(board)

        BoardActivity.objects.create(
            board=board,
            user=employee,
            action='delete',
            details=f'deleted list "{list_title}"',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        return JsonResponse({'success': True})

    except BoardList.DoesNotExist:
        return JsonResponse({'error': 'List not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_card_comment(request, card_id):
    """Add a comment to a card"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        card = Card.objects.get(id=card_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check access to board
        board = card.board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        content = request.POST.get('content')
        if not content:
            return JsonResponse({'error': 'Comment content is required'}, status=400)
        
        comment = CardComment.objects.create(
            card=card,
            author=employee,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': str(comment.id),
                'content': comment.content,
                'author': f"{comment.author.user.first_name} {comment.author.user.last_name}",
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except Card.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_board_member(request, board_id):
    """Add a member to a board"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        board = Board.objects.get(id=board_id)
        employee = Employee.objects.get(user=request.user)
        
        # Only board creator can add members
        if board.created_by != employee:
            return JsonResponse({'error': 'Only the board creator can add members'}, status=403)
        
        # Get member email from request
        member_email = request.POST.get('email')
        if not member_email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Find the employee by email
        try:
            member_employee = Employee.objects.get(user__email=member_email)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found with this email'}, status=404)
        
        # Check if already a member
        if member_employee in board.members.all():
            return JsonResponse({'error': 'Employee is already a member of this board'}, status=400)
        
        # Add member to board
        board.members.add(member_employee)
        
        return JsonResponse({
            'success': True,
            'message': f'{member_employee.first_name} {member_employee.last_name} added to board',
            'member': {
                'id': str(member_employee.id),
                'name': f'{member_employee.first_name} {member_employee.last_name}',
                'email': member_employee.user.email
            }
        })
        
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_board_member(request, board_id):
    """Remove a member from a board"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        board = Board.objects.get(id=board_id)
        employee = Employee.objects.get(user=request.user)
        
        # Only board creator can remove members
        if board.created_by != employee:
            return JsonResponse({'error': 'Only the board creator can remove members'}, status=403)
        
        # Get member ID from request
        member_id = request.POST.get('member_id')
        if not member_id:
            return JsonResponse({'error': 'Member ID is required'}, status=400)
        
        # Find the member
        try:
            member_employee = Employee.objects.get(id=member_id)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
        
        # Cannot remove the board creator
        if member_employee == board.created_by:
            return JsonResponse({'error': 'Cannot remove the board creator'}, status=400)
        
        # Check if member is actually on the board
        if member_employee not in board.members.all():
            return JsonResponse({'error': 'Employee is not a member of this board'}, status=400)
        
        # Remove member from board
        board.members.remove(member_employee)
        
        # Also remove them from any card assignments on this board
        for board_list in board.lists.all():
            for card in board_list.cards.all():
                if member_employee in card.assigned_to.all():
                    card.assigned_to.remove(member_employee)
        
        return JsonResponse({
            'success': True,
            'message': f'{member_employee.first_name} {member_employee.last_name} removed from board'
        })
        
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_board_members(request, board_id):
    """Get all members of a board"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        board = Board.objects.get(id=board_id)
        employee = Employee.objects.get(user=request.user)
        
        # Check if user has access to this board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get all members
        members = []
        for member in board.members.all():
            members.append({
                'id': str(member.id),
                'name': f'{member.first_name} {member.last_name}',
                'email': member.user.email,
                'is_owner': member == board.created_by
            })
        
        return JsonResponse({
            'success': True,
            'members': members
        })
        
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def search_employees(request):
    """Search for employees to add to boards"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    query = request.GET.get('query', '')
    if len(query) < 2:
        return JsonResponse({'employees': []})
    
    # Search employees by name or email
    employees = Employee.objects.filter(
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query) |
        models.Q(user__email__icontains=query)
    )[:10]  # Limit to 10 results
    
    results = []
    for emp in employees:
        results.append({
            'id': str(emp.id),
            'name': f'{emp.first_name} {emp.last_name}',
            'email': emp.user.email
        })
    
    return JsonResponse({'employees': results})


@login_required
@require_http_methods(["POST"])
def delete_board(request, board_id):
    """Archive a board (soft delete)"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        board = Board.objects.get(id=board_id)
        employee = Employee.objects.get(user=request.user)
        
        # Only board creator can delete
        if board.created_by != employee:
            messages.error(request, 'Only the board creator can delete this board.')
            return redirect('board_detail', board_id=board_id)
        
        board.is_archived = True
        board.save()
        
        messages.success(request, f'Board "{board.title}" has been archived.')
        return redirect('project_boards')
        
    except Board.DoesNotExist:
        messages.error(request, 'Board not found.')
        return redirect('project_boards')


@login_required
def share_board(request, board_id):
    """Share a board with other users via email"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        employee = Employee.objects.get(user=request.user)
        board = get_object_or_404(Board, id=board_id)
        
        # Check if user can share this board (creator or admin)
        if not (board.created_by == employee or 
                BoardShare.objects.filter(board=board, shared_with=employee, permission='admin').exists()):
            messages.error(request, 'You do not have permission to share this board.')
            return redirect('board_detail', board_id=board_id)
        
        if request.method == 'POST':
            form = BoardShareForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                permission = form.cleaned_data['permission']
                message = form.cleaned_data.get('message', '')
                
                # Get the user and employee by email
                from django.contrib.auth.models import User
                user = User.objects.get(email=email)
                target_employee = Employee.objects.get(user=user)
                
                # Check if user is trying to share with themselves
                if target_employee == employee:
                    return JsonResponse({'success': False, 'errors': {'email': ['You cannot share a board with yourself.']}})
                
                # Create or update share
                share, created = BoardShare.objects.get_or_create(
                    board=board,
                    shared_with=target_employee,
                    defaults={
                        'shared_by': employee,
                        'permission': permission
                    }
                )
                if not created:
                    share.permission = permission
                    share.save()
                
                # Add user to board members if not already
                if target_employee not in board.members.all():
                    board.members.add(target_employee)
                
                # Log activity
                BoardActivity.objects.create(
                    board=board,
                    user=employee,
                    action='share',
                    details=f'Shared board with {target_employee.get_full_name()} ({email}) with {permission} permission',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Board shared with {target_employee.get_full_name()} ({email}).')
                return JsonResponse({'success': True, 'message': 'Board shared successfully'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        
        form = BoardShareForm()
        context = {
            'board': board,
            'form': form,
            'employee': employee,
        }
        
        return render(request, 'employee/boards/board_share.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


@login_required
def board_activity(request, board_id):
    """View board activity logs"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        employee = Employee.objects.get(user=request.user)
        board = get_object_or_404(Board, id=board_id)
        
        # Check if user has access to this board
        if not (board.created_by == employee or 
                employee in board.members.all() or
                BoardShare.objects.filter(board=board, shared_with=employee).exists()):
            messages.error(request, 'You do not have access to this board.')
            return redirect('project_boards')
        
        # Get activities for this board
        activities = BoardActivity.objects.filter(board=board).select_related('user')
        
        # Pagination
        paginator = Paginator(activities, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'board': board,
            'activities': page_obj,
            'employee': employee,
        }
        
        return render(request, 'employee/boards/board_activity.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')


@login_required
def board_activity_list(request):
    """Display all board activities for the user"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')
    
    # Get all boards the user has access to
    accessible_boards = []
    
    # Boards created by user
    created_boards = Board.objects.filter(created_by=employee, is_archived=False)
    accessible_boards.extend(created_boards)
    
    # Boards user is a member of
    member_boards = Board.objects.filter(members=employee, is_archived=False).exclude(created_by=employee)
    accessible_boards.extend(member_boards)
    
    # Boards shared with user
    shared_board_ids = BoardShare.objects.filter(shared_with=employee).values_list('board_id', flat=True)
    shared_boards = Board.objects.filter(id__in=shared_board_ids, is_archived=False).exclude(created_by=employee).exclude(members=employee)
    accessible_boards.extend(shared_boards)
    
    # Get activities from all accessible boards
    board_ids = [board.id for board in accessible_boards]
    activities = BoardActivity.objects.filter(
        board_id__in=board_ids
    ).select_related('board', 'user').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(activities, 50)  # Show 50 activities per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'activities': page_obj,
        'employee': employee,
        'total_boards': len(accessible_boards),
    }
    
    return render(request, 'employee/boards/board_activity_list.html', context)


@login_required
@require_http_methods(["GET"])
def search_employees_for_board_sharing(request):
    """AJAX endpoint to search employees for board sharing"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return JsonResponse({'employees': []})
    
    # Search employees by name or email
    employees = Employee.objects.filter(
        models.Q(user__first_name__icontains=query) |
        models.Q(user__last_name__icontains=query) |
        models.Q(user__email__icontains=query)
    ).select_related('user')[:10]
    
    results = []
    for emp in employees:
        results.append({
            'id': str(emp.id),
            'name': f'{emp.first_name} {emp.last_name}',
            'email': emp.user.email,
            'department': emp.get_department_display()
        })
    
    return JsonResponse({'employees': results})


@login_required
@require_http_methods(["POST"])
def unshare_board(request, board_id, share_id):
    """Remove a board share"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    employee = Employee.objects.get(user=request.user)
    board = get_object_or_404(Board, id=board_id)
    
    # Check if user can manage this board (owner or admin)
    if board.created_by != employee and not employee.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        share = get_object_or_404(BoardShare, id=share_id, board=board)
        shared_with_name = share.shared_with.get_full_name()
        share.delete()
        
        # Log the activity
        BoardActivity.objects.create(
            board=board,
            user=employee,
            action='unshare',
            details=f'removed sharing with {shared_with_name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Board sharing removed for {shared_with_name}')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_board_share(request, board_id, share_id):
    """Update board share permission"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    employee = Employee.objects.get(user=request.user)
    board = get_object_or_404(Board, id=board_id)
    
    # Check if user can manage this board (owner or admin)
    if board.created_by != employee and not employee.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        share = get_object_or_404(BoardShare, id=share_id, board=board)
        new_permission = request.POST.get('permission')
        
        if new_permission not in ['view', 'edit', 'admin']:
            return JsonResponse({'error': 'Invalid permission'}, status=400)
        
        old_permission = share.get_permission_display()
        share.permission = new_permission
        share.save()
        
        # Log the activity
        BoardActivity.objects.create(
            board=board,
            user=employee,
            action='share_update',
            details=f'changed {share.shared_with.get_full_name()} permission from {old_permission} to {share.get_permission_display()}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Permission updated for {share.shared_with.get_full_name()}')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def transfer_board_ownership(request, board_id):
    """Transfer board ownership to another member"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    employee = Employee.objects.get(user=request.user)
    board = get_object_or_404(Board, id=board_id)
    
    # Only the current owner can transfer ownership
    if board.created_by != employee:
        return JsonResponse({'error': 'Only the board owner can transfer ownership'}, status=403)
    
    try:
        new_owner_id = request.POST.get('new_owner_id')
        new_owner = get_object_or_404(Employee, id=new_owner_id)
        
        # Ensure new owner is a member of the board
        if not board.members.filter(id=new_owner.id).exists():
            board.members.add(new_owner)
        
        old_owner_name = employee.get_full_name()
        board.created_by = new_owner
        board.save()
        
        # Log the activity
        BoardActivity.objects.create(
            board=board,
            user=employee,
            action='transfer_ownership',
            details=f'transferred ownership from {old_owner_name} to {new_owner.get_full_name()}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Board ownership transferred to {new_owner.get_full_name()}')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
