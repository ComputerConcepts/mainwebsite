"""
Views for HR Onboarding System
Handles form creation, invitation management, and submission review
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import uuid
import io
import os
from datetime import timedelta, datetime, time
from django.core.files.storage import default_storage
from decimal import Decimal, InvalidOperation
from django.urls import reverse
from urllib.parse import urlencode

from .models import (
    OnboardingForm, OnboardingFormField, ProspectiveEmployee, 
    OnboardingInvitation, OnboardingSubmission, Employee, OnboardingOfferLetter, JobPosting
)
from .onboarding_emails import OnboardingEmailService
from .views_onboarding_portal import _generate_offer_letter_pdf


def _build_offer_letter_context(submission):
    """Assemble shared context for offer letter management."""
    offer_letter = getattr(submission, 'offer_letter', None)

    job_postings_qs = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    job_postings = list(job_postings_qs)
    if offer_letter and offer_letter.job_posting and offer_letter.job_posting not in job_postings:
        job_postings.append(offer_letter.job_posting)

    job_postings_data = []
    for job in job_postings:
        job_postings_data.append({
            'id': str(job.id),
            'title': job.title,
            'department': job.department,
            'location': job.location,
            'job_type': job.job_type,
            'job_type_display': job.get_job_type_display(),
            'salary_range': job.salary_range or '',
            'description': job.description or '',
            'requirements': job.requirements or '',
            'responsibilities': job.responsibilities or '',
            'benefits': job.benefits or '',
            'detail_url': reverse('career_apply', kwargs={'job_id': job.id}),
        })

    return {
        'offer_letter': offer_letter,
        'job_postings': job_postings,
        'job_postings_data': job_postings_data,
        'selected_job_posting_id': str(offer_letter.job_posting.id) if offer_letter and offer_letter.job_posting else '',
        'pay_frequency_choices': OnboardingOfferLetter.COMPENSATION_FREQUENCY_CHOICES,
        'preview_url': reverse('preview_offer_letter', kwargs={'submission_id': submission.id}) if offer_letter else '',
    }


def _handle_submission_post(request, submission, default_redirect_url):
    """Process submission-related POST actions and redirect appropriately."""
    redirect_url = request.POST.get('return_path') or default_redirect_url
    offer_letter = getattr(submission, 'offer_letter', None)
    action = request.POST.get('action', 'update_review')

    if action == 'update_review':
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

        if new_status == 'needs_revision':
            invitation = submission.invitation
            invitation.sent_by = request.user
            invitation.save(update_fields=['sent_by'])
            resend_success = OnboardingEmailService.send_onboarding_invitation(
                invitation,
                request,
                force_new_pin=True
            )
            if not resend_success:
                messages.warning(
                    request,
                    "Submission updated, but we could not resend the onboarding PIN email. "
                    "Please retry or contact support."
                )

        if old_status != new_status or new_status == 'needs_revision':
            OnboardingEmailService.send_status_update(
                submission, old_status, new_status, review_notes, request
            )

        messages.success(request, "Submission updated successfully!")
        return redirect(redirect_url)

    if action == 'save_offer_letter':
        if submission.review_status != 'approved':
            messages.error(request, "Offer letters can only be created once an application is approved.")
            return redirect(redirect_url)

        job_posting_id = request.POST.get('job_posting_id', '').strip()
        job_posting = JobPosting.objects.filter(id=job_posting_id).first() if job_posting_id else None

        position_title = request.POST.get('position_title', '').strip()
        employment_type = request.POST.get('employment_type', '').strip()
        salary_amount_input = request.POST.get('salary_amount', '').strip()
        salary_currency = request.POST.get('salary_currency', 'USD').strip() or 'USD'
        pay_frequency = request.POST.get('pay_frequency', 'annual')
        compensation_notes = request.POST.get('compensation_notes', '').strip()
        start_date_input = request.POST.get('start_date', '').strip()
        expires_input = request.POST.get('offer_expires_at', '').strip()
        additional_terms = request.POST.get('additional_terms', '').strip()

        if job_posting and not position_title:
            position_title = job_posting.title
        if job_posting and not employment_type:
            employment_type = job_posting.get_job_type_display()
        if job_posting and not compensation_notes and job_posting.salary_range:
            compensation_notes = f"Salary Range: {job_posting.salary_range}"

        if not position_title:
            messages.error(request, "Please provide a position title for the offer letter.")
            return redirect(redirect_url)

        salary_amount = None
        if salary_amount_input:
            try:
                salary_amount = Decimal(salary_amount_input.replace(',', ''))
            except (InvalidOperation, AttributeError):
                messages.error(request, "Salary amount must be a valid number.")
                return redirect(redirect_url)

        if pay_frequency not in dict(OnboardingOfferLetter.COMPENSATION_FREQUENCY_CHOICES):
            pay_frequency = 'annual'

        start_date = parse_date(start_date_input) if start_date_input else None
        offer_expires_at = parse_date(expires_input) if expires_input else None

        if offer_letter and offer_letter.status == 'signed':
            messages.error(request, "This offer letter is already fully signed and cannot be modified.")
            return redirect(redirect_url)

        if not offer_letter:
            offer_letter = OnboardingOfferLetter.objects.create(
                submission=submission,
                created_by=request.user,
                position_title=position_title,
                employment_type=employment_type,
                salary_amount=salary_amount,
                salary_currency=salary_currency.upper(),
                pay_frequency=pay_frequency,
                compensation_notes=compensation_notes,
                start_date=start_date,
                offer_expires_at=offer_expires_at,
                additional_terms=additional_terms,
                job_posting=job_posting,
            )
        else:
            if offer_letter.offer_pdf_path:
                try:
                    if default_storage.exists(offer_letter.offer_pdf_path):
                        default_storage.delete(offer_letter.offer_pdf_path)
                except Exception:
                    pass
                offer_letter.offer_pdf_path = ''
            offer_letter.position_title = position_title
            offer_letter.employment_type = employment_type
            offer_letter.salary_amount = salary_amount
            offer_letter.salary_currency = salary_currency.upper()
            offer_letter.pay_frequency = pay_frequency
            offer_letter.compensation_notes = compensation_notes
            offer_letter.start_date = start_date
            offer_letter.offer_expires_at = offer_expires_at
            offer_letter.additional_terms = additional_terms
            offer_letter.job_posting = job_posting
            offer_letter.status = 'draft'
            offer_letter.employer_signed_by = None
            offer_letter.employer_signature_name = ''
            offer_letter.employer_signature_data = ''
            offer_letter.employer_signed_at = None
            offer_letter.employee_signature_name = ''
            offer_letter.employee_signed_at = None
            offer_letter.employee_signature_data = ''
            offer_letter.decline_reason = ''
            offer_letter.save()

        messages.success(request, "Offer letter details saved. Please sign to send to the candidate.")
        return redirect(redirect_url)

    if action == 'employer_sign_offer':
        if not offer_letter:
            messages.error(request, "Create the offer letter details before signing.")
            return redirect(redirect_url)

        if offer_letter.status == 'signed':
            messages.info(request, "Offer letter already fully signed.")
            return redirect(redirect_url)

        signature_name = request.POST.get('employer_signature_name', '').strip()
        signature_data = request.POST.get('employer_signature_data', '').strip()
        if not signature_name:
            messages.error(request, "Please provide your name to sign the offer letter.")
            return redirect(redirect_url)
        if not signature_data or not signature_data.startswith('data:image/'):
            messages.error(request, "Please provide your signature to complete the offer letter.")
            return redirect(redirect_url)

        offer_letter.employer_signature_name = signature_name
        offer_letter.employer_signature_data = signature_data
        offer_letter.employer_signed_at = timezone.now()
        offer_letter.employer_signed_by = request.user
        offer_letter.status = 'pending_employee'
        offer_letter.employee_signature_name = ''
        offer_letter.employee_signed_at = None
        offer_letter.employee_signature_data = ''
        offer_letter.decline_reason = ''
        offer_letter.offer_pdf_path = ''
        offer_letter.save(update_fields=[
            'employer_signature_name',
            'employer_signature_data',
            'employer_signed_at',
            'employer_signed_by',
            'status',
            'employee_signature_name',
            'employee_signed_at',
            'employee_signature_data',
            'decline_reason',
            'offer_pdf_path',
            'updated_at'
        ])

        prospective_employee = submission.invitation.prospective_employee
        pin_expiry_at = None
        if offer_letter.start_date:
            start_dt = datetime.combine(offer_letter.start_date, time(23, 59, 59))
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
            if start_dt > timezone.now():
                pin_expiry_at = start_dt

        prospective_employee.generate_pin(expiry_at=pin_expiry_at)
        email_sent = OnboardingEmailService.send_offer_ready_email(offer_letter, request)

        if email_sent:
            messages.success(request, "Offer letter signed. The candidate has been notified and can now review and sign it.")
        else:
            messages.warning(request, "Offer letter signed, but we were unable to send the notification email. Please contact the candidate manually.")
        return redirect(redirect_url)

    messages.error(request, "Unknown action.")
    return redirect(redirect_url)


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

    applicant_reviews = ProspectiveEmployee.objects.filter(
        is_active=True,
        onboardinginvitation__isnull=False,
    ).annotate(
        total_invitations=Count('onboardinginvitation', distinct=True),
        completed_submissions=Count(
            'onboardinginvitation__onboardingsubmission',
            filter=Q(onboardinginvitation__onboardingsubmission__review_status='approved'),
            distinct=True,
        ),
        needs_revision_submissions=Count(
            'onboardinginvitation__onboardingsubmission',
            filter=Q(onboardinginvitation__onboardingsubmission__review_status='needs_revision'),
            distinct=True,
        ),
        pending_submissions=Count(
            'onboardinginvitation__onboardingsubmission',
            filter=Q(onboardinginvitation__onboardingsubmission__review_status__in=['pending', 'under_review']),
            distinct=True,
        ),
        last_activity=Max('onboardinginvitation__last_activity'),
    ).order_by('-last_activity', '-created_at')[:5]
    
    # Forms overview
    forms = OnboardingForm.objects.filter(is_active=True).annotate(
        invitation_count=Count('onboardinginvitation'),
        submission_count=Count('onboardinginvitation__onboardingsubmission')
    ).order_by('-created_at')
    
    context = {
        'stats': stats,
        'recent_submissions': recent_submissions,
        'recent_invitations': recent_invitations,
        'applicant_reviews': applicant_reviews,
        'forms': forms,
    }
    
    return render(request, 'hr/onboarding/dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_onboarding_employee(request):
    """Wizard flow to create/update a prospect and assign multiple forms"""
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin']:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('employee_dashboard')
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('employee_dashboard')

    forms = OnboardingForm.objects.filter(is_active=True).order_by('title')
    job_postings = JobPosting.objects.filter(is_active=True).order_by('-created_at')[:25]

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        job_posting_id = request.POST.get('job_posting', '').strip()
        custom_message = request.POST.get('custom_message', '').strip()
        send_email = request.POST.get('send_email') == 'on'
        selected_form_ids = request.POST.getlist('form_ids')

        form_state = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'job_posting': job_posting_id,
            'custom_message': custom_message,
            'send_email': send_email,
        }

        errors = []
        if not email:
            errors.append("Email is required.")
        if not selected_form_ids:
            errors.append("Select at least one onboarding form to assign.")

        valid_forms = {str(form.id): form for form in forms}
        invalid_forms = [form_id for form_id in selected_form_ids if form_id not in valid_forms]
        if invalid_forms:
            errors.append("One or more selected forms are unavailable. Please refresh and try again.")

        job_posting = None
        if job_posting_id:
            job_posting = JobPosting.objects.filter(id=job_posting_id).first()
            if not job_posting:
                errors.append("The selected job posting is no longer available.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(
                request,
                'hr/onboarding/create_employee_wizard.html',
                {
                    'forms': forms,
                    'job_postings': job_postings,
                    'form_state': form_state,
                    'selected_forms': selected_form_ids,
                },
            )

        try:
            with transaction.atomic():
                prospective_employee, created = ProspectiveEmployee.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'created_by': request.user,
                    },
                )

                if not created:
                    prospective_employee.first_name = first_name or prospective_employee.first_name
                    prospective_employee.last_name = last_name or prospective_employee.last_name
                    prospective_employee.phone = phone or prospective_employee.phone
                    prospective_employee.is_active = True
                    prospective_employee.save(update_fields=['first_name', 'last_name', 'phone', 'is_active'])

                created_count = 0
                updated_count = 0
                failed_emails = []

                for form_id in selected_form_ids:
                    onboarding_form = valid_forms.get(form_id)
                    if not onboarding_form:
                        continue

                    invitation, invitation_created = OnboardingInvitation.objects.get_or_create(
                        onboarding_form=onboarding_form,
                        prospective_employee=prospective_employee,
                        defaults={
                            'sent_by': request.user,
                            'custom_message': custom_message,
                        },
                    )

                    if invitation_created:
                        created_count += 1
                    else:
                        invitation.sent_by = request.user
                        invitation.custom_message = custom_message
                        update_fields = ['sent_by', 'custom_message']
                        if send_email:
                            invitation.status = 'sent'
                            update_fields.append('status')
                        invitation.save(update_fields=update_fields)
                        updated_count += 1

                    if send_email:
                        success = OnboardingEmailService.send_onboarding_invitation(invitation, request)
                        if not success:
                            failed_emails.append(onboarding_form.title)

                if created:
                    messages.success(
                        request,
                        f"Prospective employee {prospective_employee.email} created successfully.",
                    )
                else:
                    messages.success(
                        request,
                        f"Prospective employee {prospective_employee.email} updated successfully.",
                    )

                if created_count:
                    messages.info(request, f"{created_count} new form invitation(s) created.")
                if updated_count:
                    messages.info(request, f"{updated_count} existing invitation(s) refreshed.")
                if send_email:
                    if failed_emails:
                        messages.warning(
                            request,
                            "Invitations created, but we could not email: " + ", ".join(failed_emails),
                        )
                    else:
                        messages.success(request, "All invitation emails were sent.")

                if job_posting:
                    request.session['last_onboarding_job_posting'] = str(job_posting.id)

                return redirect('hr_onboarding_dashboard')
        except Exception as exc:
            messages.error(request, f"Could not create onboarding record: {exc}")

    return render(
        request,
        'hr/onboarding/create_employee_wizard.html',
        {
            'forms': forms,
            'job_postings': job_postings,
            'form_state': {'send_email': True},
            'selected_forms': [],
        },
    )


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

    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        if not submission_id:
            messages.error(request, "Submission reference missing.")
            return redirect('onboarding_submissions')
        submission = submissions.filter(id=submission_id).first()
        if not submission:
            submission = OnboardingSubmission.objects.filter(id=submission_id).first()
        if not submission:
            messages.error(request, "Submission not found.")
            return redirect('onboarding_submissions')

        default_redirect = request.POST.get('return_path') or reverse('onboarding_submissions')
        return _handle_submission_post(request, submission, default_redirect)

    filtered_submissions = submissions
    selected_submission = None
    selected_id = request.GET.get('submission')
    if selected_id:
        selected_submission = filtered_submissions.filter(id=selected_id).first()
    elif search_query and filtered_submissions.count() == 1:
        selected_submission = filtered_submissions.first()

    # Pagination
    paginator = Paginator(filtered_submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    status_choices = OnboardingSubmission.REVIEW_STATUS_CHOICES
    forms = OnboardingForm.objects.filter(is_active=True).order_by('title')
    
    offer_letter_context = _build_offer_letter_context(selected_submission) if selected_submission else {}

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'form_filter': form_filter,
        'search_query': search_query,
        'status_choices': status_choices,
        'forms': forms,
        'selected_submission': selected_submission,
        'selected_offer_letter': offer_letter_context.get('offer_letter'),
        'offer_letter_job_postings': offer_letter_context.get('job_postings', []),
        'offer_letter_job_postings_data': offer_letter_context.get('job_postings_data', []),
        'offer_letter_selected_job_posting_id': offer_letter_context.get('selected_job_posting_id', ''),
        'offer_letter_pay_frequency_choices': offer_letter_context.get('pay_frequency_choices', OnboardingOfferLetter.COMPENSATION_FREQUENCY_CHOICES),
        'offer_letter_job_postings_script_id': f"job-postings-data-{selected_submission.id}" if selected_submission else '',
        'offer_letter_preview_url': offer_letter_context.get('preview_url', ''),
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
        default_redirect = reverse('hr_submission_detail', kwargs={'submission_id': submission_id})
        return _handle_submission_post(request, submission, default_redirect)

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

    offer_letter_context = _build_offer_letter_context(submission)
    offer_letter = offer_letter_context.get('offer_letter')
    management_query = urlencode({
        'search': submission.invitation.prospective_employee.email,
        'submission': submission.id,
    })
    management_url = f"{reverse('onboarding_submissions')}?{management_query}"

    context = {
        'submission': submission,
        'form_display_data': form_display_data,
        'status_choices': OnboardingSubmission.REVIEW_STATUS_CHOICES,
        'priority_choices': [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        'show_offer_letter_actions': False,
        'offer_letter_management_url': management_url,
        'job_postings_script_id': f"job-postings-data-{submission.id}",
        'offer_letter_preview_url': offer_letter_context.get('preview_url', ''),
    }
    context.update(offer_letter_context)
    
    return render(request, 'hr/onboarding/submission_detail.html', context)


@login_required
def download_submission_file(request, submission_id, field_name):
    """Download an individual uploaded file from a submission"""
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

    # Locate file metadata
    file_info = None
    value = submission.form_data.get(field_name)

    if isinstance(value, dict) and 'file_path' in value:
        file_info = {
            'file_path': value.get('file_path'),
            'original_name': value.get('original_name'),
        }

    if not file_info:
        for uploaded in submission.uploaded_files:
            if uploaded.get('field_name') == field_name:
                file_info = {
                    'file_path': uploaded.get('file_path'),
                    'original_name': uploaded.get('original_name'),
                }
                break

    if not file_info or not file_info.get('file_path'):
        messages.error(request, "Requested file could not be found for this submission.")
        return redirect('hr_submission_detail', submission_id=submission_id)

    file_path = file_info['file_path']

    if not default_storage.exists(file_path):
        messages.error(request, "The file is no longer available in storage.")
        return redirect('hr_submission_detail', submission_id=submission_id)

    stored_file = default_storage.open(file_path, 'rb')
    filename = file_info.get('original_name') or os.path.basename(file_path)

    response = FileResponse(stored_file, as_attachment=True, filename=filename)
    return response


@login_required
def download_offer_letter_pdf(request, offer_id):
    """Allow HR to download the signed offer letter PDF"""
    offer_letter = get_object_or_404(OnboardingOfferLetter, id=offer_id)
    submission = offer_letter.submission

    # Check HR permissions
    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin'] and not request.user.is_superuser:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('hr_submission_detail', submission_id=submission.id)
    except Employee.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, "Employee profile not found.")
            return redirect('hr_submission_detail', submission_id=submission.id)

    if not offer_letter.offer_pdf_path:
        messages.error(request, "A signed PDF is not yet available for this offer letter.")
        return redirect('hr_submission_detail', submission_id=submission.id)

    try:
        if not default_storage.exists(offer_letter.offer_pdf_path):
            messages.error(request, "The signed offer letter file could not be found.")
            return redirect('hr_submission_detail', submission_id=submission.id)
        pdf_file = default_storage.open(offer_letter.offer_pdf_path, 'rb')
    except Exception as exc:
        messages.error(request, f"Unable to open the offer letter PDF: {str(exc)}")
        return redirect('hr_submission_detail', submission_id=submission.id)

    filename = f"Offer_Letter_{offer_letter.position_title.replace(' ', '_')}.pdf"
    response = FileResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def download_combined_pdf(request, submission_id):
    """Download a combined PDF with all submission files"""
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
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
@login_required
def preview_offer_letter(request, submission_id):
    """Generate a PDF preview of the offer letter regardless of signature state."""
    submission = get_object_or_404(OnboardingSubmission, id=submission_id)

    try:
        employee = Employee.objects.get(user=request.user)
        if employee.department != 'HR' and employee.role not in ['admin', 'super_admin'] and not request.user.is_superuser:
            messages.error(request, "Access denied. HR permissions required.")
            return redirect('hr_submission_detail', submission_id=submission_id)
    except Employee.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, "Employee profile not found.")
            return redirect('hr_submission_detail', submission_id=submission_id)

    offer_letter = getattr(submission, 'offer_letter', None)
    if not offer_letter:
        messages.error(request, "No offer letter has been created for this submission.")
        return redirect('hr_submission_detail', submission_id=submission_id)

    pdf_bytes, saved_path = _generate_offer_letter_pdf(offer_letter)
    if not pdf_bytes:
        messages.error(request, "Unable to generate offer letter preview. Ensure PDF support is installed.")
        return redirect('hr_submission_detail', submission_id=submission_id)

    if saved_path and default_storage.exists(saved_path):
        try:
            default_storage.delete(saved_path)
        except Exception:
            pass

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=\"Offer_Letter_{offer_letter.id}_Preview.pdf\"'
    return response
