from django.contrib import admin
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
    list_display = ['employee_id', 'get_full_name', 'department', 'position', 'is_active', 'is_email_verified', 'hire_date']
    list_filter = ['department', 'position', 'is_active', 'is_email_verified', 'hire_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email', 'department', 'position']
    readonly_fields = ['id', 'hire_date', 'created_at', 'updated_at']
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'employee_id', 'phone')
        }),
        ('Work Information', {
            'fields': ('department', 'position', 'hire_date')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_email_verified', 'email_verification_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    actions = ['activate_employees', 'deactivate_employees', 'verify_emails']
    
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