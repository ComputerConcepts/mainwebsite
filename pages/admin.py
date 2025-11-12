from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    ContactForm, Events, Invoice, Ticket, Employee, Career, JobPosting,
    FileFolder, FileDocument, FileVersion, FileShare, FileActivity,
    BoardShare, BoardActivity,
    TaxFormTemplate, TaxFormSection, TaxFormField, TaxClient, TaxClientWaiver,
    TaxFormAssignment, TaxFormSubmission, TaxDocument
)
from .models import (
    OnboardingAssessment, OnboardingAssessmentQuestion,
    OnboardingAssessmentAttempt, OnboardingAssessmentResponse
)

@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'message']
    search_fields = ['name', 'email']
    readonly_fields = ['name', 'email', 'message']

@admin.register(Events)
class EventsAdmin(admin.ModelAdmin):
    list_display = ['title', 'eventdate', 'cost', 'status']
    list_filter = ['status', 'eventdate']
    search_fields = ['title', 'description']
    date_hierarchy = 'eventdate'

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'cost', 'verified', 'date']
    list_filter = ['verified', 'date']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['id', 'date']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'event', 'email', 'purchaseDate']
    list_filter = ['purchaseDate', 'event']
    search_fields = ['email', 'event__title']
    readonly_fields = ['id', 'purchaseDate']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'get_email', 'department', 'position', 'role', 'is_active', 'get_verification_status', 'get_storage_info', 'hire_date', 'last_login_date']
    list_filter = ['department', 'position', 'role', 'is_active', 'is_email_verified', 'hire_date', 'created_at']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email', 'department', 'position', 'phone']
    readonly_fields = ['id', 'hire_date', 'created_at', 'updated_at', 'last_login_date', 'verification_actions', 'storage_actions']
    date_hierarchy = 'hire_date'
    list_per_page = 50
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'employee_id', 'phone', 'address', 'emergency_contact', 'emergency_phone')
        }),
        ('Work Information', {
            'fields': ('department', 'position', 'role', 'manager', 'salary', 'hire_date')
        }),
        ('Storage Management', {
            'fields': ('storage_quota', 'storage_used', 'storage_actions'),
            'description': 'Manage user storage quotas and usage. Storage is automatically calculated.'
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_email_verified', 'email_verification_token', 'verification_actions'),
            'description': 'Email verification token will be automatically cleared when email is verified.'
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_login_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_verification_status(self, obj):
        """Display email verification status with visual indicators"""
        if obj.is_email_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span>'
            )
        else:
            has_token = 'Has Token' if obj.email_verification_token else 'No Token'
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Unverified</span><br>'
                '<small style="color: gray;">{}</small>',
                has_token
            )
    get_verification_status.short_description = 'Email Status'
    get_verification_status.admin_order_field = 'is_email_verified'
    
    def verification_actions(self, obj):
        """Display verification action buttons"""
        from django.urls import reverse
        from django.utils.safestring import mark_safe
        
        if not obj.pk:  # New object, no actions available
            return "-"
        
        buttons = []
        
        if not obj.is_email_verified:
            # Verify button
            verify_url = reverse('admin:verify_employee_email', args=[obj.pk])
            buttons.append(
                f'<a href="{verify_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✓ Verify Email</a>'
            )
            
            # Send verification email button
            send_url = reverse('admin:send_verification_email', args=[obj.pk])
            buttons.append(
                f'<a href="{send_url}" class="button" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">📧 Send Verification</a>'
            )
        else:
            # Unverify button (for testing/admin purposes)
            unverify_url = reverse('admin:unverify_employee_email', args=[obj.pk])
            buttons.append(
                f'<a href="{unverify_url}" class="button" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'Are you sure you want to unverify this email?\')">✗ Unverify Email</a>'
            )
        
        return mark_safe('<br>'.join(buttons)) if buttons else "-"
    
    verification_actions.short_description = 'Quick Actions'
    
    def get_storage_info(self, obj):
        """Display storage usage information"""
        if obj.storage_quota and obj.storage_used is not None:
            percentage = obj.get_storage_percentage()
            used_display = obj.get_storage_used_display()
            quota_display = obj.get_storage_quota_display()
            
            # Color based on usage
            if percentage < 70:
                color = 'green'
            elif percentage < 90:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span><br>'
                '<small>{} / {}</small>',
                color, percentage, used_display, quota_display
            )
        else:
            return format_html(
                '<span style="color: gray;">Not set</span>'
            )
    get_storage_info.short_description = 'Storage Usage'
    
    def storage_actions(self, obj):
        """Display storage management action buttons"""
        from django.urls import reverse
        from django.utils.safestring import mark_safe
        
        if not obj.pk:  # New object, no actions available
            return "-"
        
        buttons = []
        
        # Update quota button
        update_quota_url = reverse('admin:update_user_quota', args=[obj.pk])
        buttons.append(
            f'<a href="{update_quota_url}" class="button" style="background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">📊 Update Quota</a>'
        )
        
        # Recalculate usage button
        recalc_usage_url = reverse('admin:recalculate_storage', args=[obj.pk])
        buttons.append(
            f'<a href="{recalc_usage_url}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">🔄 Recalc Usage</a>'
        )
        
        # View files button
        view_files_url = reverse('admin:view_user_files', args=[obj.pk])
        buttons.append(
            f'<a href="{view_files_url}" class="button" style="background: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📁 View Files</a>'
        )
        
        return mark_safe('<br>'.join(buttons)) if buttons else "-"
    
    storage_actions.short_description = 'Storage Actions'
    
    def get_role_display(self, obj):
        colors = {
            'super_admin': 'red',
            'admin': 'orange',
            'manager': 'blue',
            'employee': 'green'
        }
        color = colors.get(obj.role, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    get_role_display.short_description = 'Role'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'manager')
    
    def get_actions(self, request):
        """Customize available actions based on user permissions"""
        actions = super().get_actions(request)
        
        # Only superusers can see certain sensitive actions
        if not request.user.is_superuser:
            sensitive_actions = ['verify_emails', 'unverify_emails', 'send_verification_emails', 
                               'make_admin', 'make_manager', 'reset_passwords']
            for action in sensitive_actions:
                if action in actions:
                    del actions[action]
        
        return actions

    actions = ['activate_employees', 'deactivate_employees', 'verify_emails', 'unverify_emails', 'send_verification_emails', 'make_admin', 'make_manager', 'make_employee', 'reset_passwords']
    
    def activate_employees(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} employees activated successfully.')
    activate_employees.short_description = 'Activate selected employees'
    
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} employees deactivated successfully.')
    deactivate_employees.short_description = 'Deactivate selected employees'
    
    def verify_emails(self, request, queryset):
        """Manually verify email addresses for selected employees"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can verify emails.', level='error')
            return
        
        updated = queryset.update(is_email_verified=True, email_verification_token=None)
        self.message_user(request, f'{updated} employee emails verified successfully.')
    verify_emails.short_description = 'Verify emails for selected employees (Superuser only)'
    
    def unverify_emails(self, request, queryset):
        """Unverify email addresses for selected employees"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can unverify emails.', level='error')
            return
        
        import secrets
        count = 0
        for employee in queryset:
            employee.is_email_verified = False
            employee.email_verification_token = secrets.token_urlsafe(32)
            employee.save()
            count += 1
        
        self.message_user(request, f'{count} employee emails unverified successfully. New verification tokens generated.')
    unverify_emails.short_description = 'Unverify emails for selected employees (Superuser only)'
    
    def send_verification_emails(self, request, queryset):
        """Send verification emails to selected unverified employees"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can send verification emails.', level='error')
            return
        
        import secrets
        from django.contrib.sites.shortcuts import get_current_site
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        count = 0
        for employee in queryset:
            if not employee.is_email_verified:
                # Generate new token if needed
                if not employee.email_verification_token:
                    employee.email_verification_token = secrets.token_urlsafe(32)
                    employee.save()
                
                # Send verification email
                current_site = get_current_site(request)
                subject = 'Verify Your Computer Concepts Employee Account'
                message = render_to_string('employee/email_verification.html', {
                    'employee': employee,
                    'domain': current_site.domain,
                    'protocol': 'https' if request.is_secure() else 'http',
                    'token': employee.email_verification_token,
                })
                
                try:
                    send_mail(
                        subject,
                        '',
                        settings.DEFAULT_FROM_EMAIL,
                        [employee.user.email],
                        html_message=message,
                        fail_silently=False,
                    )
                    count += 1
                except Exception as e:
                    self.message_user(request, f'Failed to send email to {employee.user.email}: {str(e)}', level='error')
        
        self.message_user(request, f'Verification emails sent to {count} employees.')
    send_verification_emails.short_description = 'Send verification emails to unverified employees (Superuser only)'
    
    def make_admin(self, request, queryset):
        """Promote selected employees to admin role"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can promote users to admin.', level='error')
            return
        
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} employees promoted to admin.')
    make_admin.short_description = 'Make selected employees admins (Superuser only)'
    
    def make_manager(self, request, queryset):
        """Promote selected employees to manager role"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can promote users to manager.', level='error')
            return
        
        updated = queryset.update(role='manager')
        self.message_user(request, f'{updated} employees promoted to manager.')
    make_manager.short_description = 'Make selected employees managers (Superuser only)'
    
    def make_employee(self, request, queryset):
        updated = queryset.update(role='employee')
        self.message_user(request, f'{updated} users set to employee role.')
    make_employee.short_description = 'Set selected users to employee role'
    
    def reset_passwords(self, request, queryset):
        """Reset passwords for selected employees"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can reset passwords.', level='error')
            return
        
        count = 0
        for employee in queryset:
            # Generate a temporary password
            temp_password = f"temp_{employee.employee_id}_2024"
            employee.user.set_password(temp_password)
            employee.user.save()
            count += 1
        self.message_user(request, f'Passwords reset for {count} employees. Temporary password format: temp_[employee_id]_2024')
    reset_passwords.short_description = 'Reset passwords for selected employees (Superuser only)'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    
    def changelist_view(self, request, extra_context=None):
        """Add custom context to the changelist view"""
        extra_context = extra_context or {}
        extra_context['verification_help'] = (
            "Use the actions below to manage employee email verification. "
            "Superusers can verify emails manually, send verification emails, "
            "or reset verification status."
        )
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_urls(self):
        """Add custom URLs for verification actions"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<uuid:employee_id>/verify-email/',
                self.admin_site.admin_view(self.verify_employee_email_view),
                name='verify_employee_email',
            ),
            path(
                '<uuid:employee_id>/unverify-email/',
                self.admin_site.admin_view(self.unverify_employee_email_view),
                name='unverify_employee_email',
            ),
            path(
                '<uuid:employee_id>/send-verification/',
                self.admin_site.admin_view(self.send_verification_email_view),
                name='send_verification_email',
            ),
        ]
        return custom_urls + urls
    
    def verify_employee_email_view(self, request, employee_id):
        """Custom view to verify employee email"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        
        if not request.user.is_superuser:
            messages.error(request, 'Only superusers can verify emails.')
            return redirect('admin:pages_employee_changelist')
        
        employee = get_object_or_404(Employee, id=employee_id)
        employee.is_email_verified = True
        employee.email_verification_token = None
        employee.save()
        
        messages.success(request, f'Email verified for {employee.user.email}')
        return redirect('admin:pages_employee_change', employee_id)

    def unverify_employee_email_view(self, request, employee_id):
        """Custom view to unverify employee email"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        import secrets

        if not request.user.is_superuser:
            messages.error(request, 'Only superusers can unverify emails.')
            return redirect('admin:pages_employee_changelist')

        employee = get_object_or_404(Employee, id=employee_id)
        employee.is_email_verified = False
        employee.email_verification_token = secrets.token_urlsafe(32)
        employee.save()

        messages.success(request, f'Email unverified for {employee.user.email}. New verification token generated.')
        return redirect('admin:pages_employee_change', employee_id)

    def send_verification_email_view(self, request, employee_id):
        """Custom view to send verification email"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from django.contrib.sites.shortcuts import get_current_site
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        import secrets

        if not request.user.is_superuser:
            messages.error(request, 'Only superusers can send verification emails.')
            return redirect('admin:pages_employee_changelist')

        employee = get_object_or_404(Employee, id=employee_id)

        if employee.is_email_verified:
            messages.warning(request, f'{employee.user.email} is already verified.')
            return redirect('admin:pages_employee_change', employee_id)

        # Generate new token
        employee.email_verification_token = secrets.token_urlsafe(32)
        employee.save()

        # Send verification email
        current_site = get_current_site(request)
        subject = 'Verify Your Computer Concepts Employee Account'
        message = render_to_string('employee/email_verification.html', {
            'employee': employee,
            'domain': current_site.domain,
            'protocol': 'https' if request.is_secure() else 'http',
            'token': employee.email_verification_token,
        })

        try:
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [employee.user.email],
                html_message=message,
                fail_silently=False,
            )
            messages.success(request, f'Verification email sent to {employee.user.email}')
        except Exception as e:
            messages.error(request, f'Failed to send email to {employee.user.email}: {str(e)}')

        return redirect('admin:pages_employee_change', employee_id)


# Simple admin registrations for onboarding assessments
@admin.register(OnboardingAssessment)
class OnboardingAssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'is_active', 'is_timed', 'time_limit_minutes', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['is_active', 'is_timed', 'created_at']


@admin.register(OnboardingAssessmentQuestion)
class OnboardingAssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'question_text', 'question_type', 'points', 'order', 'is_active']
    search_fields = ['question_text']
    list_filter = ['question_type', 'is_active']


@admin.register(OnboardingAssessmentAttempt)
class OnboardingAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'invitation', 'started_at', 'completed_at', 'score', 'percentage', 'is_submitted']
    search_fields = ['assessment__title', 'invitation__prospective_employee__email']
    list_filter = ['is_submitted', 'started_at']


@admin.register(OnboardingAssessmentResponse)
class OnboardingAssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'answer', 'points_awarded']
    search_fields = ['question__question_text']
    


# Custom User Admin with Employee Integration
class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'Employee Information'
    fields = ['employee_id', 'department', 'position', 'role', 'manager', 'phone', 'is_active', 'is_email_verified']


class CustomUserAdmin(UserAdmin):
    inlines = (EmployeeInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_employee_info', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'employee__department', 'employee__role']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee__employee_id']
    
    def get_employee_info(self, obj):
        try:
            employee = obj.employee
            return f"{employee.department} - {employee.get_role_display()}"
        except Employee.DoesNotExist:
            return "No Employee Record"
    get_employee_info.short_description = 'Employee Info'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee')


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Dashboard Overview Admin
class DashboardAdmin(admin.ModelAdmin):
    """Custom admin view for dashboard overview"""
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Employee statistics
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        inactive_employees = total_employees - active_employees
        
        # Department breakdown
        dept_stats = Employee.objects.values('department').annotate(count=Count('id')).order_by('-count')
        
        # Role breakdown
        role_stats = Employee.objects.values('role').annotate(count=Count('id')).order_by('-count')
        
        # Recent hires (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_hires = Employee.objects.filter(hire_date__gte=thirty_days_ago).count()
        
        extra_context.update({
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            'dept_stats': dept_stats,
            'role_stats': role_stats,
            'recent_hires': recent_hires,
        })
        
        return super().changelist_view(request, extra_context=extra_context)


# Admin site customization
admin.site.site_header = "Computer Concepts Admin"
admin.site.site_title = "Computer Concepts Admin Portal"
admin.site.index_title = "Welcome to Computer Concepts Administration"

@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'position_applied', 'email', 'phone', 'experience_years', 'submitted_at']
    list_filter = ['position_applied', 'experience_years', 'submitted_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'position_applied']
    readonly_fields = ['id', 'submitted_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Professional Information', {
            'fields': ('position_applied', 'experience_years', 'education', 'skills', 'available_start_date', 'salary_expectation')
        }),
        ('Application Details', {
            'fields': ('cover_letter', 'resume', 'linkedin_profile', 'portfolio_website')
        }),
        ('System Information', {
            'fields': ('id', 'submitted_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-submitted_at')
    
    actions = ['mark_as_reviewed', 'export_applications']
    
    def mark_as_reviewed(self, request, queryset):
        # You can add a status field later if needed
        self.message_user(request, f'{queryset.count()} applications marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark selected applications as reviewed'
    
    def export_applications(self, request, queryset):
        # You can implement CSV export functionality here
        self.message_user(request, f'Export feature coming soon for {queryset.count()} applications.')
    export_applications.short_description = 'Export selected applications'

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'job_type', 'experience_level', 'is_active', 'posted_by', 'created_at']
    list_filter = ['department', 'job_type', 'experience_level', 'is_active', 'created_at']
    search_fields = ['title', 'department', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'department', 'location', 'job_type', 'experience_level')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'responsibilities', 'benefits', 'salary_range')
        }),
        ('Posting Settings', {
            'fields': ('is_active', 'posted_by', 'application_deadline')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('posted_by').order_by('-created_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set posted_by on creation
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_postings', 'deactivate_postings']
    
    def activate_postings(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} job postings activated successfully.')
    activate_postings.short_description = 'Activate selected job postings'
    
    def deactivate_postings(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} job postings deactivated successfully.')
    deactivate_postings.short_description = 'Deactivate selected job postings'


# File Management Admin
@admin.register(FileFolder)
class FileFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'parent', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'created_by']
    search_fields = ['name', 'created_by__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by__user', 'parent')


@admin.register(FileDocument)
class FileDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'uploaded_by', 'folder', 'file_size_display', 'is_public', 'created_at']
    list_filter = ['file_type', 'is_public', 'created_at', 'uploaded_by']
    search_fields = ['name', 'description', 'tags', 'uploaded_by__user__username']
    readonly_fields = ['created_at', 'updated_at', 'last_accessed', 'download_count', 'file_size']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by__user', 'folder')


@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version_number', 'uploaded_by', 'created_at']
    list_filter = ['created_at', 'uploaded_by']
    search_fields = ['document__name', 'upload_comment', 'uploaded_by__user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'uploaded_by__user')


@admin.register(FileShare)
class FileShareAdmin(admin.ModelAdmin):
    list_display = ['document', 'shared_with', 'shared_by', 'permission', 'created_at']
    list_filter = ['permission', 'created_at']
    search_fields = ['document__name', 'shared_with__user__username', 'shared_by__user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'shared_with__user', 'shared_by__user')


@admin.register(FileActivity)
class FileActivityAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['document__name', 'user__user__username', 'details']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'user__user')


# Board Management Admin
@admin.register(BoardShare)
class BoardShareAdmin(admin.ModelAdmin):
    list_display = ['board', 'shared_with', 'shared_by', 'permission', 'created_at']
    list_filter = ['permission', 'created_at']
    search_fields = ['board__title', 'shared_with__user__username', 'shared_by__user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('board', 'shared_with__user', 'shared_by__user')


@admin.register(BoardActivity)
class BoardActivityAdmin(admin.ModelAdmin):
    list_display = ['board', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['board__title', 'user__user__username', 'details']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('board', 'user__user')


# Tax Preparation Admin
@admin.register(TaxFormTemplate)
class TaxFormTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'form_type', 'is_active', 'requires_signature', 'created_by', 'created_at']
    list_filter = ['form_type', 'is_active', 'requires_signature', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(TaxFormSection)
class TaxFormSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'tax_form', 'order', 'is_active', 'is_collapsible']
    list_filter = ['is_active', 'is_collapsible', 'tax_form']
    search_fields = ['title', 'description', 'tax_form__name']
    readonly_fields = ['id']
    ordering = ['tax_form', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tax_form')


@admin.register(TaxFormField)
class TaxFormFieldAdmin(admin.ModelAdmin):
    list_display = ['field_label', 'field_name', 'tax_form', 'section', 'field_type', 'is_required', 'is_active', 'order']
    list_filter = ['field_type', 'is_required', 'is_active', 'tax_form']
    search_fields = ['field_name', 'field_label', 'tax_form__name', 'section__title']
    readonly_fields = ['id']
    ordering = ['tax_form', 'section', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tax_form', 'section')


@admin.register(TaxClient)
class TaxClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'filing_status', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'filing_status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'ssn']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(TaxClientWaiver)
class TaxClientWaiverAdmin(admin.ModelAdmin):
    list_display = ['client', 'client_signed', 'client_signed_at', 'employee_witnessed', 'witnessed_by', 'witnessed_at']
    list_filter = ['client_signed', 'employee_witnessed', 'client_signed_at']
    search_fields = ['client__first_name', 'client__last_name', 'client__email']
    readonly_fields = ['client_signed_at', 'witnessed_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'witnessed_by')


@admin.register(TaxFormAssignment)
class TaxFormAssignmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'tax_form', 'status', 'assigned_by', 'assigned_at', 'due_date', 'completed_at']
    list_filter = ['status', 'assigned_at', 'due_date']
    search_fields = ['client__first_name', 'client__last_name', 'client__email', 'tax_form__name']
    readonly_fields = ['id', 'assigned_at', 'first_accessed', 'last_activity', 'completed_at']
    date_hierarchy = 'assigned_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'tax_form', 'assigned_by')


@admin.register(TaxFormSubmission)
class TaxFormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['get_client', 'get_form', 'review_status', 'submitted_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['review_status', 'submitted_at', 'reviewed_at']
    search_fields = ['assignment__client__first_name', 'assignment__client__last_name', 'assignment__tax_form__name']
    readonly_fields = ['id', 'submitted_at', 'reviewed_at', 'ip_address', 'user_agent']
    date_hierarchy = 'submitted_at'
    
    def get_client(self, obj):
        return obj.assignment.client.full_name
    get_client.short_description = 'Client'
    get_client.admin_order_field = 'assignment__client__last_name'
    
    def get_form(self, obj):
        return obj.assignment.tax_form.name
    get_form.short_description = 'Form'
    get_form.admin_order_field = 'assignment__tax_form__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assignment__client', 'assignment__tax_form', 'reviewed_by')


@admin.register(TaxDocument)
class TaxDocumentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'document_type', 'get_client', 'uploaded_at', 'file_size']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['file_name', 'description', 'submission__assignment__client__first_name', 'submission__assignment__client__last_name']
    readonly_fields = ['id', 'uploaded_at', 'file_size', 'mime_type']
    date_hierarchy = 'uploaded_at'
    
    def get_client(self, obj):
        return obj.submission.assignment.client.full_name
    get_client.short_description = 'Client'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('submission__assignment__client')
