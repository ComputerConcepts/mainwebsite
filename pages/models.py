from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import os
import uuid

class StorageAllocation(models.Model):
    """Model to store storage allocation settings"""
    total_allocation_gb = models.FloatField(
        default=6.0, 
        help_text="Total storage allocation for all users in GB"
    )
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.total_allocation_gb} GB allocation (updated by {self.updated_by.username})"
    
    @classmethod
    def get_current_allocation(cls):
        """Get the current storage allocation setting"""
        latest = cls.objects.first()
        return latest.total_allocation_gb if latest else 6.0  # Default to 6GB
    
    @classmethod
    def set_allocation(cls, allocation_gb, user):
        """Set a new storage allocation"""
        return cls.objects.create(
            total_allocation_gb=allocation_gb,
            updated_by=user
        )

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
        ('Tax', 'Tax'),
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
    
    @property
    def username(self):
        """Backward compatibility property for username access"""
        return self.user.username
    
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
    
    def get_storage_quota_gb(self):
        """Return storage quota in GB"""
        if self.storage_quota:
            return round(self.storage_quota / (1024 * 1024 * 1024), 2)
        return 0
    
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
    
    def get_available_storage_display(self):
        """Return human-readable available storage"""
        available = self.get_available_storage()
        if available == float('inf'):
            return "Unlimited"
        return self._format_bytes(available)
    
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
        import math

        if bytes_value is None:
            return "0 B"
        if isinstance(bytes_value, (int, float)):
            if math.isinf(bytes_value):
                return "Unlimited"
            if bytes_value <= 0:
                return "0 B"
        else:
            try:
                bytes_value = float(bytes_value)
            except (TypeError, ValueError):
                return "0 B"
            if math.isinf(bytes_value) or bytes_value <= 0:
                return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(bytes_value, 1024)))
        i = min(i, len(size_names) - 1)
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
    
    @property
    def is_image(self):
        """Check if file is an image"""
        return self.file_type == 'image' or (self.mime_type and self.mime_type.startswith('image/'))
    
    @property
    def is_pdf(self):
        """Check if file is a PDF"""
        return self.file_type == 'pdf' or (self.mime_type and 'pdf' in self.mime_type.lower())
    
    @property
    def is_video(self):
        """Check if file is a video"""
        return self.file_type == 'video' or (self.mime_type and self.mime_type.startswith('video/'))
    
    @property
    def is_audio(self):
        """Check if file is an audio file"""
        return self.file_type == 'audio' or (self.mime_type and self.mime_type.startswith('audio/'))


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
        """Calculate storage quota per user based on manual allocation"""
        # Get current manual allocation
        total_allocation_gb = StorageAllocation.get_current_allocation()
        total_allocation_bytes = total_allocation_gb * 1024 * 1024 * 1024
        
        active_users = Employee.objects.filter(is_active=True).count()
        
        # If no active users, return 0
        if active_users == 0:
            return 0
        
        # Calculate quota per user (evenly divided)
        quota_per_user = total_allocation_bytes // active_users
        
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
        # Get manual allocation setting
        total_allocation_gb = StorageAllocation.get_current_allocation()
        total_allocation_bytes = total_allocation_gb * 1024 * 1024 * 1024
        
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
        
        # Calculate usage percentage
        usage_percentage = (total_user_storage / total_allocation_bytes * 100) if total_allocation_bytes > 0 else 0
        
        return {
            'total_system_storage': total_allocation_bytes,
            'total_system_storage_display': Employee._format_bytes(total_allocation_bytes),
            'used_storage_display': Employee._format_bytes(total_user_storage),
            'available_for_users': total_allocation_bytes,
            'available_for_users_display': Employee._format_bytes(total_allocation_bytes),
            'per_user_quota_display': Employee._format_bytes(quota_per_user),
            'usage_percentage': min(100, usage_percentage),
            'total_user_storage': total_user_storage,
            'total_files': total_files,
            'quota_per_user': quota_per_user,
            'active_users': active_users,
            'total_allocated': total_allocated,
            'quota_per_user_display': Employee._format_bytes(quota_per_user),
            'total_user_storage_display': Employee._format_bytes(total_user_storage),
            'total_allocated_display': Employee._format_bytes(total_allocated),
            'manual_allocation_gb': total_allocation_gb,
        }


# AI Workflow Models
class AIWorkflowRule(models.Model):
    """Model for storing AI workflow automation rules"""
    TRIGGER_CHOICES = [
        ('file_upload', 'File Upload'),
        ('file_modified', 'File Modified'),
        ('file_shared', 'File Shared'),
        ('schedule_based', 'Schedule Based'),
        ('threshold_reached', 'Threshold Reached'),
        ('user_action', 'User Action'),
        ('time_based', 'Time Based'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    conditions = models.JSONField(default=dict, help_text="Workflow conditions as JSON")
    actions = models.JSONField(default=list, help_text="Workflow actions as JSON")
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_workflows')
    created_at = models.DateTimeField(auto_now_add=True)
    last_executed = models.DateTimeField(null=True, blank=True)
    execution_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.trigger})"


class AIWorkflowExecution(models.Model):
    """Model for storing workflow execution history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_rule = models.ForeignKey(AIWorkflowRule, on_delete=models.CASCADE, related_name='executions')
    triggered_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='triggered_workflows', null=True, blank=True)
    document = models.ForeignKey(FileDocument, on_delete=models.CASCADE, related_name='workflow_executions', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    context_data = models.JSONField(default=dict, help_text="Execution context data")
    result_data = models.JSONField(default=dict, help_text="Execution results")
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True, help_text="Execution time in milliseconds")
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow_rule.name} - {self.status}"


class AINotification(models.Model):
    """Model for storing AI-generated notifications"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('security', 'Security'),
        ('storage_management', 'Storage Management'),
        ('collaboration', 'Collaboration'),
        ('duplicate_detection', 'Duplicate Detection'),
        ('content_quality', 'Content Quality'),
        ('file_management', 'File Management'),
        ('workflow', 'Workflow'),
        ('general', 'General'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    user = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ai_notifications')
    document = models.ForeignKey(FileDocument, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    workflow_execution = models.ForeignKey(AIWorkflowExecution, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    data = models.JSONField(default=dict, help_text="Additional notification data")
    is_read = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class AINotificationPreference(models.Model):
    """Model for storing user notification preferences"""
    user = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    priority_threshold = models.CharField(
        max_length=10, 
        choices=AINotification.PRIORITY_CHOICES, 
        default='medium',
        help_text="Minimum priority level for notifications"
    )
    
    # Category preferences
    security_notifications = models.BooleanField(default=True)
    storage_notifications = models.BooleanField(default=True)
    collaboration_notifications = models.BooleanField(default=True)
    duplicate_notifications = models.BooleanField(default=False)
    quality_notifications = models.BooleanField(default=False)
    file_management_notifications = models.BooleanField(default=True)
    workflow_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.user.username}"
    
    def get_category_preferences(self):
        """Return category preferences as a dictionary"""
        return {
            'security': self.security_notifications,
            'storage_management': self.storage_notifications,
            'collaboration': self.collaboration_notifications,
            'duplicate_detection': self.duplicate_notifications,
            'content_quality': self.quality_notifications,
            'file_management': self.file_management_notifications,
            'workflow': self.workflow_notifications,
        }


class AIFileAnalysis(models.Model):
    """Model for storing AI analysis results of files"""
    # Status choices for queue management
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    document = models.OneToOneField(FileDocument, on_delete=models.CASCADE, related_name='ai_analysis')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    priority = models.IntegerField(default=5, help_text="Processing priority (1=highest, 10=lowest)")
    
    # Analysis lifecycle timestamps
    queued_at = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    analysis_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Retry management
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Legacy field for backward compatibility
    analysis_completed = models.BooleanField(default=False)
    analysis_started_at = models.DateTimeField(auto_now_add=True)
    
    # Content Analysis
    content_type = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=10, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    
    # AI Insights
    category = models.CharField(max_length=100, blank=True, help_text="AI-determined category")
    key_topics = models.JSONField(default=list, help_text="Extracted key topics")
    entities = models.JSONField(default=list, help_text="Named entities found")
    sentiment_score = models.FloatField(null=True, blank=True, help_text="Sentiment analysis score (-1 to 1)")
    sentiment_label = models.CharField(max_length=20, blank=True, help_text="Sentiment label")
    readability_score = models.FloatField(null=True, blank=True, help_text="Readability score")
    complexity_score = models.FloatField(null=True, blank=True, help_text="Content complexity score")
    quality_score = models.FloatField(null=True, blank=True, help_text="Overall quality score")
    
    # Security Analysis
    contains_sensitive_info = models.BooleanField(default=False)
    sensitive_info_types = models.JSONField(default=list, help_text="Types of sensitive information found")
    security_risk_level = models.CharField(max_length=20, default='low', help_text="Security risk assessment")
    
    # Content Structure
    has_images = models.BooleanField(default=False)
    has_tables = models.BooleanField(default=False)
    has_links = models.BooleanField(default=False)
    
    # Recommendations
    ai_recommendations = models.JSONField(default=list, help_text="AI-generated recommendations")
    suggested_tags = models.JSONField(default=list, help_text="AI-suggested tags")
    suggested_category = models.CharField(max_length=100, blank=True)
    
    # Analysis data storage
    analysis_data = models.JSONField(default=dict, help_text="Complete analysis results and metadata")
    tags = models.JSONField(default=list, help_text="Generated tags for the file")
    
    # Processing metadata
    processing_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-analysis_started_at']
    
    def __str__(self):
        return f"AI Analysis for {self.document.name}"
    
    def mark_completed(self, processing_time_ms=None):
        """Mark analysis as completed"""
        self.status = 'completed'
        self.analysis_completed = True
        self.analysis_completed_at = timezone.now()
        if processing_time_ms:
            self.processing_time_ms = processing_time_ms
        self.save(update_fields=['status', 'analysis_completed', 'analysis_completed_at', 'processing_time_ms'])
    
    def mark_processing(self):
        """Mark analysis as currently being processed"""
        self.status = 'processing'
        self.processing_started_at = timezone.now()
        self.save(update_fields=['status', 'processing_started_at'])
    
    def mark_failed(self, error_message=None):
        """Mark analysis as failed"""
        if self.retry_count < self.max_retries:
            self.status = 'retrying'
            self.retry_count += 1
        else:
            self.status = 'failed'
        
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'retry_count', 'error_message'])
    
    @classmethod
    def get_next_in_queue(cls):
        """Get the next queued analysis to process"""
        return cls.objects.filter(
            status__in=['queued', 'retrying']
        ).order_by('priority', 'queued_at').first()
    
    @classmethod 
    def get_queue_stats(cls):
        """Get queue statistics"""
        from django.db.models import Count
        return cls.objects.values('status').annotate(count=Count('status'))


class ChatChannel(models.Model):
    """Chat channels for group conversations"""
    CHANNEL_TYPES = [
        ('general', 'General'),
        ('department', 'Department'),
        ('project', 'Project'),
        ('board', 'Board Discussion'),
        ('private', 'Private Group'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES, default='general')
    created_by = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='created_channels')
    members = models.ManyToManyField('Employee', through='ChatChannelMembership', related_name='chat_channels')
    
    # Optional association with a specific board
    associated_board = models.ForeignKey('Board', on_delete=models.SET_NULL, null=True, blank=True, related_name='associated_channels')
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"#{self.name}"
    
    def get_latest_message(self):
        return self.messages.order_by('-created_at').first()
    
    def get_member_count(self):
        return self.members.count()
    
    def get_shared_boards(self):
        """Get all boards shared in this channel"""
        return Board.objects.filter(chat_shares__channel=self, chat_shares__is_active=True).distinct()
    
    def get_shared_files(self):
        """Get all files shared in this channel"""
        return FileDocument.objects.filter(chat_shares__channel=self, chat_shares__is_active=True).distinct()
    
    def add_board_access_to_members(self, board):
        """Add all channel members to the board"""
        for member in self.members.all():
            if not board.members.filter(id=member.id).exists():
                board.members.add(member)
    
    def get_activity_summary(self):
        """Get recent activity summary for this channel"""
        from django.db.models import Count
        recent_messages = self.messages.filter(created_at__gte=timezone.now() - timedelta(days=7))
        
        return {
            'recent_message_count': recent_messages.count(),
            'active_members': recent_messages.values('sender').distinct().count(),
            'shared_boards_count': self.shared_boards.filter(is_active=True).count(),
            'shared_files_count': self.shared_files.filter(is_active=True).count(),
        }


class ChatChannelMembership(models.Model):
    """Through model for channel membership with additional data"""
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['channel', 'employee']
    
    def get_unread_count(self):
        return self.channel.messages.filter(
            created_at__gt=self.last_read_at
        ).count()


class ChatMessage(models.Model):
    """Individual chat messages"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('board', 'Board Share'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    file_attachment = models.FileField(upload_to='chat_files/', null=True, blank=True)
    
    # New fields for board and file integration
    shared_board = models.ForeignKey('Board', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    shared_file = models.ForeignKey('FileDocument', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        target = f"#{self.channel.name}" if self.channel else f"@{self.recipient.user.username}"
        return f"{self.sender.user.username} → {target}: {self.content[:50]}..."
    
    def is_direct_message(self):
        return self.recipient is not None and self.channel is None
    
    def mark_as_edited(self):
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()
    
    def has_board_attachment(self):
        return self.shared_board is not None
    
    def has_file_attachment(self):
        return self.shared_file is not None or self.file_attachment
    
    def get_attachment_info(self):
        """Get information about any attachments in this message"""
        attachments = []
        
        if self.shared_board:
            attachments.append({
                'type': 'board',
                'id': self.shared_board.id,
                'name': self.shared_board.title,
                'description': self.shared_board.description,
                'url': f"/employee/boards/{self.shared_board.id}/"
            })
        
        if self.shared_file:
            attachments.append({
                'type': 'file',
                'id': self.shared_file.id,
                'name': self.shared_file.name,
                'size': self.shared_file.get_file_size_display(),
                'file_type': self.shared_file.file_type,
                'url': f"/employee/files/download/{self.shared_file.id}/"
            })
        
        if self.file_attachment:
            import os
            attachments.append({
                'type': 'upload',
                'name': os.path.basename(self.file_attachment.name),
                'url': self.file_attachment.url
            })
        
        return attachments


class ChatMessageRead(models.Model):
    """Track which messages have been read by which users"""
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_receipts')
    reader = models.ForeignKey('Employee', on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'reader']
        
    def __str__(self):
        return f"{self.reader.user.username} read message at {self.read_at}"


class ChatNotification(models.Model):
    """Notifications for chat messages"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('mention', 'Mentioned'),
        ('channel_invite', 'Channel Invite'),
        ('board_shared', 'Board Shared'),
        ('file_shared', 'File Shared'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='chat_notifications')
    sender = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='sent_chat_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, null=True, blank=True)
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Chat notification for {self.recipient.user.username}: {self.content[:50]}..."


class ChatBoardShare(models.Model):
    """Boards shared in chat channels"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE, related_name='shared_boards')
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='chat_shares')
    shared_by = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='shared_boards_in_chat')
    shared_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, help_text="Optional message when sharing the board")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['channel', 'board']
        ordering = ['-shared_at']
    
    def __str__(self):
        return f"Board '{self.board.title}' shared in #{self.channel.name}"
    
    def get_access_count(self):
        """Count how many channel members have accessed this board"""
        return self.board.members.filter(chat_channels=self.channel).count()


class ChatFileShare(models.Model):
    """Files shared in chat messages or channels"""
    SHARE_TYPES = [
        ('message', 'Shared in Message'),
        ('channel', 'Shared to Channel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE, related_name='shared_files', null=True, blank=True)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attached_files', null=True, blank=True)
    file_document = models.ForeignKey('FileDocument', on_delete=models.CASCADE, related_name='chat_shares')
    shared_by = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='shared_files_in_chat')
    share_type = models.CharField(max_length=20, choices=SHARE_TYPES, default='message')
    shared_at = models.DateTimeField(auto_now_add=True)
    share_message = models.TextField(blank=True, help_text="Optional message when sharing the file")
    download_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-shared_at']
    
    def __str__(self):
        if self.message:
            return f"File '{self.file_document.name}' shared in message"
        else:
            return f"File '{self.file_document.name}' shared in #{self.channel.name}"
    
    def get_download_stats(self):
        """Get download statistics for this shared file"""
        return {
            'total_downloads': self.download_count,
            'shared_at': self.shared_at,
            'shared_by': self.shared_by.user.get_full_name() or self.shared_by.user.username
        }


# HR Onboarding System Models

class OnboardingForm(models.Model):
    """Template for HR onboarding forms"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, help_text="Form title")
    description = models.TextField(blank=True, help_text="Form description")
    form_fields = models.JSONField(default=dict, help_text="Form field configuration")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_onboarding_forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Settings
    pin_expiry_hours = models.IntegerField(default=48, help_text="PIN expiry time in hours")
    allow_multiple_submissions = models.BooleanField(default=False)
    send_confirmation_email = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ProspectiveEmployee(models.Model):
    """Temporary user account for prospective employees"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # PIN system
    current_pin = models.CharField(max_length=6, blank=True)
    pin_created_at = models.DateTimeField(null=True, blank=True)
    pin_expiry = models.DateTimeField(null=True, blank=True)
    pin_attempts = models.IntegerField(default=0)
    is_pin_locked = models.BooleanField(default=False)
    
    # Session tracking
    last_login = models.DateTimeField(null=True, blank=True)
    login_attempts = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited_prospects')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email
    
    def is_pin_valid(self):
        """Check if the current PIN is still valid"""
        if not self.current_pin or not self.pin_expiry:
            return False
        return timezone.now() < self.pin_expiry and not self.is_pin_locked
    
    def generate_pin(self, expiry_at=None, expiry_hours=48):
        """Generate a new 6-digit PIN and optionally control expiry"""
        import random
        from datetime import timedelta
        
        self.current_pin = str(random.randint(100000, 999999))
        self.pin_created_at = timezone.now()
        if expiry_at:
            self.pin_expiry = expiry_at
        else:
            self.pin_expiry = timezone.now() + timedelta(hours=expiry_hours or 48)
        self.pin_attempts = 0
        self.is_pin_locked = False
        self.save()
        return self.current_pin


class OnboardingInvitation(models.Model):
    """Track onboarding invitations sent to prospective employees"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    onboarding_form = models.ForeignKey(OnboardingForm, on_delete=models.CASCADE)
    prospective_employee = models.ForeignKey(ProspectiveEmployee, on_delete=models.CASCADE)
    
    # Invitation details
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_onboarding_invitations')
    sent_at = models.DateTimeField(auto_now_add=True)
    custom_message = models.TextField(blank=True, help_text="Custom message for the invitation")
    # Assessments assigned to this invitation (optional)
    assessments = models.ManyToManyField('OnboardingAssessment', blank=True, related_name='invitations')
    
    # Status tracking
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('opened', 'Opened'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    
    # Activity tracking
    first_opened = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['onboarding_form', 'prospective_employee']
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.onboarding_form.title} -> {self.prospective_employee.email}"


def onboarding_pdf_template_upload_path(instance, filename):
    """Path helper for storing blank onboarding PDF templates"""
    identifier = instance.id or uuid.uuid4()
    return os.path.join('onboarding', 'pdf_templates', str(identifier), filename)


def onboarding_pdf_submission_upload_path(instance, filename):
    """Path helper for storing completed onboarding PDF submissions"""
    identifier = instance.id or uuid.uuid4()
    return os.path.join('onboarding', 'pdf_submissions', str(identifier), filename)


class OnboardingPDFForm(models.Model):
    """Blank PDF documents that prospects must download, fill, and re-upload"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to=onboarding_pdf_template_upload_path)
    default_instructions = models.TextField(
        blank=True,
        help_text="Guidance shown to prospects when completing this PDF."
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_pdf_forms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class OnboardingPDFTask(models.Model):
    """Assignment linking a PDF form to a specific invitation/prospect workflow"""
    STATUS_PENDING = 'pending'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_NEEDS_REVISION = 'needs_revision'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Awaiting Upload'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_NEEDS_REVISION, 'Needs Revision'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_form = models.ForeignKey(
        OnboardingPDFForm,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    invitation = models.ForeignKey(
        OnboardingInvitation,
        on_delete=models.CASCADE,
        related_name='pdf_tasks'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_onboarding_pdf_tasks'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    custom_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    completed_file = models.FileField(
        upload_to=onboarding_pdf_submission_upload_path,
        blank=True,
        null=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        ProspectiveEmployee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_onboarding_pdf_tasks'
    )
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_onboarding_pdf_tasks'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['pdf_form', 'invitation']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.pdf_form.title} for {self.invitation.prospective_employee.email}"

    @property
    def instructions(self):
        """Instructions visible to the prospect, falling back to the template defaults."""
        return self.custom_instructions or self.pdf_form.default_instructions

    def mark_submitted(self, prospect, uploaded_file):
        """Convenience helper when a prospect uploads a completed PDF."""
        if self.completed_file:
            try:
                self.completed_file.delete(save=False)
            except Exception:
                pass
        self.completed_file = uploaded_file
        self.completed_at = timezone.now()
        self.submitted_by = prospect
        self.status = self.STATUS_SUBMITTED
        self.review_notes = ''
        self.reviewed_by = None
        self.reviewed_at = None
        self.save(
            update_fields=[
                'completed_file',
                'completed_at',
                'submitted_by',
                'status',
                'review_notes',
                'reviewed_by',
                'reviewed_at'
            ]
        )


class OnboardingAssessment(models.Model):
    """Assessments that can be attached to an onboarding flow.

    Questions are stored in a related table `OnboardingAssessmentQuestion`.
    Supports timed or untimed assessments and basic grading for MCQs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_onboarding_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # timing and rules
    is_timed = models.BooleanField(default=False, help_text="If true, candidates have a time limit to complete the assessment")
    time_limit_minutes = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes when timed")
    allow_multiple_attempts = models.BooleanField(default=False)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Optional passing score (percentage)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class OnboardingAssessmentQuestion(models.Model):
    """A single question in an assessment.

    - question_type: 'mcq' or 'open'
    - choices: list of choice strings (for mcq)
    - correct_answer: for mcq, store index(es) or value(s) as JSON
    """
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('open', 'Open Ended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(OnboardingAssessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='open')
    # For MCQ questions: a list of option strings
    choices = models.JSONField(default=list, blank=True, help_text='Choice options for MCQ questions')
    # The correct answer(s) for MCQ: store as index (int) or list of indices
    correct_answer = models.JSONField(null=True, blank=True, help_text='Index or list of indices indicating correct choice(s)')
    allow_multiple_answers = models.BooleanField(default=False, help_text='When true, candidates may select multiple choices')
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.assessment.title} - {self.question_text[:60]}"


class OnboardingAssessmentAttempt(models.Model):
    """Records a candidate's attempt at an assessment."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(OnboardingAssessment, on_delete=models.CASCADE, related_name='attempts')
    invitation = models.ForeignKey(OnboardingInvitation, on_delete=models.CASCADE, related_name='assessment_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='Total points earned')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Percentage score')
    is_submitted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Attempt {self.id} - {self.assessment.title} for {self.invitation.prospective_employee.email}"

    def grade(self):
        """Auto-grade MCQ responses and compute totals. Returns (score, percentage)."""
        total_points = 0
        earned = 0
        for resp in self.responses.select_related('question').all():
            q = resp.question
            total_points += float(q.points or 0)
            if q.question_type == 'mcq' and q.correct_answer is not None:
                try:
                    correct = q.correct_answer
                except Exception:
                    correct = None
                given = resp.answer
                matched = False
                if correct is not None:
                    if q.allow_multiple_answers:
                        def _normalize(value):
                            if value in [None, '', []]:
                                return []
                            if isinstance(value, list):
                                iterable = value
                            else:
                                iterable = [value]
                            normalized = []
                            for item in iterable:
                                if item in [None, '']:
                                    continue
                                normalized.append(str(item))
                            return normalized

                        correct_values = set(_normalize(correct))
                        given_values = set(_normalize(given))
                        matched = bool(correct_values) and given_values == correct_values
                    else:
                        if isinstance(correct, list):
                            for c in correct:
                                if str(c) == str(given):
                                    matched = True
                                    break
                        else:
                            if str(correct) == str(given):
                                matched = True

                if matched:
                    earned += float(q.points or 0)
                    resp.points_awarded = q.points
                else:
                    resp.points_awarded = 0
                resp.save(update_fields=['points_awarded'])
            else:
                # open-ended: cannot auto-grade; leave points_awarded null for manual review
                resp.points_awarded = None
                resp.save(update_fields=['points_awarded'])

        self.score = earned
        if total_points > 0:
            self.percentage = round((earned / total_points) * 100, 2)
        else:
            self.percentage = None
        self.save(update_fields=['score', 'percentage'])
        return (self.score, self.percentage)


class OnboardingAssessmentResponse(models.Model):
    """Stores a single question response within an attempt."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(OnboardingAssessmentAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(OnboardingAssessmentQuestion, on_delete=models.CASCADE)
    # answer may be a string, index, or list depending on question type
    answer = models.JSONField(null=True, blank=True)
    points_awarded = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Response {self.id} (Q: {self.question.id})"


class OnboardingSubmission(models.Model):
    """Store completed onboarding form submissions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.OneToOneField(OnboardingInvitation, on_delete=models.CASCADE)
    
    # Form data
    form_data = models.JSONField(default=dict, help_text="Submitted form data")
    uploaded_files = models.JSONField(default=list, help_text="List of uploaded file paths")
    
    # Submission tracking
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Review process
    REVIEW_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # HR follow-up
    hr_notes = models.TextField(blank=True, help_text="Internal HR notes")
    next_steps = models.TextField(blank=True, help_text="Next steps in the process")
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.invitation.onboarding_form.title} - {self.invitation.prospective_employee.email}"
    
    def get_applicant_name(self):
        """Get the applicant's full name from form data or email"""
        if 'first_name' in self.form_data and 'last_name' in self.form_data:
            return f"{self.form_data['first_name']} {self.form_data['last_name']}"
        return self.invitation.prospective_employee.email


class OnboardingOfferLetter(models.Model):
    """Formal employment offer generated from an onboarding submission"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_employee', 'Awaiting Employee Signature'),
        ('signed', 'Fully Signed'),
        ('declined', 'Declined'),
    ]

    COMPENSATION_FREQUENCY_CHOICES = [
        ('annual', 'Per Year'),
        ('monthly', 'Per Month'),
        ('biweekly', 'Per Pay Period'),
        ('weekly', 'Per Week'),
        ('hourly', 'Per Hour'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(
        OnboardingSubmission,
        on_delete=models.CASCADE,
        related_name='offer_letter'
    )
    job_posting = models.ForeignKey(
        'JobPosting',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offer_letters'
    )

    position_title = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=100, blank=True)
    salary_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    pay_frequency = models.CharField(
        max_length=20,
        choices=COMPENSATION_FREQUENCY_CHOICES,
        default='annual'
    )
    compensation_notes = models.TextField(blank=True, help_text="Additional compensation details (bonuses, benefits, etc.)")
    start_date = models.DateField(null=True, blank=True)
    offer_expires_at = models.DateField(null=True, blank=True)
    additional_terms = models.TextField(blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offer_letters_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    employer_signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offer_letters_signed'
    )
    employer_signature_name = models.CharField(max_length=200, blank=True)
    employer_signature_data = models.TextField(blank=True, help_text="Base64 encoded employer signature image")
    employer_signed_at = models.DateTimeField(null=True, blank=True)

    employee_signature_name = models.CharField(max_length=200, blank=True)
    employee_signed_at = models.DateTimeField(null=True, blank=True)
    employee_signature_data = models.TextField(blank=True, help_text="Base64 encoded employee signature image")
    decline_reason = models.TextField(blank=True)
    offer_pdf_path = models.CharField(max_length=500, blank=True, help_text="Stored PDF path for the signed offer letter")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        applicant = self.submission.get_applicant_name()
        return f"Offer Letter for {applicant} ({self.position_title})"

    @property
    def is_employer_signed(self):
        return bool(self.employer_signed_at and self.employer_signature_name and self.employer_signature_data)

    @property
    def is_employee_signed(self):
        return bool(self.employee_signed_at and self.employee_signature_name and self.employee_signature_data)


class OnboardingFormField(models.Model):
    """Define field types for onboarding forms"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('email', 'Email'),
        ('phone', 'Phone Number'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('file', 'File Upload'),
        ('signature', 'Digital Signature'),
    ]
    
    onboarding_form = models.ForeignKey(OnboardingForm, on_delete=models.CASCADE, related_name='fields')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    field_name = models.CharField(max_length=100, help_text="Internal field name")
    field_label = models.CharField(max_length=200, help_text="Display label")
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    
    # Validation
    is_required = models.BooleanField(default=False)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    validation_regex = models.CharField(max_length=500, blank=True, help_text="Regex pattern for validation")
    
    # Options for select/radio/checkbox fields
    field_options = models.JSONField(default=list, help_text="Options for select/radio/checkbox fields")
    
    # Display
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'id']
        unique_together = ['onboarding_form', 'field_name']
    
    def __str__(self):
        return f"{self.onboarding_form.title} - {self.field_label}"


# =============================================================================
# TAX FORM MODELS
# =============================================================================

class TaxFormTemplate(models.Model):
    """Predefined tax form templates (Intake Form, Schedule C, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Form name (e.g., 'Tax Intake Form')")
    form_type = models.CharField(max_length=50, choices=[
        ('intake', 'Tax Intake Form'),
        ('schedule_c', 'Schedule C - Business Income'),
        ('schedule_a', 'Schedule A - Itemized Deductions'),
        ('income_summary', 'Income Summary'),
        ('dependent_care', 'Dependent Care Form'),
        ('student_ack', 'Student Acknowledgment'),
        ('photo_id', 'Photo ID and Voided Check'),
        ('due_diligence', 'Due Diligence Questionnaire'),
        ('refund_type', 'Refund Type Selection'),
        ('affordable_care', 'Affordable Care Details'),
        ('custom', 'Custom Form')
    ], default='custom')
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, help_text="Instructions for filling out the form")
    
    # Form settings
    is_active = models.BooleanField(default=True)
    requires_signature = models.BooleanField(default=True)
    allow_multiple_submissions = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tax_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['form_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_form_type_display()})"


class TaxFormField(models.Model):
    """Fields within tax form templates"""
    FIELD_TYPE_CHOICES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('email', 'Email'),
        ('phone', 'Phone Number'),
        ('number', 'Number'),
        ('currency', 'Currency ($)'),
        ('date', 'Date'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('file', 'File Upload'),
        ('signature', 'Digital Signature'),
        ('ssn', 'Social Security Number'),
        ('ein', 'Employer ID Number'),
        ('address', 'Address Block'),
        ('name', 'Full Name'),
        ('section_header', 'Section Header'),
        ('table', 'Data Table'),
        ('yes_no', 'Yes/No Radio'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxFormTemplate, on_delete=models.CASCADE, related_name='fields')
    
    # Field definition
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    field_name = models.CharField(max_length=100, help_text="Internal field name")
    field_label = models.CharField(max_length=300, help_text="Display label")
    placeholder = models.CharField(max_length=300, blank=True)
    help_text = models.TextField(blank=True)
    
    # Validation
    is_required = models.BooleanField(default=False)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    validation_regex = models.CharField(max_length=500, blank=True)
    
    # Options for select/radio/checkbox fields
    field_options = models.JSONField(default=list, help_text="Options for select/radio/checkbox fields")
    
    # Layout and display
    section = models.CharField(max_length=100, blank=True, help_text="Section name for grouping")
    order = models.IntegerField(default=0, help_text="Display order within section")
    column_width = models.CharField(max_length=20, default='full', choices=[
        ('full', 'Full Width'),
        ('half', 'Half Width'),
        ('third', 'Third Width'),
        ('quarter', 'Quarter Width')
    ])
    is_active = models.BooleanField(default=True)
    
    # Tax-specific attributes
    tax_line_reference = models.CharField(max_length=100, blank=True, help_text="IRS form line reference")
    is_calculated = models.BooleanField(default=False, help_text="Is this field auto-calculated?")
    calculation_formula = models.TextField(blank=True, help_text="Formula for calculated fields")
    
    class Meta:
        ordering = ['section', 'order', 'id']
        unique_together = ['tax_form', 'field_name']
    
    def __str__(self):
        return f"{self.tax_form.name} - {self.field_label}"


class TaxClient(models.Model):
    """Tax preparation clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic client info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    # Tax-specific info
    ssn = models.CharField(max_length=11, blank=True, help_text="Format: XXX-XX-XXXX")
    date_of_birth = models.DateField(null=True, blank=True)
    filing_status = models.CharField(max_length=20, choices=[
        ('single', 'Single'),
        ('married_joint', 'Married Filing Jointly'),
        ('married_separate', 'Married Filing Separately'),
        ('head_of_household', 'Head of Household'),
        ('qualifying_widow', 'Qualifying Widow(er)')
    ], blank=True)
    
    # Access control
    is_active = models.BooleanField(default=True)
    current_pin = models.CharField(max_length=10, blank=True, help_text="PIN for secure access")
    pin_expiry = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Internal notes about this client")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tax_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def generate_pin(self):
        """Generate a secure 6-digit PIN"""
        import random
        self.current_pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.save()
        return self.current_pin
    
    def is_pin_valid(self):
        """Check if the current PIN is still valid"""
        if not self.current_pin or not self.pin_expiry:
            return False
        return timezone.now() < self.pin_expiry
    
    def has_completed_waiver(self):
        """Check if client has completed the waiver"""
        try:
            return self.waiver.is_completed
        except TaxClientWaiver.DoesNotExist:
            return False
    
    def can_be_assigned_forms(self):
        """Check if client can be assigned tax forms"""
        return self.has_completed_waiver()


class TaxClientWaiver(models.Model):
    """Waiver and consent forms for tax clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.OneToOneField(TaxClient, on_delete=models.CASCADE, related_name='waiver')
    
    # Waiver content tracking
    waiver_version = models.CharField(max_length=20, default='1.0', help_text="Version of waiver terms")
    
    # Client consent tracking
    client_signed = models.BooleanField(default=False)
    client_signature_data = models.TextField(blank=True, help_text="Base64 signature image data")
    client_signed_at = models.DateTimeField(null=True, blank=True)
    client_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Employee tracking
    employee_witnessed = models.BooleanField(default=False)
    witnessed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='witnessed_waivers')
    witnessed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional consent fields
    consent_data_processing = models.BooleanField(default=False, help_text="Consent to process tax data")
    consent_document_storage = models.BooleanField(default=False, help_text="Consent to store documents")
    consent_electronic_delivery = models.BooleanField(default=False, help_text="Consent to electronic document delivery")
    consent_third_party_disclosure = models.BooleanField(default=False, help_text="Consent for IRS/state communications")
    
    # Notes and tracking
    notes = models.TextField(blank=True, help_text="Additional notes about waiver")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Waiver for {self.client.full_name}"
    
    @property
    def is_completed(self):
        """Check if waiver is fully completed"""
        return (self.client_signed and 
                self.consent_data_processing and 
                self.consent_document_storage and 
                self.consent_electronic_delivery)
    
    @property
    def completion_status(self):
        """Get human-readable completion status"""
        if self.is_completed:
            return "Completed"
        elif self.client_signed:
            return "Signed but missing consents"
        else:
            return "Pending signature"


class TaxFormAssignment(models.Model):
    """Assignment of tax forms to clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_form = models.ForeignKey(TaxFormTemplate, on_delete=models.CASCADE)
    client = models.ForeignKey(TaxClient, on_delete=models.CASCADE)
    
    # Assignment details
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    custom_instructions = models.TextField(blank=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('ready_for_signature', 'Ready for Client Signature'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('needs_revision', 'Needs Revision'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    
    # Activity tracking
    first_accessed = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['tax_form', 'client']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.client.full_name} - {self.tax_form.name}"


class TaxFormSubmission(models.Model):
    """Client submissions of tax forms"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.OneToOneField(TaxFormAssignment, on_delete=models.CASCADE)
    
    # Form data
    form_data = models.JSONField(default=dict, help_text="Submitted form field values")
    uploaded_files = models.JSONField(default=list, help_text="List of uploaded file paths")
    
    # Two-step workflow: Employee completion + Client signature
    # Employee completion
    employee_completed_at = models.DateTimeField(null=True, blank=True, help_text="When employee completed the form")
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tax_submissions_created', help_text="Employee who filled the form")
    internal_notes = models.TextField(blank=True, help_text="Internal notes from employee")
    
    # Client signature
    client_signature_data = models.TextField(blank=True, help_text="Base64 encoded client signature image")
    client_signed_at = models.DateTimeField(null=True, blank=True, help_text="When client signed the form")
    is_completed = models.BooleanField(default=False, help_text="True when both employee filled and client signed")
    
    # Legacy signature field for backwards compatibility
    signature_data = models.TextField(blank=True, help_text="Base64 encoded signature image (legacy)")
    signature_file_path = models.CharField(max_length=500, blank=True)
    
    # Submission metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Review process
    REVIEW_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('needs_revision', 'Needs Revision'),
        ('rejected', 'Rejected'),
    ]
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tax_submissions_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Tax preparer notes
    preparer_notes = models.TextField(blank=True, help_text="Internal notes for tax preparer")
    estimated_refund = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_owed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.assignment.client.full_name} - {self.assignment.tax_form.name} ({self.submitted_at.date()})"


class TaxDocument(models.Model):
    """Supporting tax documents uploaded by clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(TaxFormSubmission, on_delete=models.CASCADE, related_name='documents')
    
    # Document info
    document_type = models.CharField(max_length=50, choices=[
        ('w2', 'W-2 Form'),
        ('1099', '1099 Form'),
        ('1098', '1098 Form'),
        ('photo_id', 'Photo ID'),
        ('voided_check', 'Voided Check'),
        ('receipt', 'Receipt/Expense'),
        ('bank_statement', 'Bank Statement'),
        ('other', 'Other Document')
    ])
    file_name = models.CharField(max_length=300)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['document_type', '-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.file_name}"
