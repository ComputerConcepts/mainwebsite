from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db import models
from django.core.paginator import Paginator
from .models import Board, BoardList, Card, CardComment, CardAttachment, Employee
from .views import is_employee_authenticated
import json


@login_required
def project_boards(request):
    """Display all project boards for the authenticated employee"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    employee = Employee.objects.get(email=request.user.email)
    
    # Get boards where user is creator or member
    created_boards = Board.objects.filter(created_by=employee, is_archived=False)
    member_boards = Board.objects.filter(members=employee, is_archived=False).exclude(created_by=employee)
    
    context = {
        'created_boards': created_boards,
        'member_boards': member_boards,
        'total_boards': created_boards.count() + member_boards.count(),
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
            employee = Employee.objects.get(email=request.user.email)
            
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
    
    employee = Employee.objects.get(email=request.user.email)
    
    try:
        board = Board.objects.get(id=board_id)
        
        # Check if user has access to this board
        if board.created_by != employee and employee not in board.members.all():
            messages.error(request, 'You do not have access to this board.')
            return redirect('project_boards')
        
        # Get all lists with their cards
        lists = board.lists.prefetch_related('cards__assigned_to').all()
        
        # Get all employees for assignment dropdown
        all_employees = Employee.objects.all()
        
        context = {
            'board': board,
            'lists': lists,
            'all_employees': all_employees,
            'is_board_owner': board.created_by == employee,
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
        employee = Employee.objects.get(email=request.user.email)
        
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
        employee = Employee.objects.get(email=request.user.email)
        
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
                'created_by': f"{card.created_by.first_name} {card.created_by.last_name}"
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
        employee = Employee.objects.get(email=request.user.email)
        
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
            'created_by': f"{card.created_by.first_name} {card.created_by.last_name}",
            'assigned_to': [
                {
                    'id': str(emp.id),
                    'name': f"{emp.first_name} {emp.last_name}"
                } for emp in card.assigned_to.all()
            ],
            'comments': [
                {
                    'id': str(comment.id),
                    'content': comment.content,
                    'author': f"{comment.author.first_name} {comment.author.last_name}",
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
        employee = Employee.objects.get(email=request.user.email)
        
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
        employee = Employee.objects.get(email=request.user.email)
        
        # Check access to board
        board = card.board_list.board
        if board.created_by != employee and employee not in board.members.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        with transaction.atomic():
            old_list = card.board_list
            new_list = BoardList.objects.get(id=new_list_id)
            
            # Update positions in old list
            old_list.cards.filter(position__gt=card.position).update(
                position=models.F('position') - 1
            )
            
            # Update positions in new list
            new_list.cards.filter(position__gte=new_position).update(
                position=models.F('position') + 1
            )
            
            # Move card
            card.board_list = new_list
            card.position = new_position
            card.save()
        
        return JsonResponse({'success': True, 'message': 'Card moved successfully'})
        
    except (Card.DoesNotExist, BoardList.DoesNotExist):
        return JsonResponse({'error': 'Card or list not found'}, status=404)
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
        employee = Employee.objects.get(email=request.user.email)
        
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
                'author': f"{comment.author.first_name} {comment.author.last_name}",
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except Card.DoesNotExist:
        return JsonResponse({'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_board(request, board_id):
    """Archive a board (soft delete)"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        board = Board.objects.get(id=board_id)
        employee = Employee.objects.get(email=request.user.email)
        
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
