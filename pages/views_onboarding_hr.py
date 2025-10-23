"""
Views for HR Onboarding System
Handles form creation, invitation management, and submission review
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import uuid
import io
import os
from datetime import timedelta

from .models import (
    OnboardingForm, OnboardingFormField, ProspectiveEmployee, 
    OnboardingInvitation, OnboardingSubmission, Employee
)
from .onboarding_emails import OnboardingEmailService


@login_required
def hr_onboarding_dashboard(request):
    """HR dashboard for onboarding system overview"""
    # Check if user has HR permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin']:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')
    
    # Dashboard statistics
    stats = {
        'total_forms': OnboardingForm.objects.filter(is_active=True).count(),
        'total_invitations': OnboardingInvitation.objects.count(),
        'pending_submissions': OnboardingSubmission.objects.filter(review_status='pending').count(),
        'active_prospects': ProspectiveEmployee.objects.filter(is_active=True).count(),
    }
    
    # Recent activity
    recent_submissions = OnboardingSubmission.objects.select_related(
        'invitation__onboarding_form', 'invitation__prospective_employee'
    ).order_by('-submitted_at')[:5]
    
    recent_invitations = OnboardingInvitation.objects.select_related(
        'onboarding_form', 'prospective_employee', 'sent_by'
    ).order_by('-sent_at')[:5]
    
    # Forms overview
    forms = OnboardingForm.objects.filter(is_active=True).annotate(
        invitation_count=Count('onboardinginvitation'),
        submission_count=Count('onboardinginvitation__onboardingsubmission')
    ).order_by('-created_at')
    
    context = {
        'stats': stats,
        'recent_submissions': recent_submissions,
        'recent_invitations': recent_invitations,
        'forms': forms,
    }
    
    return render(request, 'hr/onboarding/dashboard.html', context)


@login_required
def create_onboarding_form(request):
    """Create new onboarding form with custom fields"""
    # Check HR permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin']:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create onboarding form
            form = OnboardingForm.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                created_by=request.user,
                pin_expiry_hours=data.get('pin_expiry_hours', 48),
                allow_multiple_submissions=data.get('allow_multiple_submissions', False),
                send_confirmation_email=data.get('send_confirmation_email', True)
            )
            
            # Create form fields
            for field_data in data.get('fields', []):
                OnboardingFormField.objects.create(
                    onboarding_form=form,
                    field_type=field_data['field_type'],
                    field_name=field_data['field_name'],
                    field_label=field_data['field_label'],
                    placeholder=field_data.get('placeholder', ''),
                    help_text=field_data.get('help_text', ''),
                    is_required=field_data.get('is_required', False),
                    min_length=field_data.get('min_length'),
                    max_length=field_data.get('max_length'),
                    validation_regex=field_data.get('validation_regex', ''),
                    field_options=field_data.get('field_options', []),
                    order=field_data.get('order', 0)
                )
            
            return JsonResponse({
                'success': True,
                'form_id': str(form.id),
                'message': 'Onboarding form created successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating form: {str(e)}'
            }, status=400)
    
    # Field type choices for the form builder
    field_types = OnboardingFormField.FIELD_TYPES
    
    return render(request, 'hr/onboarding/create_form.html', {
        'field_types': field_types
    })


@login_required
def edit_onboarding_form(request, form_id):
    """Edit existing onboarding form"""
    form = get_object_or_404(OnboardingForm, id=form_id)
    
    # Check permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if (employee.department != 'HR' and employee.role not in ['admin', 'super_admin'] 
            and form.created_by != request.user):
            messages.error(request, "Access denied.")
            return redirect('hr_onboarding_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update form
            form.title = data['title']
            form.description = data.get('description', '')
            form.pin_expiry_hours = data.get('pin_expiry_hours', 48)
            form.allow_multiple_submissions = data.get('allow_multiple_submissions', False)
            form.send_confirmation_email = data.get('send_confirmation_email', True)
            form.save()
            
            # Delete existing fields and recreate
            form.fields.all().delete()
            
            for field_data in data.get('fields', []):
                OnboardingFormField.objects.create(
                    onboarding_form=form,
                    field_type=field_data['field_type'],
                    field_name=field_data['field_name'],
                    field_label=field_data['field_label'],
                    placeholder=field_data.get('placeholder', ''),
                    help_text=field_data.get('help_text', ''),
                    is_required=field_data.get('is_required', False),
                    min_length=field_data.get('min_length'),
                    max_length=field_data.get('max_length'),
                    validation_regex=field_data.get('validation_regex', ''),
                    field_options=field_data.get('field_options', []),
                    order=field_data.get('order', 0)
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Form updated successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating form: {str(e)}'
            }, status=400)
    
    # Get existing form data for editing
    form_data = {
        'id': str(form.id),
        'title': form.title,
        'description': form.description,
        'pin_expiry_hours': form.pin_expiry_hours,
        'allow_multiple_submissions': form.allow_multiple_submissions,
        'send_confirmation_email': form.send_confirmation_email,
        'fields': []
    }
    
    for field in form.fields.all():
        form_data['fields'].append({
            'field_type': field.field_type,
            'field_name': field.field_name,
            'field_label': field.field_label,
            'placeholder': field.placeholder,
            'help_text': field.help_text,
            'is_required': field.is_required,
            'min_length': field.min_length,
            'max_length': field.max_length,
            'validation_regex': field.validation_regex,
            'field_options': field.field_options,
            'order': field.order
        })
    
    field_types = OnboardingFormField.FIELD_TYPES
    
    return render(request, 'hr/onboarding/edit_form.html', {
        'form': form,
        'form_data': json.dumps(form_data),
        'field_types': field_types
    })


@login_required
def send_onboarding_invitation(request):
    """Send onboarding invitation to prospective employee"""
    # Check HR permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin']:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        try:
            form_id = request.POST.get('form_id')
            email = request.POST.get('email').lower().strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            custom_message = request.POST.get('custom_message', '').strip()
            
            # Get onboarding form
            onboarding_form = get_object_or_404(OnboardingForm, id=form_id, is_active=True)
            
            # Create or get prospective employee
            prospective_employee, created = ProspectiveEmployee.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'created_by': request.user
                }
            )
            
            # Update info if employee already exists
            if not created:
                prospective_employee.first_name = first_name or prospective_employee.first_name
                prospective_employee.last_name = last_name or prospective_employee.last_name
                prospective_employee.phone = phone or prospective_employee.phone
                prospective_employee.is_active = True
                prospective_employee.save()
            
            # Check if invitation already exists
            existing_invitation = OnboardingInvitation.objects.filter(
                onboarding_form=onboarding_form,
                prospective_employee=prospective_employee
            ).first()
            
            if existing_invitation:
                # Update existing invitation
                invitation = existing_invitation
                invitation.sent_by = request.user
                invitation.sent_at = timezone.now()
                invitation.custom_message = custom_message
                invitation.status = 'sent'
                invitation.save()
            else:
                # Create new invitation
                invitation = OnboardingInvitation.objects.create(
                    onboarding_form=onboarding_form,
                    prospective_employee=prospective_employee,
                    sent_by=request.user,
                    custom_message=custom_message
                )
            
            # Send email
            if OnboardingEmailService.send_onboarding_invitation(invitation, request):
                messages.success(request, f"Onboarding invitation sent to {email}")
            else:
                messages.error(request, f"Failed to send invitation email to {email}")
            
            return redirect('hr_onboarding_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error sending invitation: {str(e)}")
            return redirect('hr_onboarding_dashboard')
    
    # GET request - show invitation form
    forms = OnboardingForm.objects.filter(is_active=True).order_by('title')
    
    return render(request, 'hr/onboarding/send_invitation.html', {
        'forms': forms
    })


@login_required
def onboarding_submissions(request):
    """View and manage onboarding submissions"""
    # Check HR permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin']:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')
    
    # Filters
    status_filter = request.GET.get('status', '')
    form_filter = request.GET.get('form', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    submissions = OnboardingSubmission.objects.select_related(
        'invitation__onboarding_form',
        'invitation__prospective_employee',
        'invitation__sent_by',
        'reviewed_by'
    ).order_by('-submitted_at')
    
    # Apply filters
    if status_filter:
        submissions = submissions.filter(review_status=status_filter)
    
    if form_filter:
        submissions = submissions.filter(invitation__onboarding_form_id=form_filter)
    
    if search_query:
        submissions = submissions.filter(
            Q(invitation__prospective_employee__email__icontains=search_query) |
            Q(invitation__prospective_employee__first_name__icontains=search_query) |
            Q(invitation__prospective_employee__last_name__icontains=search_query) |
            Q(form_data__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    status_choices = OnboardingSubmission.REVIEW_STATUS_CHOICES
    forms = OnboardingForm.objects.filter(is_active=True).order_by('title')
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'form_filter': form_filter,
        'search_query': search_query,
        'status_choices': status_choices,
        'forms': forms,
    }
    
    return render(request, 'hr/onboarding/submissions.html', context)


@login_required
def submission_detail(request, submission_id):
    """View detailed submission information"""
    submission = get_object_or_404(OnboardingSubmission, id=submission_id)
    
    # Check permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin']:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        # Update submission review
        old_status = submission.review_status
        new_status = request.POST.get('review_status')
        review_notes = request.POST.get('review_notes', '').strip()
        hr_notes = request.POST.get('hr_notes', '').strip()
        next_steps = request.POST.get('next_steps', '').strip()
        priority = request.POST.get('priority', 'medium')
        
        submission.review_status = new_status
        submission.review_notes = review_notes
        submission.hr_notes = hr_notes
        submission.next_steps = next_steps
        submission.priority = priority
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save()
        
        # Send status update email if status changed
        if old_status != new_status:
            OnboardingEmailService.send_status_update(
                submission, old_status, new_status, review_notes, request
            )
        
        messages.success(request, "Submission updated successfully!")
        return redirect('hr_submission_detail', submission_id=submission_id)
    
    # Get form fields for display
    form_fields = submission.invitation.onboarding_form.fields.all().order_by('order')
    
    # Organize form data for display
    form_display_data = []
    for field in form_fields:
        value = submission.form_data.get(field.field_name, '')
        form_display_data.append({
            'field': field,
            'value': value
        })
    
    context = {
        'submission': submission,
        'form_display_data': form_display_data,
        'status_choices': OnboardingSubmission.REVIEW_STATUS_CHOICES,
        'priority_choices': [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ]
    }
    
    return render(request, 'hr/onboarding/submission_detail.html', context)


@login_required
def download_combined_pdf(request, submission_id):
    """Download a combined PDF with all submission files"""
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from django.core.files.storage import default_storage
    except ImportError as e:
        messages.error(request, f"PDF generation library not available: {str(e)}")
        return redirect('hr_submission_detail', submission_id=submission_id)
    
    submission = get_object_or_404(OnboardingSubmission, id=submission_id)
    
    # Check permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin'] and not request.user.is_superuser:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('hr_submission_detail', submission_id=submission_id)
    except Employee.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, "Employee profile not found.")
            return redirect('hr_submission_detail', submission_id=submission_id)
    
    try:
        # Create response
        response = HttpResponse(content_type='application/pdf')
        applicant_name = submission.get_applicant_name().replace(' ', '_')
        filename = f"Onboarding_Application_{applicant_name}_{submission.submitted_at.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF with reportlab
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        field_label_style = ParagraphStyle(
            'FieldLabel',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        field_value_style = ParagraphStyle(
            'FieldValue',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leftIndent=20,
            textColor=colors.darkgray
        )
        
        # Build PDF content
        story = []
        
        # Title page
        story.append(Paragraph("Computer Concepts", title_style))
        story.append(Paragraph("Employee Onboarding Application", heading_style))
        story.append(Spacer(1, 20))
        
        # Applicant info
        story.append(Paragraph("Applicant Information", heading_style))
        story.append(Paragraph(f"Name: {submission.get_applicant_name()}", styles['Normal']))
        story.append(Paragraph(f"Email: {submission.invitation.prospective_employee.email}", styles['Normal']))
        
        # Position - check if available in form data or use default
        position = submission.form_data.get('position') or submission.form_data.get('job_title') or submission.form_data.get('role') or 'Not specified'
        story.append(Paragraph(f"Position: {position}", styles['Normal']))
        
        story.append(Paragraph(f"Submission Date: {submission.submitted_at.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Paragraph(f"Status: {submission.get_review_status_display()}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Form fields
        story.append(Paragraph("Application Details", heading_style))
        form_fields = submission.invitation.onboarding_form.fields.all().order_by('order')
        
        for field in form_fields:
            field_name = field.field_name
            value = submission.form_data.get(field_name, '')
            
            story.append(Paragraph(field.field_label, field_label_style))
            
            if field.field_type == 'file':
                if value and isinstance(value, dict) and 'original_name' in value:
                    story.append(Paragraph(f"File: {value.get('original_name', 'Unknown')}", field_value_style))
                else:
                    story.append(Paragraph("No file uploaded", field_value_style))
                    
            elif field.field_type == 'signature':
                if value and isinstance(value, dict) and 'signature_data' in value:
                    story.append(Paragraph("Digital signature provided", field_value_style))
                    
                    # Try to include signature image
                    try:
                        signature_data = value['signature_data']
                        if signature_data and signature_data.startswith('data:image/'):
                            import base64
                            format_part, imgstr = signature_data.split(';base64,')
                            img_data = base64.b64decode(imgstr)
                            img_buffer = io.BytesIO(img_data)
                            
                            # Add signature to PDF
                            img = Image(img_buffer, width=200, height=100)
                            story.append(img)
                            story.append(Spacer(1, 10))
                    except Exception as e:
                        story.append(Paragraph(f"[Signature image could not be processed]", field_value_style))
                else:
                    story.append(Paragraph("No signature provided", field_value_style))
                    
            elif field.field_type == 'checkbox':
                if value:
                    if isinstance(value, list):
                        story.append(Paragraph(", ".join(str(v) for v in value), field_value_style))
                    else:
                        story.append(Paragraph(str(value), field_value_style))
                else:
                    story.append(Paragraph("None selected", field_value_style))
            else:
                display_value = str(value) if value else "Not provided"
                # Clean up the display value to avoid reportlab issues
                display_value = display_value.replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(display_value, field_value_style))
        
        # Add review information if available
        if submission.review_notes or submission.hr_notes:
            story.append(PageBreak())
            story.append(Paragraph("Review Information", heading_style))
            
            if submission.review_notes:
                story.append(Paragraph("Review Notes:", field_label_style))
                clean_notes = submission.review_notes.replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(clean_notes, field_value_style))
                
            if submission.hr_notes:
                story.append(Paragraph("HR Notes:", field_label_style))
                clean_hr_notes = submission.hr_notes.replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(clean_hr_notes, field_value_style))
                
            if submission.reviewed_by:
                story.append(Paragraph(f"Reviewed by: {submission.reviewed_by.get_full_name()}", styles['Normal']))
                
            if submission.reviewed_at:
                story.append(Paragraph(f"Review Date: {submission.reviewed_at.strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Write to response
        response.write(pdf_content)
        return response
        
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('hr_submission_detail', submission_id=submission_id)