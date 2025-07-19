from django.db import models
from django.contrib.auth.models import User
import uuid

class ContactForm(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()

class JobPosting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default='On-site')
    job_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ], default='full_time')
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    benefits = models.TextField(blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    experience_level = models.CharField(max_length=50, choices=[
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ], default='mid')
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    application_deadline = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.department}"

class Career(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    position_applied = models.CharField(max_length=200)  # Keep for backward compatibility
    experience_years = models.IntegerField()
    education = models.CharField(max_length=200)
    skills = models.TextField()
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    portfolio_website = models.URLField(blank=True, null=True)
    available_start_date = models.DateField()
    salary_expectation = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, choices=[
        ('submitted', 'Submitted'),
        ('reviewing', 'Under Review'),
        ('interview', 'Interview Scheduled'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ], default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # AI Analysis fields
    ai_analysis_completed = models.BooleanField(default=False)
    ai_match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="AI calculated match score (0-100)")
    ai_skills_match = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Skills alignment score (0-100)")
    ai_experience_match = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Experience alignment score (0-100)")
    ai_education_match = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Education alignment score (0-100)")
    ai_summary = models.TextField(blank=True, null=True, help_text="AI generated summary of the candidate")
    ai_strengths = models.TextField(blank=True, null=True, help_text="AI identified candidate strengths")
    ai_concerns = models.TextField(blank=True, null=True, help_text="AI identified potential concerns")
    ai_recommendation = models.CharField(max_length=50, choices=[
        ('highly_recommended', 'Highly Recommended'),
        ('recommended', 'Recommended'),
        ('consider', 'Consider'),
        ('not_recommended', 'Not Recommended'),
    ], blank=True, null=True)
    ai_processed_at = models.DateTimeField(null=True, blank=True)
    resume_text = models.TextField(blank=True, null=True, help_text="Extracted text from resume")
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.job_posting.title}"

    def save(self, *args, **kwargs):
        # Auto-fill position_applied from job_posting for backward compatibility
        if self.job_posting:
            self.position_applied = self.job_posting.title
        super().save(*args, **kwargs)

class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('IT', 'Information Technology'),
        ('HR', 'Human Resources'),
        ('Finance', 'Finance'),
        ('Marketing', 'Marketing'),
        ('Sales', 'Sales'),
        ('Operations', 'Operations'),
        ('Management', 'Management'),
        ('Other', 'Other'),
    ]
    
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
        ('super_admin', 'Super Administrator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='Other')
    position = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    last_login_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Storage management fields
    storage_used = models.BigIntegerField(default=0, help_text="Storage used in bytes")
    storage_quota = models.BigIntegerField(null=True, blank=True, help_text="Storage quota in bytes")
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.employee_id}"
    
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def is_admin(self):
        return self.role in ['admin', 'super_admin']
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def can_manage_users(self):
        return self.role in ['admin', 'super_admin']
    
    def get_storage_used_display(self):
        """Return human-readable storage used"""
        return self._format_bytes(self.storage_used)
    
    def get_storage_quota_display(self):
        """Return human-readable storage quota"""
        if self.storage_quota:
            return self._format_bytes(self.storage_quota)
        return "No limit"
    
    def get_storage_percentage(self):
        """Return storage usage percentage"""
        if not self.storage_quota or self.storage_quota == 0:
            return 0
        return min(100, (self.storage_used / self.storage_quota) * 100)
    
    def get_available_storage(self):
        """Return available storage in bytes"""
        if not self.storage_quota:
            return float('inf')
        return max(0, self.storage_quota - self.storage_used)
    
    def can_upload_file(self, file_size):
        """Check if user can upload a file of given size"""
        if not self.storage_quota:
            return True
        return self.storage_used + file_size <= self.storage_quota
    
    def update_storage_used(self):
        """Recalculate and update storage used from files"""
        from .models import FileDocument
        total_size = FileDocument.objects.filter(uploaded_by=self).aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        self.storage_used = total_size
        self.save(update_fields=['storage_used'])
        return total_size
    
    @staticmethod
    def _format_bytes(bytes_value):
        """Format bytes into human-readable string"""
        if bytes_value == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(bytes_value, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_value / p, 2)
        return f"{s} {size_names[i]}"

class Events(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    eventdate = models.DateField()
    cost = models.IntegerField()
    image = models.FileField(blank=True)
    status = models.BooleanField(default=True)
    def __str__(self):
        return self.title

class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Events, on_delete=models.CASCADE)
    purchaseDate = models.DateField(auto_now_add=True)
    email = models.EmailField()

class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tickets = models.ManyToManyField(Ticket, blank=True)
    email = models.EmailField()
    cost = models.IntegerField()
    verified = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)


# Project Board Models
class Board(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_boards')
    members = models.ManyToManyField(Employee, related_name='boards', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class BoardList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ['board', 'position']
    
    def __str__(self):
        return f"{self.board.title} - {self.title}"


class Card(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    board_list = models.ForeignKey(BoardList, on_delete=models.CASCADE, related_name='cards')
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_cards')
    assigned_to = models.ManyToManyField(Employee, related_name='assigned_cards', blank=True)
    position = models.PositiveIntegerField(default=0)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['position']
        unique_together = ['board_list', 'position']
    
    def __str__(self):
        return self.title


class CardComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Employee, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.first_name} on {self.card.title}"


class CardAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='card_attachments/')
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(Employee, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment: {self.original_name}"


class BoardShare(models.Model):
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Edit'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='received_board_shares')
    shared_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sent_board_shares')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='view')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['board', 'shared_with']
    
    def __str__(self):
        return f"{self.board.title} shared with {self.shared_with.get_full_name()}"


class BoardActivity(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('share', 'Share'),
        ('edit', 'Edit'),
        ('view', 'View'),
        ('delete', 'Delete'),
        ('archive', 'Archive'),
        ('member_add', 'Member Added'),
        ('member_remove', 'Member Removed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} {self.action} {self.board.title}"


# File Management Models
class FileFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_folders')
    shared_with = models.ManyToManyField(Employee, related_name='shared_folders', blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'parent', 'created_by']
    
    def __str__(self):
        return self.name
    
    def get_path(self):
        """Get the full path of the folder"""
        path = []
        folder = self
        while folder:
            path.append(folder.name)
            folder = folder.parent
        return ' / '.join(reversed(path))


class FileDocument(models.Model):
    FILE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('pdf', 'PDF'),
        ('spreadsheet', 'Spreadsheet'),
        ('presentation', 'Presentation'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    folder = models.ForeignKey(FileFolder, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    uploaded_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='uploaded_files')
    shared_with = models.ManyToManyField(Employee, related_name='shared_files', blank=True)
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    version = models.IntegerField(default=1)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    is_favorite = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'folder', 'uploaded_by']
    
    def __str__(self):
        return self.name
    
    def get_file_size_display(self):
        """Return human readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    def get_file_path(self):
        """Get the absolute path to the file"""
        if self.file:
            return self.file.path
        return None


class FileActivity(models.Model):
    ACTION_CHOICES = [
        ('upload', 'Uploaded'),
        ('download', 'Downloaded'),
        ('view', 'Viewed'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('share', 'Shared'),
        ('rename', 'Renamed'),
        ('move', 'Moved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(FileDocument, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} {self.action} {self.document.name}"


class FileShare(models.Model):
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Edit'),
        ('full', 'Full Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(FileDocument, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='received_shares')
    shared_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sent_shares')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='view')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['document', 'shared_with']
    
    def __str__(self):
        return f"{self.document.name} shared with {self.shared_with.get_full_name()}"


class FileVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(FileDocument, on_delete=models.CASCADE, related_name='versions')
    file = models.FileField(upload_to='document_versions/')
    version_number = models.IntegerField()
    upload_comment = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']
    
    def __str__(self):
        return f"{self.document.name} v{self.version_number}"


class StorageManager:
    """Utility class for managing storage quotas and allocation"""
    
    @staticmethod
    def get_system_storage_info():
        """Get system storage information with configurable limits"""
        import shutil
        import os
        from django.conf import settings
        
        try:
            # Get storage info for the media directory
            media_path = getattr(settings, 'MEDIA_ROOT', '/tmp')
            if not os.path.exists(media_path):
                media_path = '/'
            
            total_disk, used_disk, free_disk = shutil.disk_usage(media_path)
            
            # Check if we have a configured application storage limit
            app_storage_limit = getattr(settings, 'APPLICATION_STORAGE_LIMIT_GB', None)
            
            if app_storage_limit:
                # Use configured limit instead of full disk
                app_total = app_storage_limit * 1024 * 1024 * 1024  # Convert GB to bytes
                
                # Calculate actual usage by summing user storage
                from django.db.models import Sum
                actual_used = Employee.objects.filter(is_active=True).aggregate(
                    total=Sum('storage_used')
                )['total'] or 0
                
                # Add estimated system overhead (website files, database, etc.)
                system_overhead = 1024 * 1024 * 1024  # 1GB for website
                total_used = actual_used + system_overhead
                
                return {
                    'total': app_total,
                    'used': total_used,
                    'free': app_total - total_used,
                    'path': media_path,
                    'is_limited': True,
                    'disk_total': total_disk,
                    'disk_free': free_disk,
                    'configured_limit_gb': app_storage_limit
                }
            else:
                # Fallback to disk usage (current behavior)
                return {
                    'total': total_disk,
                    'used': used_disk,
                    'free': free_disk,
                    'path': media_path,
                    'is_limited': False,
                    'disk_total': total_disk,
                    'disk_free': free_disk
                }
                
        except Exception as e:
            # Fallback values if unable to get disk usage
            return {
                'total': 10 * 1024 * 1024 * 1024,  # 10GB fallback
                'used': 5 * 1024 * 1024 * 1024,   # 5GB fallback
                'free': 5 * 1024 * 1024 * 1024,   # 5GB fallback
                'path': 'unknown',
                'error': str(e)
            }
    
    @staticmethod
    def calculate_user_quota():
        """Calculate storage quota per user based on available space"""
        storage_info = StorageManager.get_system_storage_info()
        active_users = Employee.objects.filter(is_active=True).count()
        
        # Reserve 1GB for website purposes
        reserved_space = 1 * 1024 * 1024 * 1024  # 1GB in bytes
        
        # Calculate available space for users
        available_for_users = max(0, storage_info['free'] - reserved_space)
        
        # If no active users, return 0
        if active_users == 0:
            return 0
        
        # Calculate quota per user
        quota_per_user = available_for_users // active_users
        
        # Minimum quota of 10MB per user
        min_quota = 10 * 1024 * 1024  # 10MB
        
        return max(min_quota, quota_per_user)
    
    @staticmethod
    def update_all_user_quotas():
        """Update storage quotas for all active users"""
        quota_per_user = StorageManager.calculate_user_quota()
        
        active_employees = Employee.objects.filter(is_active=True)
        updated_count = active_employees.update(storage_quota=quota_per_user)
        
        return {
            'quota_per_user': quota_per_user,
            'updated_users': updated_count,
            'quota_display': Employee._format_bytes(quota_per_user)
        }
    
    @staticmethod
    def get_storage_stats():
        """Get comprehensive storage statistics"""
        storage_info = StorageManager.get_system_storage_info()
        
        # Get user storage usage
        total_user_storage = Employee.objects.filter(is_active=True).aggregate(
            total=models.Sum('storage_used')
        )['total'] or 0
        
        # Get file count
        total_files = FileDocument.objects.count()
        
        # Calculate quotas
        quota_per_user = StorageManager.calculate_user_quota()
        active_users = Employee.objects.filter(is_active=True).count()
        total_allocated = quota_per_user * active_users
        
        return {
            'system': storage_info,
            'total_user_storage': total_user_storage,
            'total_files': total_files,
            'quota_per_user': quota_per_user,
            'active_users': active_users,
            'total_allocated': total_allocated,
            'reserved_space': 1 * 1024 * 1024 * 1024,  # 1GB
            'quota_per_user_display': Employee._format_bytes(quota_per_user),
            'total_user_storage_display': Employee._format_bytes(total_user_storage),
            'total_allocated_display': Employee._format_bytes(total_allocated),
        }