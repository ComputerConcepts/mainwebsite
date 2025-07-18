# Computer Concepts Employee Portal

## Overview
A comprehensive employee portal system for Computer Concepts with robust email verification and management features.

## Features Implemented

### 🔐 Authentication & Security
- **Domain-Restricted Access**: Only @onecomputerconcepts.com email addresses allowed
- **Streamlined Onboarding**: No registration - new users use password reset flow
- **Email Verification**: Token-based email verification system
- **Secure Login**: Authentication with email verification checks
- **Account Management**: Active/inactive status control

### 📧 Email System
- **Automated Verification Emails**: Professional HTML templates
- **Email Testing**: Built-in email testing functionality
- **Resend Verification**: Option to resend verification emails
- **Email Configuration**: Uses Gmail SMTP (configured in settings)

### 🎯 Employee Portal Features
- **Dashboard**: Overview of events, statistics, and account status
- **Profile Management**: Update personal and work information
- **Events Management**: View all events with detailed information
- **Event Details**: Ticket sales, revenue, and customer data
- **Help System**: FAQ and support information

### 🛠 Admin Features
- **Django Admin Integration**: Full admin interface for employees
- **Bulk Actions**: Activate/deactivate employees, verify emails
- **Management Command**: Create superuser employee accounts
- **Advanced Filtering**: Search and filter employees by various criteria

## URLs Structure

### Public URLs
- `/employee/login/` - Employee login page (restricted to @onecomputerconcepts.com)
- `/employee/forgot-password/` - Password reset request (for new and existing users)
- `/employee/reset-password/<uidb64>/<token>/` - Password reset form
- `/employee/verify-email/<id>/` - Email verification page
- `/employee/confirm-email/<id>/<token>/` - Email confirmation handler

### Protected URLs (Login Required)
- `/employee/dashboard/` - Main dashboard
- `/employee/profile/` - Profile management
- `/employee/events/` - Events listing
- `/employee/events/<id>/` - Event details
- `/employee/help/` - Help and FAQ
- `/employee/test-email/` - Email testing tool
- `/employee/logout/` - Logout handler

## Database Models

### Employee Model
```python
class Employee(models.Model):
    id = UUIDField (Primary Key)
    user = OneToOneField(User) 
    employee_id = CharField(max_length=50, unique=True)
    department = CharField(max_length=100)
    position = CharField(max_length=100)
    phone = CharField(max_length=20)
    hire_date = DateField(auto_now_add=True)
    is_active = BooleanField(default=True)
    is_email_verified = BooleanField(default=False)
    email_verification_token = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## Email Configuration

### SMTP Settings (settings.py)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreplycomputerconcepts@gmail.com'
EMAIL_HOST_PASSWORD = 'mmsn wgyv kejj kpms'
DEFAULT_FROM_EMAIL = 'noreplycomputerconcepts@gmail.com'
```

## Management Commands

### Create Superuser Employee
```bash
python manage.py create_employee_superuser
```

## Key Features

### 1. Employee Onboarding Process
1. Admin creates employee email in the domain (@onecomputerconcepts.com)
2. Employee uses "Forgot Password" with company email
3. System sends password reset link to email
4. Employee sets password and completes profile
5. Account activated for login

### 2. Security Features
- CSRF protection on all forms
- Email verification required for login
- Account activation controls
- Secure token generation
- Session management

### 3. User Experience
- Responsive design (Bootstrap 5)
- Professional UI with gradient themes
- Intuitive navigation
- Clear error messages
- Success feedback

### 4. Admin Dashboard
- Full CRUD operations for employees
- Bulk actions for management
- Advanced search and filtering
- Employee statistics
- Email verification controls

## Testing Email Functionality

### Test Email Feature
- Navigate to `/employee/test-email/`
- Enter any email address
- System sends test email
- Verify email delivery and formatting

### Verification Process Test
1. Register new employee account
2. Check email for verification link
3. Click link to verify account
4. Login with verified account

## Installation & Setup

1. **Database Migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create Superuser Employee**
   ```bash
   python manage.py create_employee_superuser
   ```

3. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

4. **Access Portal**
   - Employee Portal: `http://localhost:8000/employee/login/`
   - Admin Panel: `http://localhost:8000/admin/`

## Email Templates

### Verification Email Template
- Professional HTML design
- Company branding
- Clear call-to-action button
- Account details included
- Expiration warning

### Test Email Template
- Simple HTML format
- Timestamp included
- Delivery confirmation

## Security Considerations

1. **Email Verification**: Required before login
2. **Token Security**: Unique tokens with expiration
3. **CSRF Protection**: All forms protected
4. **Input Validation**: Server-side validation
5. **Authentication**: Django's built-in auth system

## Future Enhancements

1. **Two-Factor Authentication**: SMS/App-based 2FA
2. **Advanced Reporting**: Data analytics and reports
3. **Mobile App**: Native mobile application
4. **API Integration**: REST API for external systems
5. **Document Management**: File upload and sharing
6. **Calendar Integration**: Event scheduling
7. **Notification System**: Real-time notifications

## Support

For technical support or questions about the employee portal:
- **Email**: support@computerconcepts.com
- **Phone**: (555) 123-4567
- **Hours**: Monday-Friday 8AM-6PM

---
*Computer Concepts Employee Portal - Empowering your workforce with efficient tools and secure access.*
