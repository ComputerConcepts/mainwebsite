"""
Email service for HR onboarding system
Handles sending onboarding invitations and related communications
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class OnboardingEmailService:
    """Service class for handling onboarding-related emails"""
    
    @staticmethod
    def send_onboarding_invitation(invitation, request=None):
        """
        Send onboarding invitation email with PIN to prospective employee
        
        Args:
            invitation: OnboardingInvitation instance
            request: HttpRequest object for building absolute URLs
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            prospective_employee = invitation.prospective_employee
            onboarding_form = invitation.onboarding_form
            
            # Generate PIN if not exists or expired
            if not prospective_employee.is_pin_valid():
                pin = prospective_employee.generate_pin()
            else:
                pin = prospective_employee.current_pin
            
            # Build onboarding URL
            if request:
                onboarding_url = request.build_absolute_uri(
                    reverse('onboarding_login')
                )
            else:
                # Fallback URL
                onboarding_url = f"https://onecomputerconcepts.com{reverse('onboarding_login')}"
            
            # Email context
            context = {
                'invitation': invitation,
                'prospective_employee': prospective_employee,
                'onboarding_form': onboarding_form,
                'pin': pin,
                'pin_expiry': prospective_employee.pin_expiry,
                'onboarding_url': onboarding_url,
                'custom_message': invitation.custom_message,
                'current_year': timezone.now().year,
            }
            
            # Render email templates
            subject = f"Complete Your Onboarding - {onboarding_form.title}"
            text_content = render_to_string('email/onboarding/invitation.txt', context)
            html_content = render_to_string('email/onboarding/invitation.html', context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[prospective_employee.email],
                reply_to=['hr@onecomputerconcepts.com']
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            # Update invitation status
            invitation.status = 'sent'
            invitation.save()
            
            logger.info(f"Onboarding invitation sent to {prospective_employee.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send onboarding invitation to {prospective_employee.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_submission_confirmation(submission, request=None):
        """
        Send confirmation email when onboarding form is submitted
        
        Args:
            submission: OnboardingSubmission instance
            request: HttpRequest object for building absolute URLs
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            invitation = submission.invitation
            prospective_employee = invitation.prospective_employee
            
            # Build status URL
            if request:
                status_url = request.build_absolute_uri(
                    reverse('onboarding_status', kwargs={'submission_id': submission.id})
                )
            else:
                status_url = f"https://onecomputerconcepts.com{reverse('onboarding_status', kwargs={'submission_id': submission.id})}"
            
            context = {
                'submission': submission,
                'invitation': invitation,
                'prospective_employee': prospective_employee,
                'status_url': status_url,
                'current_year': timezone.now().year,
            }
            
            subject = f"Application Received - {invitation.onboarding_form.title}"
            text_content = render_to_string('email/onboarding/confirmation.txt', context)
            html_content = render_to_string('email/onboarding/confirmation.html', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[prospective_employee.email],
                reply_to=['hr@onecomputerconcepts.com']
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Submission confirmation sent to {prospective_employee.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send submission confirmation: {str(e)}")
            return False
    
    @staticmethod
    def send_hr_notification(submission, request=None):
        """
        Send notification to HR when new onboarding form is submitted
        
        Args:
            submission: OnboardingSubmission instance
            request: HttpRequest object for building absolute URLs
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            invitation = submission.invitation
            
            # Build admin URL
            if request:
                admin_url = request.build_absolute_uri(
                    reverse('hr_submission_detail', kwargs={'submission_id': submission.id})
                )
            else:
                admin_url = f"https://onecomputerconcepts.com{reverse('hr_submission_detail', kwargs={'submission_id': submission.id})}"
            
            context = {
                'submission': submission,
                'invitation': invitation,
                'admin_url': admin_url,
                'current_year': timezone.now().year,
            }
            
            subject = f"New Onboarding Submission - {submission.get_applicant_name()}"
            text_content = render_to_string('email/onboarding/hr_notification.txt', context)
            html_content = render_to_string('email/onboarding/hr_notification.html', context)
            
            # Send to HR team and the person who sent the invitation
            recipients = ['hr@onecomputerconcepts.com']
            if invitation.sent_by.email:
                recipients.append(invitation.sent_by.email)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"HR notification sent for submission {submission.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send HR notification: {str(e)}")
            return False
    
    @staticmethod
    def send_status_update(submission, old_status, new_status, notes="", request=None):
        """
        Send status update email to prospective employee
        
        Args:
            submission: OnboardingSubmission instance
            old_status: Previous status
            new_status: New status
            notes: Optional notes from HR
            request: HttpRequest object for building absolute URLs
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            invitation = submission.invitation
            prospective_employee = invitation.prospective_employee
            
            context = {
                'submission': submission,
                'invitation': invitation,
                'prospective_employee': prospective_employee,
                'old_status': old_status,
                'new_status': new_status,
                'notes': notes,
                'current_year': timezone.now().year,
            }
            
            subject = f"Application Status Update - {invitation.onboarding_form.title}"
            text_content = render_to_string('email/onboarding/status_update.txt', context)
            html_content = render_to_string('email/onboarding/status_update.html', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[prospective_employee.email],
                reply_to=['hr@onecomputerconcepts.com']
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Status update sent to {prospective_employee.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update: {str(e)}")
            return False


class OnboardingEmailTemplates:
    """Helper class for email template management"""
    
    TEMPLATE_CHOICES = [
        ('invitation', 'Onboarding Invitation'),
        ('confirmation', 'Submission Confirmation'),
        ('hr_notification', 'HR Notification'),
        ('status_update', 'Status Update'),
        ('reminder', 'Reminder Email'),
    ]
    
    @staticmethod
    def get_template_preview(template_name, sample_data=None):
        """
        Generate preview of email template with sample data
        
        Args:
            template_name: Name of the template
            sample_data: Optional sample data for preview
            
        Returns:
            dict: Contains 'subject', 'text_content', 'html_content'
        """
        if not sample_data:
            sample_data = OnboardingEmailTemplates._get_sample_data()
        
        try:
            subject = f"Preview: {template_name.title()} Email"
            text_content = render_to_string(f'email/onboarding/{template_name}.txt', sample_data)
            html_content = render_to_string(f'email/onboarding/{template_name}.html', sample_data)
            
            return {
                'subject': subject,
                'text_content': text_content,
                'html_content': html_content
            }
        except Exception as e:
            logger.error(f"Failed to generate template preview: {str(e)}")
            return None
    
    @staticmethod
    def _get_sample_data():
        """Generate sample data for template previews"""
        from datetime import datetime, timedelta
        
        return {
            'invitation': {
                'id': 'sample-id',
                'sent_by': type('User', (), {'get_full_name': lambda: 'Jane Smith'})(),
                'custom_message': 'We are excited to have you join our development team!',
                'onboarding_form': {
                    'title': 'Software Developer Onboarding'
                }
            },
            'prospective_employee': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com'
            },
            'pin': '123456',
            'pin_expiry': datetime.now() + timedelta(hours=48),
            'onboarding_url': 'https://onecomputerconcepts.com/onboarding/login/',
            'current_year': datetime.now().year,
        }