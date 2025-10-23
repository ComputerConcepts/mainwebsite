"""
Views for Prospective Employee Onboarding Portal
Handles PIN authentication and form submission
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import os
import uuid
import base64
from datetime import timedelta

from .models import (
    ProspectiveEmployee, OnboardingInvitation, OnboardingSubmission,
    OnboardingForm, OnboardingFormField
)
from .onboarding_emails import OnboardingEmailService


def onboarding_login(request):
    """Login page for prospective employees using PIN"""
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        pin = request.POST.get('pin', '').strip()
        
        if not email or not pin:
            messages.error(request, "Please enter both email and PIN.")
            return render(request, 'onboarding/login.html')
        
        try:
            # Get prospective employee
            prospective_employee = ProspectiveEmployee.objects.get(
                email=email, is_active=True
            )
            
            # Check if PIN is locked
            if prospective_employee.is_pin_locked:
                messages.error(request, "Your PIN has been locked due to too many failed attempts. Please contact HR for assistance.")
                return render(request, 'onboarding/login.html')
            
            # Validate PIN
            if prospective_employee.current_pin == pin and prospective_employee.is_pin_valid():
                # Successful login
                prospective_employee.last_login = timezone.now()
                prospective_employee.login_attempts = 0
                prospective_employee.pin_attempts = 0
                prospective_employee.save()
                
                # Store in session
                request.session['onboarding_prospect_id'] = str(prospective_employee.id)
                request.session['onboarding_email'] = email
                
                # Update any pending invitations status
                OnboardingInvitation.objects.filter(
                    prospective_employee=prospective_employee,
                    status__in=['sent', 'opened']
                ).update(
                    status='opened',
                    first_opened=timezone.now(),
                    last_activity=timezone.now()
                )
                
                messages.success(request, f"Welcome! Please complete your onboarding form.")
                return redirect('onboarding_dashboard')
            else:
                # Failed login
                prospective_employee.pin_attempts += 1
                prospective_employee.login_attempts += 1
                
                # Lock PIN after 5 failed attempts
                if prospective_employee.pin_attempts >= 5:
                    prospective_employee.is_pin_locked = True
                    messages.error(request, "Too many failed PIN attempts. Your PIN has been locked. Please contact HR for assistance.")
                else:
                    remaining = 5 - prospective_employee.pin_attempts
                    messages.error(request, f"Invalid PIN. {remaining} attempts remaining.")
                
                prospective_employee.save()
                
        except ProspectiveEmployee.DoesNotExist:
            messages.error(request, "Invalid email or PIN. Please check your credentials.")
    
    return render(request, 'onboarding/login.html')


def onboarding_dashboard(request):
    """Dashboard showing available onboarding forms for the logged-in prospect"""
    # Check if user is logged in
    prospect_id = request.session.get('onboarding_prospect_id')
    if not prospect_id:
        messages.error(request, "Please log in to access your onboarding forms.")
        return redirect('onboarding_login')
    
    try:
        prospective_employee = ProspectiveEmployee.objects.get(id=prospect_id, is_active=True)
    except ProspectiveEmployee.DoesNotExist:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('onboarding_login')
    
    # Get pending invitations
    invitations = OnboardingInvitation.objects.filter(
        prospective_employee=prospective_employee
    ).select_related('onboarding_form').order_by('-sent_at')
    
    # Check for completed submissions and those needing revision
    completed_invitations = []
    pending_invitations = []
    
    for invitation in invitations:
        try:
            submission = OnboardingSubmission.objects.get(invitation=invitation)
            # Only consider submissions as completed if they're approved
            if submission.review_status == 'approved':
                completed_invitations.append({
                    'invitation': invitation,
                    'submission': submission
                })
            else:
                # Submissions that are pending, under review, rejected, or need revision
                # should appear as pending with relevant feedback
                pending_invitations.append({
                    'invitation': invitation,
                    'submission': submission,
                    'needs_revision': submission.review_status == 'needs_revision',
                    'review_notes': submission.review_notes if submission.review_status == 'needs_revision' else None
                })
        except OnboardingSubmission.DoesNotExist:
            # No submission yet - truly pending
            pending_invitations.append({
                'invitation': invitation,
                'submission': None,
                'needs_revision': False,
                'review_notes': None
            })
    
    context = {
        'prospective_employee': prospective_employee,
        'pending_invitations': pending_invitations,
        'completed_invitations': completed_invitations,
    }
    
    return render(request, 'onboarding/dashboard.html', context)


def onboarding_form(request, invitation_id):
    """Display and handle onboarding form submission"""
    # Check if user is logged in
    prospect_id = request.session.get('onboarding_prospect_id')
    if not prospect_id:
        messages.error(request, "Please log in to access your onboarding forms.")
        return redirect('onboarding_login')
    
    try:
        prospective_employee = ProspectiveEmployee.objects.get(id=prospect_id, is_active=True)
    except ProspectiveEmployee.DoesNotExist:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('onboarding_login')
    
    # Get invitation
    invitation = get_object_or_404(
        OnboardingInvitation,
        id=invitation_id,
        prospective_employee=prospective_employee
    )
    
    # Check if already submitted (unless multiple submissions allowed or needs revision)
    existing_submission = OnboardingSubmission.objects.filter(invitation=invitation).first()
    
    # Allow resubmission if:
    # 1. No existing submission yet
    # 2. Multiple submissions are allowed
    # 3. Existing submission needs revision
    can_submit = (
        not existing_submission or
        invitation.onboarding_form.allow_multiple_submissions or
        (existing_submission and existing_submission.review_status == 'needs_revision')
    )
    
    if existing_submission and not can_submit:
        messages.info(request, "You have already submitted this form and it's currently under review.")
        return redirect('onboarding_dashboard')
    
    if request.method == 'POST':
        try:
            # Collect form data
            form_data = {}
            uploaded_files = []
            
            # Get form fields
            form_fields = invitation.onboarding_form.fields.all()
            
            # Validate and collect data
            validation_errors = []
            
            for field in form_fields:
                field_name = field.field_name
                
                if field.field_type == 'file':
                    # Handle file upload
                    uploaded_file = request.FILES.get(field_name)
                    if uploaded_file:
                        # Validate file
                        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
                            validation_errors.append(f"{field.field_label}: File size must be less than 10MB")
                            continue
                        
                        # Save file
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        filename = f"onboarding/{invitation.id}/{uuid.uuid4()}{file_extension}"
                        file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
                        
                        uploaded_files.append({
                            'field_name': field_name,
                            'original_name': uploaded_file.name,
                            'file_path': file_path,
                            'file_size': uploaded_file.size
                        })
                        
                        form_data[field_name] = {
                            'original_name': uploaded_file.name,
                            'file_path': file_path
                        }
                    elif field.is_required:
                        validation_errors.append(f"{field.field_label}: This field is required")
                
                elif field.field_type == 'checkbox':
                    # Handle checkbox (multiple values)
                    values = request.POST.getlist(field_name)
                    form_data[field_name] = values
                    
                    if field.is_required and not values:
                        validation_errors.append(f"{field.field_label}: This field is required")
                
                elif field.field_type == 'signature':
                    # Handle signature field (base64 image data)
                    signature_data = request.POST.get(field_name, '').strip()
                    
                    if signature_data and signature_data.startswith('data:image/'):
                        # Valid signature data
                        form_data[field_name] = signature_data
                        
                        # Save signature as file for better management
                        import base64
                        
                        try:
                            # Extract base64 data
                            format, imgstr = signature_data.split(';base64,')
                            ext = format.split('/')[-1]
                            
                            # Decode base64 to file
                            signature_file = ContentFile(base64.b64decode(imgstr), name=f'signature_{field_name}.{ext}')
                            
                            # Save signature file
                            filename = f"onboarding/{invitation.id}/signature_{uuid.uuid4()}.{ext}"
                            file_path = default_storage.save(filename, signature_file)
                            
                            uploaded_files.append({
                                'field_name': field_name,
                                'original_name': f'signature_{field_name}.{ext}',
                                'file_path': file_path,
                                'file_size': len(base64.b64decode(imgstr)),
                                'is_signature': True
                            })
                            
                            # Store both base64 and file path
                            form_data[field_name] = {
                                'signature_data': signature_data,
                                'file_path': file_path
                            }
                            
                        except Exception as e:
                            validation_errors.append(f"{field.field_label}: Invalid signature format")
                    
                    elif field.is_required:
                        validation_errors.append(f"{field.field_label}: Digital signature is required")
                
                else:
                    # Handle regular fields
                    value = request.POST.get(field_name, '').strip()
                    form_data[field_name] = value
                    
                    # Validate required fields
                    if field.is_required and not value:
                        validation_errors.append(f"{field.field_label}: This field is required")
                    
                    # Validate length
                    if value:
                        if field.min_length and len(value) < field.min_length:
                            validation_errors.append(f"{field.field_label}: Minimum {field.min_length} characters required")
                        if field.max_length and len(value) > field.max_length:
                            validation_errors.append(f"{field.field_label}: Maximum {field.max_length} characters allowed")
                    
                    # Validate regex pattern
                    if value and field.validation_regex:
                        import re
                        if not re.match(field.validation_regex, value):
                            validation_errors.append(f"{field.field_label}: Invalid format")
            
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                return render(request, 'onboarding/form.html', {
                    'invitation': invitation,
                    'form_fields': form_fields.order_by('order'),
                    'form_data': form_data
                })
            
            # Create or update submission
            if existing_submission and existing_submission.review_status == 'needs_revision':
                # Update existing submission that needs revision
                existing_submission.form_data = form_data
                existing_submission.uploaded_files = uploaded_files
                existing_submission.ip_address = request.META.get('REMOTE_ADDR')
                existing_submission.user_agent = request.META.get('HTTP_USER_AGENT', '')
                existing_submission.review_status = 'pending'  # Reset to pending review
                existing_submission.review_notes = ''  # Clear previous review notes
                existing_submission.reviewed_by = None
                existing_submission.reviewed_at = None
                existing_submission.save()
                submission = existing_submission
                
                messages.success(request, "Your updated onboarding form has been resubmitted successfully!")
            else:
                # Create new submission
                submission = OnboardingSubmission.objects.create(
                    invitation=invitation,
                    form_data=form_data,
                    uploaded_files=uploaded_files,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, "Your onboarding form has been submitted successfully! You will receive email updates on your application status.")
            
            # Update invitation status
            invitation.status = 'completed'
            invitation.completion_date = timezone.now()
            invitation.last_activity = timezone.now()
            invitation.save()
            
            # Send confirmation emails
            if invitation.onboarding_form.send_confirmation_email:
                OnboardingEmailService.send_submission_confirmation(submission, request)
            
            # Send HR notification  
            OnboardingEmailService.send_hr_notification(submission, request)
            
            return redirect('onboarding_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error submitting form: {str(e)}")
    
    # GET request - show form
    form_fields = invitation.onboarding_form.fields.all().order_by('order')
    
    # Get existing submission data if this is a revision
    existing_data = {}
    revision_notes = None
    if existing_submission and existing_submission.review_status == 'needs_revision':
        existing_data = existing_submission.form_data or {}
        revision_notes = existing_submission.review_notes
    
    # Update activity
    invitation.last_activity = timezone.now()
    if invitation.status == 'opened':
        invitation.status = 'in_progress'
    invitation.save()
    
    context = {
        'invitation': invitation,
        'form_fields': form_fields,
        'prospective_employee': prospective_employee,
        'existing_data': existing_data,
        'revision_notes': revision_notes,
        'is_revision': bool(existing_submission and existing_submission.review_status == 'needs_revision'),
    }
    
    return render(request, 'onboarding/form.html', context)


def onboarding_status(request, submission_id):
    """Check status of submitted onboarding form"""
    # Check if user is logged in
    prospect_id = request.session.get('onboarding_prospect_id')
    if not prospect_id:
        messages.error(request, "Please log in to check your application status.")
        return redirect('onboarding_login')
    
    try:
        prospective_employee = ProspectiveEmployee.objects.get(id=prospect_id, is_active=True)
    except ProspectiveEmployee.DoesNotExist:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('onboarding_login')
    
    # Get submission
    submission = get_object_or_404(
        OnboardingSubmission,
        id=submission_id,
        invitation__prospective_employee=prospective_employee
    )
    
    context = {
        'submission': submission,
        'prospective_employee': prospective_employee,
    }
    
    return render(request, 'onboarding/status.html', context)


def onboarding_logout(request):
    """Logout prospective employee"""
    # Clear session
    if 'onboarding_prospect_id' in request.session:
        del request.session['onboarding_prospect_id']
    if 'onboarding_email' in request.session:
        del request.session['onboarding_email']
    
    messages.success(request, "You have been logged out successfully.")
    return redirect('onboarding_login')


@require_http_methods(["GET"])
def form_field_options(request, form_id, field_name):
    """API endpoint to get field options for dynamic forms"""
    try:
        form = OnboardingForm.objects.get(id=form_id, is_active=True)
        field = form.fields.get(field_name=field_name)
        
        return JsonResponse({
            'options': field.field_options,
            'field_type': field.field_type
        })
    except (OnboardingForm.DoesNotExist, OnboardingFormField.DoesNotExist):
        return JsonResponse({'error': 'Field not found'}, status=404)


# Public landing page for onboarding (no login required)
def onboarding_info(request):
    """Public information page about the onboarding process"""
    return render(request, 'onboarding/info.html')