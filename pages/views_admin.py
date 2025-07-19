from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Employee
from .views import is_employee_authenticated
import json
import uuid


def user_can_manage_employees(user):
    """Check if user can manage employees"""
    try:
        employee = Employee.objects.get(user=user)
        return employee.can_manage_users()
    except Employee.DoesNotExist:
        return False


@login_required
def admin_dashboard(request):
    """Admin dashboard with user management overview"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            messages.error(request, 'You do not have permission to access the admin dashboard.')
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, 'Employee record not found.')
        return redirect('employee_login')
    
    # Statistics
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    inactive_employees = total_employees - active_employees
    unverified_employees = Employee.objects.filter(is_email_verified=False).count()
    
    # Department breakdown
    dept_stats = Employee.objects.values('department').annotate(count=Count('id')).order_by('-count')
    
    # Role breakdown
    role_stats = Employee.objects.values('role').annotate(count=Count('id')).order_by('-count')
    
    # Recent hires (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_hires = Employee.objects.filter(hire_date__gte=thirty_days_ago).order_by('-hire_date')[:10]
    
    # Recent activity (you can expand this based on your needs)
    recent_activity = []
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'unverified_employees': unverified_employees,
        'dept_stats': dept_stats,
        'role_stats': role_stats,
        'recent_hires': recent_hires,
        'recent_activity': recent_activity,
        'is_super_admin': current_employee.is_super_admin(),
    }
    
    return render(request, 'employee/admin/dashboard.html', context)


@login_required
def user_management(request):
    """User management page with search and filtering"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            messages.error(request, 'You do not have permission to manage users.')
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, 'Employee record not found.')
        return redirect('employee_login')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    employees = Employee.objects.select_related('user', 'manager').all()
    
    # Apply filters
    if search_query:
        employees = employees.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(position__icontains=search_query)
        )
    
    if department_filter:
        employees = employees.filter(department=department_filter)
    
    if role_filter:
        employees = employees.filter(role=role_filter)
    
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)
    elif status_filter == 'unverified':
        employees = employees.filter(is_email_verified=False)
    
    # Pagination
    paginator = Paginator(employees, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get choices for filters
    departments = Employee.DEPARTMENT_CHOICES
    roles = Employee.ROLE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'roles': roles,
        'search_query': search_query,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'is_super_admin': current_employee.is_super_admin(),
    }
    
    return render(request, 'employee/admin/user_management.html', context)


@login_required
def user_detail(request, user_id):
    """View and edit user details"""
    if not is_employee_authenticated(request):
        return redirect('employee_login')
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            messages.error(request, 'You do not have permission to view user details.')
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, 'Employee record not found.')
        return redirect('employee_login')
    
    employee = get_object_or_404(Employee, id=user_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update user fields
                employee.user.first_name = request.POST.get('first_name', '')
                employee.user.last_name = request.POST.get('last_name', '')
                employee.user.email = request.POST.get('email', '')
                employee.user.save()
                
                # Update employee fields
                employee.department = request.POST.get('department', '')
                employee.position = request.POST.get('position', '')
                employee.phone = request.POST.get('phone', '')
                employee.address = request.POST.get('address', '')
                employee.emergency_contact = request.POST.get('emergency_contact', '')
                employee.emergency_phone = request.POST.get('emergency_phone', '')
                employee.notes = request.POST.get('notes', '')
                
                # Only super admin can change roles
                if current_employee.is_super_admin():
                    employee.role = request.POST.get('role', 'employee')
                    employee.is_active = request.POST.get('is_active') == 'on'
                    employee.is_email_verified = request.POST.get('is_email_verified') == 'on'
                    
                    # Set manager
                    manager_id = request.POST.get('manager')
                    if manager_id:
                        employee.manager = Employee.objects.get(id=manager_id)
                    else:
                        employee.manager = None
                
                employee.save()
                
                messages.success(request, 'User updated successfully.')
                return redirect('user_detail', user_id=user_id)
                
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    # Get potential managers (exclude self and subordinates)
    potential_managers = Employee.objects.filter(
        role__in=['manager', 'admin', 'super_admin']
    ).exclude(id=employee.id)
    
    # Get project board statistics
    from .models import Board, Card
    created_boards = Board.objects.filter(created_by=employee)
    member_boards = Board.objects.filter(members=employee).exclude(created_by=employee)
    
    # Get recent activity (this can be expanded based on your needs)
    recent_activities = []
    
    # Add some sample activities for demonstration
    if employee.user.last_login:
        recent_activities.append({
            'icon': 'sign-in-alt',
            'title': 'Logged in',
            'timestamp': employee.user.last_login
        })
    
    context = {
        'user': employee.user,
        'employee': employee,
        'departments': Employee.DEPARTMENT_CHOICES,
        'roles': Employee.ROLE_CHOICES,
        'potential_managers': potential_managers,
        'is_super_admin': current_employee.is_super_admin(),
        'created_boards_count': created_boards.count(),
        'member_boards_count': member_boards.count(),
        'recent_activities': recent_activities,
    }
    
    return render(request, 'employee/admin/user_detail.html', context)


@login_required
@require_http_methods(["POST"])
def create_user(request):
    """Create a new user"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                is_staff=request.POST.get('role') in ['admin', 'super_admin']
            )
            
            # Generate employee ID
            employee_id = f"EMP{str(uuid.uuid4())[:8].upper()}"
            
            # Create employee record
            employee = Employee.objects.create(
                user=user,
                employee_id=employee_id,
                department=request.POST.get('department', 'Other'),
                position=request.POST.get('position', ''),
                role=request.POST.get('role', 'employee'),
                phone=request.POST.get('phone', ''),
                is_active=True,
                is_email_verified=False
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User created successfully',
                'user_id': str(employee.id),
                'employee_id': employee_id
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        employee = Employee.objects.get(id=user_id)
        employee.is_active = not employee.is_active
        employee.save()
        
        # Also update the user's is_active status
        employee.user.is_active = employee.is_active
        employee.user.save()
        
        status = 'activated' if employee.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'User {status} successfully',
            'is_active': employee.is_active
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def reset_user_password(request, user_id):
    """Reset user password"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        employee = Employee.objects.get(id=user_id)
        
        # Generate temporary password
        temp_password = f"temp_{employee.employee_id}_2024"
        employee.user.set_password(temp_password)
        employee.user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Password reset successfully. Temporary password: {temp_password}',
            'temp_password': temp_password
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def bulk_action(request):
    """Perform bulk actions on users"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.can_manage_users():
            return JsonResponse({'error': 'Permission denied'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({'error': 'No users selected'}, status=400)
        
        employees = Employee.objects.filter(id__in=user_ids)
        count = employees.count()
        
        if action == 'activate':
            employees.update(is_active=True)
            message = f'{count} users activated successfully'
        elif action == 'deactivate':
            employees.update(is_active=False)
            message = f'{count} users deactivated successfully'
        elif action == 'verify_email':
            employees.update(is_email_verified=True, email_verification_token=None)
            message = f'{count} emails verified successfully'
        elif action == 'reset_password':
            for employee in employees:
                temp_password = f"temp_{employee.employee_id}_2024"
                employee.user.set_password(temp_password)
                employee.user.save()
            message = f'Passwords reset for {count} users'
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def verify_user_email(request, user_id):
    """Verify a user's email"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.is_super_admin():
            return JsonResponse({'error': 'Only super administrators can verify emails'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        employee = get_object_or_404(Employee, id=user_id)
        employee.is_email_verified = True
        employee.email_verification_token = None
        employee.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Email verified for {employee.user.get_full_name() or employee.user.username}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def unverify_user_email(request, user_id):
    """Unverify a user's email"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.is_super_admin():
            return JsonResponse({'error': 'Only super administrators can unverify emails'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        employee = get_object_or_404(Employee, id=user_id)
        employee.is_email_verified = False
        employee.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Email unverified for {employee.user.get_full_name() or employee.user.username}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def send_verification_email(request, user_id):
    """Send verification email to user"""
    if not is_employee_authenticated(request):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        if not current_employee.is_super_admin():
            return JsonResponse({'error': 'Only super administrators can send verification emails'}, status=403)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found'}, status=404)
    
    try:
        employee = get_object_or_404(Employee, id=user_id)
        
        # Generate verification token if not exists
        if not employee.email_verification_token:
            import secrets
            employee.email_verification_token = secrets.token_urlsafe(32)
            employee.save()
        
        # Import email sending function
        from .views import send_verification_email_to_user
        
        # Send verification email
        success = send_verification_email_to_user(employee)
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': f'Verification email sent to {employee.user.email}'
            })
        else:
            return JsonResponse({'error': 'Failed to send verification email'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
