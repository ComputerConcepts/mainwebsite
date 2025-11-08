"""
Tax Form Views - Handle tax form management and client interactions
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
import os
from django.conf import settings
import json
import base64
import uuid
import os
import logging
from datetime import datetime, timedelta

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO

from .models import (
    TaxFormTemplate, TaxFormField, TaxClient, TaxClientWaiver, TaxFormAssignment, 
    TaxFormSubmission, TaxDocument
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_tax_staff(user):
    """Check if user is tax preparation staff"""
    if not user.is_authenticated:
        return False

    if user.is_staff or user.groups.filter(name='Tax Preparers').exists():
        return True

    employee = getattr(user, 'employee', None)
    if not employee:
        return False

    # Allow managers/admins and anyone explicitly in a tax department/role
    if getattr(employee, 'role', '') in ['manager', 'admin', 'super_admin']:
        return True

    department = (getattr(employee, 'department', '') or '').lower()
    position = (getattr(employee, 'position', '') or '').lower()
    return 'tax' in department or 'tax' in position

def is_employee(user):
    """Check if user is an employee (for accessing admin features)"""
    return user.is_authenticated and (user.is_staff or hasattr(user, 'employee'))

def send_client_welcome_email(client):
    """Send welcome email to newly created tax client"""
    from django.contrib.sites.models import Site
    from django.core.mail import EmailMultiAlternatives
    
    try:
        # Get current site domain
        current_site = Site.objects.get_current()
        domain = getattr(settings, 'SITE_DOMAIN', current_site.domain)
        protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
        site_url = f"{protocol}://{domain}"
        
        # Email context
        context = {
            'client': client,
            'site_url': site_url,
            'domain': domain,
        }
        
        # Render email templates
        subject = f"Welcome to One Computer Concepts Tax Preparation - Your PIN: {client.current_pin}"
        html_content = render_to_string('email/client_welcome.html', context)
        text_content = render_to_string('email/client_welcome.txt', context)
        
        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[client.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return True
        
    except Exception as e:
        # Log the error (you might want to use proper logging here)
        print(f"Failed to send welcome email to {client.email}: {str(e)}")
        raise e


def send_form_completion_email(assignment, completed_by):
    """Send email notification to client when form is completed and ready for signature"""
    logger = logging.getLogger(__name__)
    
    try:
        # Build the login URL
        from django.urls import reverse
        from django.contrib.sites.models import Site
        
        preferred_domain = (getattr(settings, 'SITE_DOMAIN', None) or os.environ.get('SITE_DOMAIN', '')).strip()
        use_https = getattr(settings, 'USE_HTTPS', False) or os.environ.get('USE_HTTPS', '').lower() == 'true'

        if preferred_domain and preferred_domain.lower() != 'example.com':
            domain = preferred_domain
        else:
            # Try to get domain from Django Sites framework
            try:
                current_site = Site.objects.get_current()
                domain = current_site.domain.strip()
            except Site.DoesNotExist:
                domain = ''

            if not domain or domain.lower() == 'example.com':
                # Final fallback to localhost for development
                domain = 'localhost:8000'

        # Strip any accidental protocol prefixes kept in the domain value
        if domain.startswith('http://') or domain.startswith('https://'):
            domain = domain.split('://', 1)[1]

        is_local = domain.startswith('localhost') or domain.startswith('127.0.0.1')
        if use_https:
            protocol = 'https'
        else:
            protocol = 'http' if is_local else 'https'

        login_url = f"{protocol}://{domain}{reverse('tax_client_login')}"
        
        # Prepare email context
        context = {
            'client': assignment.client,
            'tax_form': assignment.tax_form,
            'completed_by': completed_by,
            'completion_date': timezone.now(),
            'login_url': login_url,
        }
        
        # Render email content
        html_message = render_to_string('email/tax_form_ready.html', context)
        
        # Create plain text version
        plain_message = f"""
Hello {assignment.client.first_name},

Your tax form "{assignment.tax_form.name}" has been completed by our tax preparation team and is now ready for your review and digital signature.

To access your form:
1. Visit: {login_url}
2. Login with:
   Email: {assignment.client.email}
   PIN: {assignment.client.current_pin}

Please review the information carefully and provide your digital signature to complete the process.

If you have any questions, please contact our tax preparation team.

Best regards,
Computer Concepts Tax Team
        """.strip()
        
        # Send email
        send_mail(
            subject=f'Your Tax Form "{assignment.tax_form.name}" is Ready for Review',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assignment.client.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Form completion email sent to {assignment.client.email} for form {assignment.tax_form.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send form completion email to {assignment.client.email}: {str(e)}")
        return False


# =============================================================================
# ADMIN VIEWS (Tax Staff)
# =============================================================================

@login_required
@user_passes_test(is_employee)
def tax_admin_dashboard(request):
    """Tax admin dashboard showing forms and client submissions"""
    # Get summary statistics
    stats = {
        'total_clients': TaxClient.objects.filter(is_active=True).count(),
        'active_assignments': TaxFormAssignment.objects.filter(
            status__in=['assigned', 'in_progress']
        ).count(),
        'pending_reviews': TaxFormSubmission.objects.filter(
            review_status='pending'
        ).count(),
        'completed_forms': TaxFormSubmission.objects.filter(
            review_status='approved'
        ).count(),
    }
    
    # Recent submissions
    recent_submissions = TaxFormSubmission.objects.select_related(
        'assignment__client', 'assignment__tax_form'
    ).order_by('-submitted_at')[:10]
    
    # Forms needing review
    needs_review = TaxFormSubmission.objects.filter(
        review_status='pending'
    ).select_related('assignment__client', 'assignment__tax_form')[:5]
    
    context = {
        'stats': stats,
        'recent_submissions': recent_submissions,
        'needs_review': needs_review,
    }
    
    return render(request, 'tax/admin/dashboard.html', context)


@login_required
@user_passes_test(is_tax_staff)
def tax_form_templates(request):
    """Manage tax form templates"""
    templates = TaxFormTemplate.objects.filter(is_active=True).order_by('form_type', 'name')
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'tax/admin/form_templates.html', context)


@login_required
@user_passes_test(is_tax_staff)
def create_tax_form_template(request):
    """Create a new tax form template"""
    if request.method == 'POST':
        try:
            template = TaxFormTemplate.objects.create(
                name=request.POST['name'],
                form_type=request.POST['form_type'],
                description=request.POST.get('description', ''),
                instructions=request.POST.get('instructions', ''),
                requires_signature=request.POST.get('requires_signature') == 'on',
                allow_multiple_submissions=request.POST.get('allow_multiple_submissions') == 'on',
                created_by=request.user
            )
            
            messages.success(request, f"Tax form template '{template.name}' created successfully!")
            return redirect('edit_tax_form_template', template_id=template.id)
            
        except Exception as e:
            messages.error(request, f"Error creating template: {str(e)}")
    
    form_type_choices = TaxFormTemplate._meta.get_field('form_type').choices
    
    context = {
        'form_type_choices': form_type_choices,
    }
    
    return render(request, 'tax/admin/create_template.html', context)


@login_required
@user_passes_test(is_tax_staff)
def edit_tax_form_template(request, template_id):
    """Edit tax form template and its fields"""
    template = get_object_or_404(TaxFormTemplate, id=template_id)
    fields = template.fields.filter(is_active=True).order_by('section', 'order')
    
    if request.method == 'POST':
        # Update template info
        template.name = request.POST.get('name', template.name)
        template.description = request.POST.get('description', template.description)
        template.instructions = request.POST.get('instructions', template.instructions)
        template.requires_signature = request.POST.get('requires_signature') == 'on'
        template.allow_multiple_submissions = request.POST.get('allow_multiple_submissions') == 'on'
        template.save()
        
        messages.success(request, "Template updated successfully!")
        return redirect('edit_tax_form_template', template_id=template.id)
    
    field_type_choices = TaxFormField._meta.get_field('field_type').choices
    
    context = {
        'template': template,
        'fields': fields,
        'field_type_choices': field_type_choices,
        'sections': list(set(f.section for f in fields if f.section)),
    }
    
    return render(request, 'tax/admin/edit_template.html', context)


@login_required
@user_passes_test(is_tax_staff)
def add_form_field(request, template_id):
    """Add a field to a tax form template"""
    template = get_object_or_404(TaxFormTemplate, id=template_id)
    
    if request.method == 'POST':
        try:
            # Parse field options if provided
            field_options = []
            if request.POST.get('field_options'):
                options_text = request.POST['field_options'].strip()
                if options_text:
                    field_options = [opt.strip() for opt in options_text.split('\\n') if opt.strip()]
            
            field = TaxFormField.objects.create(
                tax_form=template,
                field_type=request.POST['field_type'],
                field_name=request.POST['field_name'],
                field_label=request.POST['field_label'],
                placeholder=request.POST.get('placeholder', ''),
                help_text=request.POST.get('help_text', ''),
                section=request.POST.get('section', ''),
                is_required=request.POST.get('is_required') == 'on',
                field_options=field_options,
                order=int(request.POST.get('order', 0)),
                column_width=request.POST.get('column_width', 'full'),
                tax_line_reference=request.POST.get('tax_line_reference', ''),
                min_length=int(request.POST['min_length']) if request.POST.get('min_length') else None,
                max_length=int(request.POST['max_length']) if request.POST.get('max_length') else None,
            )
            
            return JsonResponse({'success': True, 'field_id': str(field.id)})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@user_passes_test(is_tax_staff)
def manage_clients(request):
    """Manage tax clients"""
    clients = TaxClient.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'clients': clients,
    }
    
    return render(request, 'tax/admin/clients.html', context)


@login_required
@user_passes_test(is_tax_staff)
def create_client(request):
    """Create a new tax client"""
    import random
    
    if request.method == 'POST':
        try:
            # Get the auto-generated PIN from the form
            pin = request.POST.get('access_pin', '')
            if not pin or len(pin) != 4:
                # Generate new PIN if not provided or invalid
                pin = f"{random.randint(1000, 9999)}"
            
            client = TaxClient.objects.create(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                phone=request.POST.get('phone', ''),
                address_line1=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                state=request.POST.get('state', ''),
                zip_code=request.POST.get('zip_code', ''),
                ssn=request.POST.get('ssn', ''),
                date_of_birth=datetime.strptime(request.POST['date_of_birth'], '%Y-%m-%d').date() if request.POST.get('date_of_birth') else None,
                current_pin=pin,
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            # Send welcome email to the new client
            email_sent = False
            try:
                send_client_welcome_email(client)
                email_sent = True
            except Exception as email_error:
                # Log the error but don't fail the client creation
                messages.warning(request, f"Client created successfully, but welcome email failed to send: {str(email_error)}")
            
            action = request.POST.get('action', 'save')
            if action == 'save_and_assign':
                success_msg = f"Client '{client.full_name}' created successfully! PIN: {pin}."
                if email_sent:
                    success_msg += f" Welcome email sent to {client.email}."
                success_msg += " Please complete the waiver next."
                messages.success(request, success_msg)
                return redirect('client_waiver', client_id=client.id)
            else:
                success_msg = f"Client '{client.full_name}' created successfully! PIN: {pin}."
                if email_sent:
                    success_msg += f" Welcome email sent to {client.email}."
                messages.success(request, success_msg)
                return redirect('manage_tax_clients')
            
        except Exception as e:
            messages.error(request, f"Error creating client: {str(e)}")
    
    # Generate a random PIN for display
    auto_pin = f"{random.randint(1000, 9999)}"
    
    context = {
        'auto_pin': auto_pin,
    }
    
    return render(request, 'tax/admin/create_client.html', context)


@login_required
@user_passes_test(is_tax_staff)
def client_waiver(request, client_id):
    """View client waiver status (read-only for employees)"""
    from django.utils import timezone
    
    client = get_object_or_404(TaxClient, id=client_id)
    
    # Get or create waiver record
    waiver, created = TaxClientWaiver.objects.get_or_create(
        client=client,
        defaults={'waiver_version': '1.0'}
    )
    
    # Handle only employee notes and witnessing (no client signature)
    if request.method == 'POST':
        try:
            # Only allow employee to add notes and witness (if client already signed)
            if waiver.client_signed:
                # Employee witness
                if request.POST.get('employee_witness') == 'on':
                    waiver.employee_witnessed = True
                    waiver.witnessed_by = request.user
                    waiver.witnessed_at = timezone.now()
                
                # Notes
                waiver.notes = request.POST.get('notes', '')
                waiver.save()
                
                messages.success(request, f"Waiver witness information updated for {client.full_name}.")
            else:
                messages.error(request, "Client must sign the waiver first before employee can witness it.")
                
        except Exception as e:
            messages.error(request, f"Error updating waiver: {str(e)}")
        
        return redirect('client_waiver', client_id=client.id)
    
    # Build client login URL for instructions
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    domain = getattr(settings, 'SITE_DOMAIN', current_site.domain)
    protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
    client_waiver_url = f"{protocol}://{domain}/tax/waiver/"
    
    context = {
        'client': client,
        'waiver': waiver,
        'is_new_waiver': created,
        'client_waiver_url': client_waiver_url,
        'is_employee_view': True,
    }
    
    return render(request, 'tax/admin/client_waiver_status.html', context)


def tax_client_waiver(request):
    """Client-side waiver signing (requires PIN authentication)"""
    from django.utils import timezone
    
    # Check if client is authenticated via session
    client_id = request.session.get('tax_client_id')
    if not client_id:
        messages.error(request, "Please log in with your PIN to access the waiver.")
        return redirect('tax_client_login')
    
    client = get_object_or_404(TaxClient, id=client_id)
    
    # Get or create waiver record
    waiver, created = TaxClientWaiver.objects.get_or_create(
        client=client,
        defaults={'waiver_version': '1.0'}
    )
    
    if request.method == 'POST':
        try:
            # Update consent fields (client can modify these)
            waiver.consent_data_processing = request.POST.get('consent_data_processing') == 'on'
            waiver.consent_document_storage = request.POST.get('consent_document_storage') == 'on'
            waiver.consent_electronic_delivery = request.POST.get('consent_electronic_delivery') == 'on'
            waiver.consent_third_party_disclosure = request.POST.get('consent_third_party_disclosure') == 'on'
            
            # Handle client signature
            signature_data = request.POST.get('signature_data', '')
            if signature_data:
                waiver.client_signature_data = signature_data
                waiver.client_signed = True
                waiver.client_signed_at = timezone.now()
                waiver.client_ip_address = request.META.get('REMOTE_ADDR')
            
            waiver.save()
            
            if waiver.is_completed:
                messages.success(request, "Waiver completed successfully! Your tax preparer can now assign forms to you.")
                return redirect('tax_client_dashboard')
            else:
                messages.warning(request, f"Waiver saved. Status: {waiver.completion_status}")
                
        except Exception as e:
            messages.error(request, f"Error saving waiver: {str(e)}")
    
    context = {
        'client': client,
        'waiver': waiver,
        'is_new_waiver': created,
        'is_client_view': True,
    }
    
    return render(request, 'tax/client/waiver.html', context)


@login_required
@user_passes_test(is_tax_staff)
def assign_forms(request, client_id):
    """Assign tax forms to a client"""
    client = get_object_or_404(TaxClient, id=client_id)
    
    # Check if client has completed waiver before allowing form assignment
    if not client.can_be_assigned_forms():
        messages.error(request, f"Please complete the waiver for {client.full_name} before assigning tax forms.")
        return redirect('client_waiver', client_id=client.id)
    
    if request.method == 'POST':
        form_ids = request.POST.getlist('form_ids')
        due_date = request.POST.get('due_date')
        instructions = request.POST.get('custom_instructions', '')
        
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        assigned_count = 0
        for form_id in form_ids:
            try:
                tax_form = TaxFormTemplate.objects.get(id=form_id)
                assignment, created = TaxFormAssignment.objects.get_or_create(
                    tax_form=tax_form,
                    client=client,
                    defaults={
                        'assigned_by': request.user,
                        'due_date': due_date_obj,
                        'custom_instructions': instructions,
                    }
                )
                if created:
                    assigned_count += 1
            except TaxFormTemplate.DoesNotExist:
                continue
        
        messages.success(request, f"Assigned {assigned_count} forms to {client.full_name}")
        return redirect('manage_tax_clients')
    
    # Get available forms and existing assignments
    available_templates = TaxFormTemplate.objects.filter(is_active=True)
    existing_assignments = TaxFormAssignment.objects.filter(client=client)
    assigned_form_ids = existing_assignments.values_list('tax_form_id', flat=True)
    
    context = {
        'client': client,
        'available_templates': available_templates,
        'assigned_assignments': existing_assignments,
        'assigned_form_ids': assigned_form_ids,
        'today': timezone.now().date(),
    }
    
    return render(request, 'tax/admin/assign_forms.html', context)


@login_required
@user_passes_test(is_tax_staff)
def client_detail(request, client_id):
    """View client details and form assignments"""
    client = get_object_or_404(TaxClient, id=client_id)
    assignments = TaxFormAssignment.objects.filter(client=client).select_related('tax_form')
    
    context = {
        'client': client,
        'assignments': assignments,
    }
    
    return render(request, 'tax/admin/client_detail.html', context)


@login_required
@user_passes_test(is_tax_staff)
def client_forms(request, client_id):
    """View and manage client's assigned forms"""
    client = get_object_or_404(TaxClient, id=client_id)
    assignments = TaxFormAssignment.objects.filter(client=client).select_related('tax_form')
    
    context = {
        'client': client,
        'assignments': assignments,
    }
    
    return render(request, 'tax/admin/client_forms.html', context)


@login_required
@user_passes_test(is_tax_staff)
def employee_fill_form(request, assignment_id):
    """Allow employees to fill out forms on behalf of clients"""
    assignment = get_object_or_404(TaxFormAssignment, id=assignment_id)
    
    # Check if there's an existing submission
    try:
        submission = TaxFormSubmission.objects.get(assignment=assignment)
    except TaxFormSubmission.DoesNotExist:
        submission = None
    
    if request.method == 'POST':
        # Handle form submission
        form_data = {}
        
        # Process all form fields
        for field in assignment.tax_form.fields.all():
            field_name = f"field_{field.id}"
            field_value = request.POST.get(field_name, '')
            if field_value:
                form_data[field.field_name] = field_value
        
        # Get employee confirmation
        employee_confirmation = request.POST.get('employee_confirmation') == 'yes'
        internal_notes = request.POST.get('internal_notes', '')
        
        if not employee_confirmation:
            messages.error(request, "Please confirm that the information is accurate before submitting.")
            return redirect('employee_fill_form', assignment_id=assignment_id)
        
        if submission:
            # Update existing submission
            submission.form_data = form_data
            submission.internal_notes = internal_notes
            submission.employee_completed_at = timezone.now()
            submission.submitted_by = request.user
            submission.save()
        else:
            # Create new submission
            submission = TaxFormSubmission.objects.create(
                assignment=assignment,
                form_data=form_data,
                internal_notes=internal_notes,
                employee_completed_at=timezone.now(),
                submitted_by=request.user,
                is_completed=False  # Not completed until client signs
            )
        
        # Update assignment status to ready for client signature
        assignment.status = 'ready_for_signature'
        assignment.save()
        
        # Send email notification to client
        email_sent = send_form_completion_email(assignment, request.user)
        if email_sent:
            messages.success(request, f"Form '{assignment.tax_form.name}' sent to client for signature! Notification email sent to {assignment.client.email}")
        else:
            messages.warning(request, f"Form '{assignment.tax_form.name}' sent to client for signature! However, there was an issue sending the email notification.")
        
        return redirect('tax_client_detail', client_id=assignment.client.id)
    
    # Get form fields with their current values
    form_fields = []
    existing_values = {}
    if submission and submission.form_data:
        existing_values = submission.form_data
    
    for field in assignment.tax_form.fields.filter(is_active=True).order_by('section', 'order', 'id'):
        # Skip signature fields - these are only for client signing, not employee filling
        # Also skip section headers as they are just for organization/display
        if field.field_type in ['signature', 'electronic_signature', 'section_header']:
            continue
            
        field_data = {
            'id': field.id,
            'field_name': field.field_name,
            'field_label': field.field_label,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'help_text': field.help_text,
            'placeholder': field.placeholder,
            'field_options': field.field_options,
            'current_value': existing_values.get(field.field_name, ''),
        }
        form_fields.append(field_data)
    
    context = {
        'assignment': assignment,
        'client': assignment.client,
        'tax_form': assignment.tax_form,
        'form_fields': form_fields,
        'submission': submission,
        'is_employee_filling': True,
        'enforce_field_requirements': False,
    }
    
    return render(request, 'tax/admin/employee_fill_form.html', context)


@login_required
@user_passes_test(is_tax_staff)
def view_tax_assignment(request, assignment_id):
    """View a tax assignment and its submission details (read-only for employees)"""
    assignment = get_object_or_404(TaxFormAssignment, id=assignment_id)
    
    # Get the submission if it exists
    try:
        submission = TaxFormSubmission.objects.get(assignment=assignment)
    except TaxFormSubmission.DoesNotExist:
        submission = None
    
    # Get form fields with their submitted values
    form_fields = []
    existing_values = submission.form_data if submission and submission.form_data else {}
    
    for field in assignment.tax_form.fields.filter(is_active=True).order_by('section', 'order', 'id'):
        field_data = {
            'id': field.id,
            'field_name': field.field_name,
            'field_label': field.field_label,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'help_text': field.help_text,
            'section': field.section,
            'current_value': existing_values.get(field.field_name, ''),
        }
        form_fields.append(field_data)
    
    context = {
        'assignment': assignment,
        'client': assignment.client,
        'tax_form': assignment.tax_form,
        'form_fields': form_fields,
        'submission': submission,
        'is_read_only': True,
    }
    
    return render(request, 'tax/admin/view_assignment.html', context)


@login_required
@user_passes_test(is_tax_staff)
def export_tax_assignment_pdf(request, assignment_id):
    """Export tax assignment as PDF"""
    assignment = get_object_or_404(TaxFormAssignment, id=assignment_id)
    
    # Get the submission if it exists
    try:
        submission = TaxFormSubmission.objects.get(assignment=assignment)
    except TaxFormSubmission.DoesNotExist:
        submission = None
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tax_assignment_{assignment.client.last_name}_{assignment.tax_form.name.replace(" ", "_")}.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=TA_CENTER)
    header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=14, spaceAfter=12, textColor=colors.darkblue)
    normal_style = styles['Normal']
    
    # Title
    title = Paragraph(f"Tax Form: {assignment.tax_form.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Client Information Header
    client_info = [
        ['Client Information', ''],
        ['Name:', f"{assignment.client.full_name}"],
        ['Email:', assignment.client.email],
        ['Phone:', assignment.client.phone or 'Not provided'],
        ['Status:', assignment.get_status_display()],
    ]
    
    if submission:
        if submission.employee_completed_at:
            client_info.append(['Completed by:', submission.submitted_by.get_full_name() or submission.submitted_by.username])
            client_info.append(['Employee Completion:', submission.employee_completed_at.strftime('%B %d, %Y at %I:%M %p')])
        if submission.client_signed_at:
            client_info.append(['Client Signed:', submission.client_signed_at.strftime('%B %d, %Y at %I:%M %p')])
            if submission.is_completed:
                client_info.append(['Final Completion:', submission.client_signed_at.strftime('%B %d, %Y at %I:%M %p')])
    
    client_table = Table(client_info, colWidths=[2*inch, 4*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(client_table)
    elements.append(Spacer(1, 20))
    
    # Form Fields
    form_fields = []
    existing_values = submission.form_data if submission and submission.form_data else {}
    
    for field in assignment.tax_form.fields.filter(is_active=True).order_by('section', 'order', 'id'):
        field_data = {
            'field_name': field.field_name,
            'field_label': field.field_label,
            'field_type': field.field_type,
            'section': field.section,
            'current_value': existing_values.get(field.field_name, ''),
        }
        form_fields.append(field_data)
    
    # Group fields by section
    sections = {}
    for field in form_fields:
        section = field['section'] or 'General'
        if section not in sections:
            sections[section] = []
        sections[section].append(field)
    
    # Add form data by section
    for section_name, section_fields in sections.items():
        # Section header
        section_header = Paragraph(section_name, header_style)
        elements.append(section_header)
        
        # Special handling for Monthly Income
        if section_name == "Monthly Income":
            monthly_data = [['Month', 'Service', 'Amount Made']]
            total_amount = 0
            
            # Process monthly income fields
            for field in section_fields:
                if '- service' in field['field_name']:
                    month = field['field_name'].replace('_service', '').replace('_', ' ').title()
                    service = field['current_value'] or '—'
                    
                    # Find corresponding amount field
                    amount_field_name = field['field_name'].replace('_service', '_amount')
                    amount = '—'
                    for f in section_fields:
                        if f['field_name'] == amount_field_name:
                            if f['current_value']:
                                amount = f'${f["current_value"]}'
                                try:
                                    total_amount += float(f['current_value'])
                                except ValueError:
                                    pass
                            break
                    
                    monthly_data.append([month, service, amount])
            
            # Add total row
            monthly_data.append(['TOTAL', '', f'${total_amount:.2f}'])
            
            monthly_table = Table(monthly_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch])
            monthly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Right align amounts
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Total row
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(monthly_table)
            
        # Special handling for Dependent Care
        elif "Dependent" in section_name and "Standard" in section_name:
            dependent_data = [['#', 'Child Name', 'SSN', 'Daycare/Provider', 'FEIN', 'Amount Paid']]
            
            for i in range(1, 5):  # Up to 4 dependents
                name_field = f'dependent_{i}_name'
                name = next((f['current_value'] for f in section_fields if f['field_name'] == name_field), '')
                
                if name:  # Only show if name is provided
                    ssn = next((f['current_value'] for f in section_fields if f['field_name'] == f'dependent_{i}_ssn'), '—')
                    daycare = next((f['current_value'] for f in section_fields if f['field_name'] == f'dependent_{i}_daycare_name'), '—')
                    fein = next((f['current_value'] for f in section_fields if f['field_name'] == f'dependent_{i}_fein'), '—')
                    amount = next((f['current_value'] for f in section_fields if f['field_name'] == f'dependent_{i}_amount'), '—')
                    if amount and amount != '—':
                        amount = f'${amount}'
                    
                    dependent_data.append([str(i), name, ssn, daycare, fein, amount])
            
            if len(dependent_data) > 1:  # Only create table if there are dependents
                dependent_table = Table(dependent_data, colWidths=[0.3*inch, 1.5*inch, 1.2*inch, 1.5*inch, 1*inch, 0.8*inch])
                dependent_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Right align amounts
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(dependent_table)
            else:
                elements.append(Paragraph("No dependent care information provided.", normal_style))
                
        else:
            # Regular fields display
            field_data = []
            for field in section_fields:
                if field['field_type'] != 'section_header':
                    value = field['current_value'] or 'Not provided'
                    if field['field_type'] == 'signature':
                        value = 'Signature captured' if field['current_value'] else 'Signature pending'
                    elif field['field_type'] == 'currency' and field['current_value']:
                        value = f"${field['current_value']}"
                    
                    field_data.append([field['field_label'], value])
            
            if field_data:
                field_table = Table(field_data, colWidths=[2.5*inch, 3.5*inch])
                field_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                elements.append(field_table)
        
        elements.append(Spacer(1, 15))
    
    # Internal Notes
    if submission and submission.internal_notes:
        notes_header = Paragraph("Internal Notes", header_style)
        elements.append(notes_header)
        notes_content = Paragraph(submission.internal_notes.replace('\n', '<br/>'), normal_style)
        elements.append(notes_content)
        elements.append(Spacer(1, 15))
    
    # Footer
    footer_text = f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')} | Computer Concepts Tax Preparation"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey))
    elements.append(Spacer(1, 20))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


# =============================================================================
# CLIENT VIEWS (Public Access)
# =============================================================================

def tax_client_login(request):
    """Client login using email and PIN"""
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        pin = request.POST.get('pin', '').strip()
        
        # Debug logging
        print(f"DEBUG: Login attempt - Email: '{email}', PIN: '{pin}', PIN length: {len(pin)}")
        
        try:
            client = TaxClient.objects.get(email=email, is_active=True)
            print(f"DEBUG: Found client - Email: '{client.email}', Stored PIN: '{client.current_pin}', Stored PIN length: {len(client.current_pin) if client.current_pin else 0}")
            
            # Check PIN (no expiry check)
            if client.current_pin == pin:
                # Login successful
                request.session['tax_client_id'] = str(client.id)
                client.last_login = timezone.now()
                client.save()
                
                messages.success(request, f"Welcome back, {client.first_name}!")
                return redirect('tax_client_dashboard')
            else:
                print(f"DEBUG: PIN mismatch - Expected: '{client.current_pin}', Received: '{pin}'")
                messages.error(request, f"Invalid PIN. Please check your PIN and try again. (Expected length: {len(client.current_pin) if client.current_pin else 0}, Got length: {len(pin)})")
                
        except TaxClient.DoesNotExist:
            print(f"DEBUG: Client not found for email: '{email}'")
            messages.error(request, "Client not found. Please check your email address.")
    
    return render(request, 'tax/client/login.html')


def tax_client_debug(request):
    """Debug view to show client information"""
    clients = TaxClient.objects.all()
    debug_info = []
    for client in clients:
        debug_info.append({
            'email': client.email,
            'pin': client.current_pin,
            'pin_length': len(client.current_pin) if client.current_pin else 0,
            'is_active': client.is_active,
            'first_name': client.first_name,
        })
    
    return JsonResponse({'clients': debug_info})


def tax_client_logout(request):
    """Client logout"""
    if 'tax_client_id' in request.session:
        del request.session['tax_client_id']
    messages.info(request, "You have been logged out successfully.")
    return redirect('tax_client_login')


def tax_client_dashboard(request):
    """Client dashboard showing assigned forms"""
    # Check if client is logged in
    client_id = request.session.get('tax_client_id')
    if not client_id:
        messages.error(request, "Please log in to access your tax forms.")
        return redirect('tax_client_login')
    
    try:
        client = TaxClient.objects.get(id=client_id, is_active=True)
    except TaxClient.DoesNotExist:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('tax_client_login')
    
    # Get client's waiver status
    try:
        waiver = TaxClientWaiver.objects.get(client=client)
    except TaxClientWaiver.DoesNotExist:
        waiver = None
    
    # If waiver doesn't exist or isn't completed, redirect to waiver page
    if not waiver or not waiver.is_completed:
        messages.info(request, "Please complete your waiver before accessing tax forms.")
        return redirect('tax_client_waiver')
    
    # Get client's form assignments
    assignments = TaxFormAssignment.objects.filter(
        client=client
    ).select_related('tax_form').order_by('-assigned_at')
    
    # Separate by status: pending, ready for signature, and completed
    pending_assignments = []
    ready_for_signature = []
    completed_assignments = []
    
    for assignment in assignments:
        try:
            submission = TaxFormSubmission.objects.get(assignment=assignment)
            
            if submission.is_completed and submission.review_status == 'approved':
                # Fully completed and approved
                completed_assignments.append({
                    'assignment': assignment,
                    'submission': submission
                })
            elif assignment.status == 'ready_for_signature' and not submission.is_completed:
                # Employee filled, ready for client signature
                ready_for_signature.append({
                    'assignment': assignment,
                    'submission': submission,
                    'needs_signature': True
                })
            else:
                # Needs revision or under review
                pending_assignments.append({
                    'assignment': assignment,
                    'submission': submission,
                    'needs_revision': submission.review_status == 'needs_revision',
                    'review_notes': submission.review_notes if submission.review_status == 'needs_revision' else None
                })
        except TaxFormSubmission.DoesNotExist:
            # No submission yet - show in pending
            pending_assignments.append({
                'assignment': assignment,
                'submission': None,
                'needs_revision': False,
                'review_notes': None
            })
    
    context = {
        'client': client,
        'waiver': waiver,
        'pending_assignments': pending_assignments,
        'ready_for_signature': ready_for_signature,
        'completed_assignments': completed_assignments,
    }
    
    return render(request, 'tax/client/dashboard.html', context)


def tax_form_fill(request, assignment_id):
    """Client form filling interface"""
    # Check if client is logged in
    client_id = request.session.get('tax_client_id')
    if not client_id:
        messages.error(request, "Please log in to access your tax forms.")
        return redirect('tax_client_login')
    
    try:
        client = TaxClient.objects.get(id=client_id, is_active=True)
    except TaxClient.DoesNotExist:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('tax_client_login')
    
    # Check if client has completed waiver
    try:
        waiver = TaxClientWaiver.objects.get(client=client)
        if not waiver.is_completed:
            messages.error(request, "Please complete your waiver before accessing tax forms.")
            return redirect('tax_client_waiver')
    except TaxClientWaiver.DoesNotExist:
        messages.error(request, "Please complete your waiver before accessing tax forms.")
        return redirect('tax_client_waiver')
    
    # Get assignment
    assignment = get_object_or_404(
        TaxFormAssignment,
        id=assignment_id,
        client=client
    )
    
    # Check if already submitted (unless needs revision or multiple submissions allowed)
    existing_submission = TaxFormSubmission.objects.filter(assignment=assignment).first()
    
    can_submit = (
        not existing_submission or
        assignment.tax_form.allow_multiple_submissions or
        (existing_submission and existing_submission.review_status == 'needs_revision')
    )
    
    if existing_submission and not can_submit:
        messages.info(request, "You have already submitted this form and it's currently under review.")
        return redirect('tax_client_dashboard')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Collect form data
                form_data = {}
                uploaded_files = []
                
                # Get form fields
                form_fields = assignment.tax_form.fields.filter(is_active=True)
                
                # Process each field
                for field in form_fields:
                    field_name = field.field_name
                    
                    if field.field_type == 'file':
                        # Handle file upload
                        uploaded_file = request.FILES.get(field_name)
                        if uploaded_file:
                            # Save file
                            file_path = f"tax_documents/{assignment.client.id}/{assignment.id}/{uploaded_file.name}"
                            saved_path = default_storage.save(file_path, uploaded_file)
                            uploaded_files.append(saved_path)
                            form_data[field_name] = saved_path
                    
                    elif field.field_type == 'signature':
                        # Handle signature data
                        signature_data = request.POST.get(field_name)
                        if signature_data and signature_data.startswith('data:image/png;base64,'):
                            form_data[field_name] = signature_data
                    
                    else:
                        # Regular form fields
                        value = request.POST.get(field_name, '')
                        if value:
                            form_data[field_name] = value
                
                # Process signature if present
                signature_file_path = ''
                signature_data = ''
                if 'signature' in form_data and form_data['signature']:
                    sig_data = form_data['signature']
                    if sig_data.startswith('data:image/png;base64,'):
                        # Extract base64 data
                        base64_data = sig_data.split(',')[1]
                        binary_data = base64.b64decode(base64_data)
                        
                        # Save signature file
                        sig_filename = f"signature_{uuid.uuid4().hex}.png"
                        sig_path = f"tax_signatures/{assignment.client.id}/{sig_filename}"
                        signature_file_path = default_storage.save(sig_path, ContentFile(binary_data))
                        signature_data = sig_data
                
                # Create or update submission
                if existing_submission and existing_submission.review_status == 'needs_revision':
                    # Update existing submission
                    existing_submission.form_data = form_data
                    existing_submission.uploaded_files = uploaded_files
                    existing_submission.signature_data = signature_data
                    existing_submission.signature_file_path = signature_file_path
                    existing_submission.ip_address = request.META.get('REMOTE_ADDR')
                    existing_submission.user_agent = request.META.get('HTTP_USER_AGENT', '')
                    existing_submission.review_status = 'pending'
                    existing_submission.review_notes = ''
                    existing_submission.reviewed_by = None
                    existing_submission.reviewed_at = None
                    existing_submission.save()
                    
                    messages.success(request, "Your updated tax form has been resubmitted successfully!")
                else:
                    # Create new submission
                    submission = TaxFormSubmission.objects.create(
                        assignment=assignment,
                        form_data=form_data,
                        uploaded_files=uploaded_files,
                        signature_data=signature_data,
                        signature_file_path=signature_file_path,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, "Your tax form has been submitted successfully!")
                
                # Update assignment status
                assignment.status = 'completed'
                assignment.completed_at = timezone.now()
                assignment.last_activity = timezone.now()
                assignment.save()
                
                return redirect('tax_client_dashboard')
                
        except Exception as e:
            messages.error(request, f"Error submitting form: {str(e)}")
    
    # GET request - show form
    form_fields = assignment.tax_form.fields.filter(is_active=True).order_by('section', 'order')
    
    # Get existing submission data if this is a revision
    existing_data = {}
    revision_notes = None
    if existing_submission and existing_submission.review_status == 'needs_revision':
        existing_data = existing_submission.form_data or {}
        revision_notes = existing_submission.review_notes
    
    # Update activity
    assignment.last_activity = timezone.now()
    if assignment.status == 'assigned':
        assignment.status = 'in_progress'
        assignment.first_accessed = timezone.now()
    assignment.save()
    
    context = {
        'assignment': assignment,
        'form_fields': form_fields,
        'client': client,
        'existing_data': existing_data,
        'revision_notes': revision_notes,
        'is_revision': bool(existing_submission and existing_submission.review_status == 'needs_revision'),
        'sections': list(dict.fromkeys(f.section for f in form_fields if f.section)),
    }
    
    return render(request, 'tax/client/form.html', context)


def tax_client_review_form(request, submission_id):
    """Client reviews and signs form completed by employee"""
    # Check if client is logged in
    client_id = request.session.get('tax_client_id')
    if not client_id:
        messages.error(request, "Please log in to access your tax forms.")
        return redirect('tax_client_login')
    
    try:
        client = TaxClient.objects.get(id=client_id, is_active=True)
    except TaxClient.DoesNotExist:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('tax_client_login')
    
    # Check if client has completed waiver
    try:
        waiver = TaxClientWaiver.objects.get(client=client)
        if not waiver.is_completed:
            messages.error(request, "Please complete your waiver before accessing tax forms.")
            return redirect('tax_client_waiver')
    except TaxClientWaiver.DoesNotExist:
        messages.error(request, "Please complete your waiver before accessing tax forms.")
        return redirect('tax_client_waiver')
    
    # Get submission
    submission = get_object_or_404(
        TaxFormSubmission,
        id=submission_id,
        assignment__client=client,
        is_completed=False  # Only allow review of uncompleted forms
    )
    
    if request.method == 'POST':
        # Handle client signature and approval
        client_signature = request.POST.get('client_signature', '')
        client_agreement = request.POST.get('client_agreement') == 'yes'
        
        if not client_signature or not client_agreement:
            messages.error(request, "Please provide your signature and confirm the agreement.")
            return redirect('tax_client_review_form', submission_id=submission_id)
        
        # Update submission with client signature
        submission.client_signature_data = client_signature
        submission.client_signed_at = timezone.now()
        submission.is_completed = True
        submission.save()
        
        # Update assignment status
        submission.assignment.status = 'completed'
        submission.assignment.save()
        
        messages.success(request, f"Form '{submission.assignment.tax_form.name}' signed and submitted successfully!")
        return redirect('tax_client_dashboard')
    
    # Prepare form data for review
    form_fields = []
    for field in submission.assignment.tax_form.fields.filter(is_active=True).order_by('section', 'order'):
        field_data = {
            'id': field.id,
            'label': field.field_label,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'value': submission.form_data.get(field.field_name, '') if submission.form_data else ''
        }
        form_fields.append(field_data)
    
    context = {
        'client': client,
        'submission': submission,
        'assignment': submission.assignment,
        'form_fields': form_fields,
    }
    
    return render(request, 'tax/client/review_form.html', context)


@login_required
def send_client_reminder(request, client_id):
    """Send reminder email to client about pending tax forms"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        client = TaxClient.objects.get(id=client_id, is_active=True)
        
        # Send the welcome email again as a reminder
        send_client_welcome_email(client)
        
        return JsonResponse({'success': True, 'message': 'Reminder email sent successfully'})
        
    except TaxClient.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required  
def send_login_help(request, client_id):
    """Send login assistance email to client"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        client = TaxClient.objects.get(id=client_id, is_active=True)
        
        # Send the welcome email as login help
        send_client_welcome_email(client)
        
        return JsonResponse({'success': True, 'message': 'Login assistance email sent successfully'})
        
    except TaxClient.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def deactivate_client(request, client_id):
    """Deactivate a client account"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        client = TaxClient.objects.get(id=client_id)
        client.is_active = False
        client.save()
        
        return JsonResponse({'success': True, 'message': 'Client deactivated successfully'})
        
    except TaxClient.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
