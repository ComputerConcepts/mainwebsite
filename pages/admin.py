from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count
from .models import ContactForm, Events, Invoice, Ticket, Employee, Career, JobPosting

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
    list_display = ['employee_id', 'get_full_name', 'get_email', 'department', 'position', 'role', 'is_active', 'is_email_verified', 'hire_date', 'last_login_date']
    list_filter = ['department', 'position', 'role', 'is_active', 'is_email_verified', 'hire_date', 'created_at']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email', 'department', 'position', 'phone']
    readonly_fields = ['id', 'hire_date', 'created_at', 'updated_at', 'last_login_date']
    date_hierarchy = 'hire_date'
    list_per_page = 50
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'employee_id', 'phone', 'address', 'emergency_contact', 'emergency_phone')
        }),
        ('Work Information', {
            'fields': ('department', 'position', 'role', 'manager', 'salary', 'hire_date')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_email_verified', 'email_verification_token')
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

    actions = ['activate_employees', 'deactivate_employees', 'verify_emails', 'make_admin', 'make_manager', 'make_employee', 'reset_passwords']
    
    def activate_employees(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} employees activated successfully.')
    activate_employees.short_description = 'Activate selected employees'
    
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} employees deactivated successfully.')
    deactivate_employees.short_description = 'Deactivate selected employees'
    
    def verify_emails(self, request, queryset):
        updated = queryset.update(is_email_verified=True, email_verification_token=None)
        self.message_user(request, f'{updated} employee emails verified successfully.')
    verify_emails.short_description = 'Verify emails for selected employees'
    
    def make_admin(self, request, queryset):
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} employees promoted to admin.')
    make_admin.short_description = 'Make selected employees admins'
    
    def make_manager(self, request, queryset):
        updated = queryset.update(role='manager')
        self.message_user(request, f'{updated} employees promoted to manager.')
    make_manager.short_description = 'Make selected employees managers'
    
    def make_employee(self, request, queryset):
        updated = queryset.update(role='employee')
        self.message_user(request, f'{updated} users set to employee role.')
    make_employee.short_description = 'Set selected users to employee role'
    
    def reset_passwords(self, request, queryset):
        count = 0
        for employee in queryset:
            # Generate a temporary password
            temp_password = f"temp_{employee.employee_id}_2024"
            employee.user.set_password(temp_password)
            employee.user.save()
            count += 1
        self.message_user(request, f'Passwords reset for {count} employees. Temporary password format: temp_[employee_id]_2024')
    reset_passwords.short_description = 'Reset passwords for selected employees'


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