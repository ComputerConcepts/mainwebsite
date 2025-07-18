from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import ContactForm, Events, Invoice, Ticket, Employee, Career, JobPosting
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.db import IntegrityError
import uuid
import secrets
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password, check_password
import barcode
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from barcode.writer import ImageWriter
from io import BytesIO
from django.conf import settings
import datetime
from .forms import EventImageForm, JobPostingForm, EmployeeProfileForm
import random
from django.core.mail import send_mail
import stripe
from django.utils import timezone
from django.contrib import messages
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
import secrets
from django.db import transaction
from django.contrib.auth.decorators import user_passes_test

stripe.api_key = settings.STRIPE_SECRET_KEY
    
def verifyTicketSuccess(request, invoice_id, ticket_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if invoice.tickets.filter(id=ticket_id).exists():
        return render(request, 'portal/ticket_success.html', {'invoice': invoice, 'ticket_id': ticket_id})
    else:
        return redirect('verifyTicketFailure', invoice_id=invoice_id, ticket_id=ticket_id)

def verifyTicketFailure(request, invoice_id, ticket_id):
    return render(request, 'ticket_failure.html', {'invoice_id': invoice_id, 'ticket_id': ticket_id})

def generate_otp():
    return str(random.randint(100000, 999999))



def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('adminEvents')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def send_otp(email):
    otp = generate_otp()
    subject = 'Your Verification code'
    message = f'Your Verification code is: {otp}'
    send_mail(subject, message, 'your_email@example.com', [email])
    return otp

def buy_tickets(request, event_id):
    event = Events.objects.get(id=event_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        number_of_tickets = int(request.POST.get('tickets'))
        otp = send_otp(email)
        request.session['otp'] = otp
        request.session['email'] = email
        request.session['first_name'] = first_name
        request.session['last_name'] = last_name
        request.session['event_id'] = str(event.id)
        request.session['number_of_tickets'] = number_of_tickets
        request.session['otp_timestamp'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        return redirect('verify_email')
    return render(request, 'buy_tickets.html', {'event': event})

def verify_email(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_expiry_time_str = request.session.get('otp_expiry_time')
        otp_expiry_time = None
        if otp_expiry_time_str:
            try:
                otp_expiry_time = timezone.datetime.fromisoformat(otp_expiry_time_str)
            except ValueError:
                otp_expiry_time = None
        if otp_expiry_time and timezone.now() > otp_expiry_time:
            messages.error(request, 'The OTP has expired.')
            return redirect('verify_email')
        if entered_otp == stored_otp:
            email = request.session.get('email')
            last_name = request.session.get('last_name')
            first_name = request.session.get('first_name')
            event_id = request.session.get('event_id')
            number_of_tickets = request.session.get('number_of_tickets')
            event = Events.objects.get(id=event_id)
            tickets = []
            cost = 0
            for _ in range(number_of_tickets):
                ticket = Ticket(event=event, purchaseDate=timezone.now(), email=email)
                ticket.save()
                tickets.append(ticket)
                cost+=event.cost
            invoice = Invoice(email=email, first_name = first_name, last_name = last_name, verified=True, cost = cost)
            invoice.save()
            invoice.tickets.set(tickets)
            invoice.save()
            request.session.pop('otp', None)
            request.session.pop('otp_expiry_time', None)
            request.session.pop('email', None)
            request.session.pop('event_id', None)
            request.session.pop('number_of_tickets', None)
            return redirect('payment_page', invoice.id)
        else:
            messages.error(request, 'Invalid OTP.')
            return redirect('verify_email')
    return render(request, 'verify_email.html')

def show_tickets(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = send_otp(email)
        request.session['otp'] = otp
        request.session['email'] = email
        request.session['otp_timestamp'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        return redirect('verify_tickets')    
    return render(request, 'show_tickets.html')

def verify_tickets(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_expiry_time_str = request.session.get('otp_expiry_time')
        otp_expiry_time = None
        if otp_expiry_time_str:
            try:
                otp_expiry_time = timezone.datetime.fromisoformat(otp_expiry_time_str)
            except ValueError:
                otp_expiry_time = None
        if otp_expiry_time and timezone.now() > otp_expiry_time:
            messages.error(request, 'The OTP has expired.')
            return redirect('verify_email')
        if entered_otp == stored_otp:
            email = request.session.get('email')
            invoice = Invoice.objects.filter(email=email, verified=True).order_by('-date').first()
            if not invoice:
                messages.error(request, 'No valid invoice found.')
                return redirect('verify_email')
            tickets = Ticket.objects.filter(invoice=invoice)
            barcodes = {}
            for ticket in tickets:
                barcode_data = str(ticket.id)
                barcode_obj = barcode.Code128(barcode_data, writer=ImageWriter())
                buffer = BytesIO()
                barcode_obj.write(buffer)
                barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                barcodes[ticket.id] = barcode_base64
            request.session.pop('otp', None)
            request.session.pop('otp_expiry_time', None)
            request.session.pop('email', None)
            context = {
                'invoice': invoice,
                'tickets': tickets,
                'barcodes': barcodes,
            }
            return render(request, 'ticketsDisplay.html', context)
        else:
            messages.error(request, 'Invalid OTP.')
            return redirect('verify_email')
    return render(request, 'verify_email.html')

def payment_page(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    total_amount = invoice.cost * 100  # Example: each ticket costs $10.00 (1000 cents)
    if request.method == 'POST':
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount,
                currency='usd',
                description=f'Payment for invoice {invoice_id}',
                metadata={'invoice_id': str(invoice_id)},
            )
            client_secret = payment_intent['client_secret']
            return render(request, 'payment_page.html', {
                'invoice': invoice,
                'total_amount': total_amount / 100,
                'stripe_publishable_key': 'pk_test_51MsYaVIj9JFN5Py8ttbhr1SvNPFQxIJs31AjnD7QJmbc0FbAahnkSjlvIENI4BSZJ4JRNBoBYdg0FeaGHeBN5ugG00NQfe7HzC',
                'client_secret': client_secret
            })
        except stripe.error.StripeError as e:
            return render(request, 'payment_error.html', {'error': str(e)})
    payment_intent = stripe.PaymentIntent.create(
        amount=total_amount,
        currency='usd',
        description=f'Payment for invoice {invoice_id}',
        metadata={'invoice_id': str(invoice_id)},
    )
    client_secret = payment_intent['client_secret']
    return render(request, 'payment_page.html', {
        'invoice': invoice,
        'total_amount': total_amount / 100,
        'stripe_publishable_key': 'pk_test_51MsYaVIj9JFN5Py8ttbhr1SvNPFQxIJs31AjnD7QJmbc0FbAahnkSjlvIENI4BSZJ4JRNBoBYdg0FeaGHeBN5ugG00NQfe7HzC',
        'client_secret': client_secret
    })

def payment_success(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    if invoice.verified:
        # Retrieve invoice items
        tickets = invoice.tickets.all()
        invoice_items = [
            {
                'name': ticket.event.title,
                'description': ticket.event.description,
                'quantity': 1,  # Assuming each ticket represents 1 quantity
                'unit_price': ticket.event.cost,
                'total': ticket.event.cost
            }
            for ticket in tickets
        ]
        total_amount = sum(item['total'] for item in invoice_items)

        # Render the email template with invoice details
        subject = 'Your Payment was Successful'
        message = render_to_string('invoice_email.html', {
            'customer_name': invoice.email,  # Assuming email is the customer's name
            'invoice_items': invoice_items,
            'total_amount': total_amount,
        })

        # Send email using Django's send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Replace with your email address
            [invoice.email],  # Replace with recipient's email address
            fail_silently=False,
            html_message=message,  # Include HTML content
        )

        # Redirect to a success page
        return render(request, 'payment_success.html', {'invoice': invoice})

def index(request):
    return render(request, 'index.html')

@require_POST
@login_required
def adminEventsCreate(request):
    title = request.POST.get("eventName")
    description = request.POST.get("eventDescription")
    cost = int(request.POST.get("ticketCost"))
    date_str = request.POST.get("eventDate")
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    Events.objects.create(title = title, description = description, cost = cost, eventdate = date)
    return redirect("adminEvents")

def reset(request, uidb64, token):
    """Password reset and profile completion for new/existing users"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        # Check if this is a new user or existing user
        try:
            employee = Employee.objects.get(user=user)
            is_new_user = not employee.department  # If department is empty, treat as new user
        except Employee.DoesNotExist:
            # Create a new employee record if none exists
            employee = Employee.objects.create(
                user=user,
                employee_id=f"EMP{str(uuid.uuid4())[:8]}",
                department="",
                position="",
                phone="",
                is_email_verified=False,
                email_verification_token=secrets.token_urlsafe(32)
            )
            is_new_user = True
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        employee = None
        is_new_user = False
        
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST['new-password']
            password2 = request.POST['confirm-password']
            
            # Always collect these details
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            # For new users, collect these additional details
            if is_new_user:
                department = request.POST.get('department', '')
                position = request.POST.get('position', '')
                phone = request.POST.get('phone', '')
            
            if password1 == password2:
                user.set_password(password1)
                
                # If this is a new user setup, update profile details
                if is_new_user:
                    user.first_name = first_name
                    user.last_name = last_name
                    employee.department = department
                    employee.position = position
                    employee.phone = phone
                    
                    # Set email as verified since they accessed via email
                    employee.is_email_verified = True
                    employee.save()
                
                user.save()
                messages.success(request, 'Your account has been set up successfully. Please login with your new password.')
                return redirect('employee_login')
        return render(request, 'portal/resetPassword.html', {'is_new_user': is_new_user})
    else:
        return redirect("forgotPassword")

def forgotPassword(request):
    """Password reset request - also serves as entry point for new users"""
    if request.method == 'POST':
        email = request.POST['email']
        
        # Check if email belongs to company domain
        if not email.endswith('@onecomputerconcepts.com'):
            messages.error(request, 'Only @onecomputerconcepts.com email addresses are allowed.')
            return render(request, 'portal/forgotPassword.html')
            
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            is_new_user = False
        else:
            # For new users - create a basic user account
            base_username = email.split('@')[0]  # Use part before @ as base username
            username = base_username
            counter = 1
            
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            random_password = secrets.token_urlsafe(16)  # Generate random temporary password
            
            try:
                # Create the user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=random_password
                )
                
                # Create empty employee profile
                employee = Employee.objects.create(
                    user=user,
                    employee_id=f"EMP{str(uuid.uuid4())[:8]}",  # Generate temporary employee ID
                    department="",
                    position="",
                    phone="",
                    is_email_verified=False,
                    email_verification_token=secrets.token_urlsafe(32)
                )
                is_new_user = True
                
            except IntegrityError:
                # If there's still an integrity error, it might be due to email uniqueness
                messages.error(request, 'An account with this email may already exist. Please contact IT support.')
                return render(request, 'portal/forgotPassword.html')
            
        # Send password reset email
        current_site = get_current_site(request)
        subject = 'Set Up Your Computer Concepts Account'
        message = render_to_string('email/PasswordReset.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
            'is_new_user': is_new_user
        })
        send_mail(subject, '', 'noreplycomputerconcepts@gmail.com', [email], html_message=message)
        
        messages.success(request, f'We\'ve sent a password reset link to {email}. Please check your inbox.')
        return redirect('employee_login')
            
    return render(request, 'portal/forgotPassword.html')

@login_required
def adminEvents(request):
    form = EventImageForm()
    events = Events.objects.all()
    return render(request, "portal/events.html", {"events":events, "form":form})

def invoices(request, event_id):
    invoices = Invoice.objects.filter(tickets__event_id=event_id).distinct()
    return render(request, "portal/invoices.html", {"invoices":invoices})

def about(request):
    return render(request, 'about.html')

def email(request):
    return render(request, 'emailEnter.html')

def events(request):
    events = Events.objects.all()
    return render(request, 'events.html', {"events":events})

def sitemap(request):
    return HttpResponse(open('templates/sitemap.xml').read(), content_type='text/xml')

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        ContactForm.objects.create(name = name, email = email, message = message)
    return render(request, 'contact.html')

@require_POST
def add_image(request, event_id):
    event = Events.objects.get(id=event_id)
    if request.method == 'POST':
        form = EventImageForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('adminEvents')
    else:
        form = EventImageForm(instance=event)
    return render(request, 'your_template_name.html', {'form': form, 'event': event})

@require_POST
def change_event(request, event_id):
    event = Events.objects.get(id=event_id)
    if event:
        event.status = False
        event.save()
    else:
        event.status = True
        event.save()
    return redirect('adminEvents')

# Employee Portal Views
def employee_login(request):
    """Employee login view with domain restriction (@onecomputerconcepts.com only)"""
    if request.method == 'POST':
        email = request.POST.get('email')  # Changed from username to email login
        password = request.POST.get('password')
        
        # Check if email belongs to company domain
        if not email.endswith('@onecomputerconcepts.com'):
            messages.error(request, 'Only @onecomputerconcepts.com email addresses are allowed.')
            return render(request, 'employee/login.html')
        
        # Try to get the user by email
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                try:
                    employee = Employee.objects.get(user=user)
                    if not employee.is_active:
                        messages.error(request, 'Your account is deactivated. Please contact HR.')
                        return render(request, 'employee/login.html')
                    
                    if not employee.is_email_verified:
                        messages.warning(request, 'Please verify your email before logging in.')
                        return redirect('employee_verify_email', employee_id=employee.id)
                    
                    auth_login(request, user)
                    messages.success(request, f'Welcome, {user.first_name}!')
                    return redirect('employee_dashboard')
                except Employee.DoesNotExist:
                    messages.error(request, 'Employee profile not found. Please contact HR.')
            else:
                messages.error(request, 'Invalid email or password.')
                
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email. Please use the "Forgot Password" option to set up your account.')
            return redirect('forgotPassword')
    
    return render(request, 'employee/login.html')

def employee_logout(request):
    """Employee logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('employee_login')

# employee_register function removed - using password reset flow for new user onboarding

def send_employee_verification_email(employee, request):
    """Send email verification to employee"""
    current_site = get_current_site(request)
    subject = 'Verify Your Computer Concepts Employee Account'
    message = render_to_string('employee/email_verification.html', {
        'employee': employee,
        'domain': current_site.domain,
        'protocol': 'https' if request.is_secure() else 'http',
        'token': employee.email_verification_token,
    })
    
    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [employee.user.email],
        html_message=message,
        fail_silently=False,
    )

def employee_verify_email(request, employee_id):
    """Employee email verification view"""
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee not found.')
        return redirect('employee_login')
    
    if request.method == 'POST':
        if 'resend' in request.POST:
            # Resend verification email
            send_employee_verification_email(employee, request)
            messages.success(request, 'Verification email sent again.')
    
    return render(request, 'employee/verify_email.html', {'employee': employee})

def employee_email_confirm(request, employee_id, token):
    """Confirm email verification"""
    try:
        employee = Employee.objects.get(id=employee_id, email_verification_token=token)
        employee.is_email_verified = True
        employee.email_verification_token = None
        employee.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('employee_login')
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('employee_login')

@login_required
def employee_dashboard(request):
    """Employee dashboard view"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Get project board statistics
        from .models import Board, Card
        created_boards = Board.objects.filter(created_by=employee, is_archived=False)
        member_boards = Board.objects.filter(members=employee, is_archived=False).exclude(created_by=employee)
        total_boards = created_boards.count() + member_boards.count()
        
        # Get recent cards assigned to user
        assigned_cards = Card.objects.filter(assigned_to=employee, is_completed=False)[:5]
        
        # HR statistics (if user is HR)
        context = {
            'employee': employee,
            'events': Events.objects.filter(status=True)[:5],  # Show recent active events
            'total_events': Events.objects.filter(status=True).count(),
            'total_boards': total_boards,
            'created_boards_count': created_boards.count(),
            'member_boards_count': member_boards.count(),
            'assigned_cards': assigned_cards,
            'assigned_cards_count': assigned_cards.count(),
        }
        
        # Add HR-specific statistics if user is HR
        if is_hr_or_admin(request.user):
            from .models import Career, JobPosting
            recent_applications = Career.objects.order_by('-submitted_at')[:5]
            recent_jobs = JobPosting.objects.filter(is_active=True).order_by('-created_at')[:5]
            
            context.update({
                'total_applications': Career.objects.count(),
                'pending_applications': Career.objects.filter(status='submitted').count(),
                'active_jobs': JobPosting.objects.filter(is_active=True).count(),
                'inactive_jobs': JobPosting.objects.filter(is_active=False).count(),
                'recent_applications': recent_applications,
                'recent_jobs': recent_jobs,
                'is_hr': True,
            })
        
        # Add admin-specific statistics if user is admin
        if employee.is_admin() or employee.is_super_admin():
            total_users = User.objects.count()
            active_users = Employee.objects.filter(is_active=True).count()
            pending_users = Employee.objects.filter(is_email_verified=False).count()
            departments = Employee.objects.values('department').distinct().count()
            
            # Get recent users (last 5 users created)
            recent_users = User.objects.select_related('employee').filter(
                employee__isnull=False
            ).order_by('-date_joined')[:5]
            
            context.update({
                'total_users': total_users,
                'active_users': active_users,
                'pending_users': pending_users,
                'total_departments': departments,
                'recent_users': recent_users,
            })
        
        return render(request, 'employee/dashboard.html', context)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')

@login_required
def employee_profile(request):
    """Employee profile view with restricted editing"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        if request.method == 'POST':
            form = EmployeeProfileForm(request.POST, instance=employee, user=request.user)
            if form.is_valid():
                # Store user reference for save method
                form.user = request.user
                form.save()
                
                # If not superuser, manually update allowed fields only
                if not request.user.is_superuser:
                    # Update only non-restricted User fields
                    user = request.user
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    # Do NOT update email, department, or position for non-superusers
                    user.save()
                
                messages.success(request, 'Profile updated successfully.')
                return redirect('employee_profile')
        else:
            form = EmployeeProfileForm(instance=employee, user=request.user)
        
        return render(request, 'employee/profile.html', {'employee': employee, 'form': form})
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')

@login_required
def employee_events(request):
    """Employee events view"""
    try:
        employee = Employee.objects.get(user=request.user)
        events = Events.objects.all().order_by('-eventdate')
        return render(request, 'employee/events.html', {
            'employee': employee,
            'events': events
        })
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')

@login_required
def employee_event_detail(request, event_id):
    """Employee event detail view"""
    try:
        employee = Employee.objects.get(user=request.user)
        event = get_object_or_404(Events, id=event_id)
        tickets = Ticket.objects.filter(event=event)
        invoices = Invoice.objects.filter(tickets__event=event).distinct()
        
        context = {
            'employee': employee,
            'event': event,
            'tickets': tickets,
            'invoices': invoices,
            'total_tickets': tickets.count(),
            'total_revenue': sum(invoice.cost for invoice in invoices)
        }
        return render(request, 'employee/event_detail.html', context)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')

def test_email(request):
    """Test email functionality"""
    if request.method == 'POST':
        email = request.POST.get('email', 'test@example.com')
        try:
            subject = 'Test Email from Computer Concepts'
            message = '''
            <h2>Test Email</h2>
            <p>This is a test email from the Computer Concepts Employee Portal.</p>
            <p>If you received this email, the email configuration is working correctly.</p>
            <p>Time sent: {}'''.format(timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=message,
                fail_silently=False,
            )
            
            messages.success(request, f'Test email sent successfully to {email}')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')
    
    return render(request, 'employee/test_email.html')

def employee_help(request):
    """Employee help page"""
    try:
        employee = Employee.objects.get(user=request.user)
        return render(request, 'employee/help.html', {'employee': employee})
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')

def careers(request):
    """Public careers page"""
    # Check if user is an employee - if so, show them a different message
    is_employee = False
    if request.user.is_authenticated:
        try:
            employee = Employee.objects.get(user=request.user)
            is_employee = True
        except Employee.DoesNotExist:
            pass
    
    # Get active job postings
    active_jobs = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    
    if request.method == 'POST':
        # Prevent employees from applying
        if is_employee:
            messages.error(request, 'Company employees cannot apply to job postings through the public portal. Please contact HR directly for internal opportunities.')
            return redirect('careers')
        
        # Handle career application submission
        try:
            job_posting_id = request.POST.get('job_posting_id')
            job_posting = get_object_or_404(JobPosting, id=job_posting_id, is_active=True)
            
            career = Career.objects.create(
                job_posting=job_posting,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                experience_years=int(request.POST.get('experience_years', 0)),
                education=request.POST.get('education'),
                skills=request.POST.get('skills'),
                cover_letter=request.POST.get('cover_letter'),
                resume=request.FILES.get('resume'),
                linkedin_profile=request.POST.get('linkedin_profile'),
                portfolio_website=request.POST.get('portfolio_website'),
                available_start_date=request.POST.get('available_start_date'),
                salary_expectation=request.POST.get('salary_expectation') or None,
            )
            
            # Send confirmation email to applicant
            try:
                applicant_subject = 'Application Received - Computer Concepts'
                applicant_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #00c2cb, #1a2533); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 2rem;">Computer Concepts</h1>
                        <p style="margin: 10px 0 0 0; font-size: 1.1rem;">Application Received</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #1a2533; margin-top: 0;">Dear {career.first_name},</h2>
                        
                        <p>Thank you for your interest in joining Computer Concepts! We have successfully received your application for the position of <strong>{career.position_applied}</strong>.</p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #1a2533;">Application Details:</h3>
                            <p><strong>Position:</strong> {career.position_applied}</p>
                            <p><strong>Application ID:</strong> {career.id}</p>
                            <p><strong>Submitted:</strong> {career.submitted_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                            <p><strong>Status:</strong> Under Review</p>
                        </div>
                        
                        <p>Our HR team will review your application and contact you within 1-2 weeks if your qualifications match our requirements.</p>
                        
                        <p>In the meantime, feel free to explore our website to learn more about our company culture and current projects.</p>
                        
                        <p>Best regards,<br>
                        <strong>Computer Concepts HR Team</strong></p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 20px; color: #666; font-size: 0.9rem;">
                        <p>Computer Concepts - Innovative IT Solutions</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
                '''
                
                send_mail(
                    applicant_subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [career.email],
                    html_message=applicant_message,
                    fail_silently=False,
                )
            except Exception as e:
                pass  # Don't fail if confirmation email fails
            
            # Send notification email to HR
            try:
                hr_subject = f'New Career Application - {career.position_applied}'
                hr_message = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 2rem;">New Application Alert</h1>
                        <p style="margin: 10px 0 0 0;">Computer Concepts HR Portal</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #1a2533; margin-top: 0;">New Career Application Received</h2>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #1a2533;">Applicant Information:</h3>
                            <p><strong>Name:</strong> {career.first_name} {career.last_name}</p>
                            <p><strong>Email:</strong> {career.email}</p>
                            <p><strong>Phone:</strong> {career.phone}</p>
                            <p><strong>Position:</strong> {career.position_applied}</p>
                            <p><strong>Experience:</strong> {career.experience_years} years</p>
                            <p><strong>Education:</strong> {career.education}</p>
                            <p><strong>Available Start:</strong> {career.available_start_date}</p>
                            <p><strong>Submitted:</strong> {career.submitted_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        </div>
                        
                        <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h4 style="margin-top: 0; color: #1a2533;">Skills:</h4>
                            <p>{career.skills}</p>
                        </div>
                        
                        <p><strong>Cover Letter:</strong></p>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <p>{career.cover_letter}</p>
                        </div>
                        
                        <p style="margin-top: 30px;">Please review this application in the employee portal.</p>
                        
                        <div style="text-align: center; margin-top: 20px;">
                            <p style="color: #666; font-size: 0.9rem;">Application ID: {career.id}</p>
                        </div>
                    </div>
                </div>
                '''
                
                send_mail(
                    hr_subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],  # Send to HR email
                    html_message=hr_message,
                    fail_silently=True,
                )
            except Exception as e:
                pass  # Don't fail if notification email fails
            
            messages.success(request, 'Thank you for your application! We have received your submission and sent a confirmation email. Our HR team will review your application and get back to you soon.')
            return redirect('careers')
            
        except Exception as e:
            messages.error(request, 'There was an error submitting your application. Please try again.')
    
    return render(request, 'careers.html', {
        'active_jobs': active_jobs,
        'is_employee': is_employee
    })

def is_admin_user(user):
    """Check if user is admin (superuser or staff)"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

def is_hr_or_admin(user):
    """Check if user is HR or admin"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser or user.is_staff:
        return True
    
    try:
        employee = Employee.objects.get(user=user)
        return employee.department.lower() == 'hr' or employee.position.lower() in ['hr manager', 'hr specialist', 'human resources']
    except Employee.DoesNotExist:
        return False

def is_employee_authenticated(request):
    """Check if user is authenticated and has an employee profile"""
    if not request.user.is_authenticated:
        return False
    
    try:
        employee = Employee.objects.get(user=request.user)
        return employee.is_active and employee.is_email_verified
    except Employee.DoesNotExist:
        return False

@user_passes_test(is_hr_or_admin)
def admin_careers(request):
    """Admin/HR view for career applications"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    position_filter = request.GET.get('position', '')
    
    # Build query
    applications = Career.objects.all()
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if position_filter:
        applications = applications.filter(position_applied__icontains=position_filter)
    
    # Get statistics
    total_applications = Career.objects.count()
    pending_applications = Career.objects.filter(status='submitted').count()
    under_review = Career.objects.filter(status='reviewing').count()
    hired = Career.objects.filter(status='hired').count()
    
    context = {
        'employee': employee,
        'applications': applications,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'under_review': under_review,
        'hired': hired,
        'status_filter': status_filter,
        'position_filter': position_filter,
        'status_choices': Career._meta.get_field('status').choices,
    }
    
    return render(request, 'employee/careers.html', context)

@user_passes_test(is_hr_or_admin)
def admin_career_detail(request, career_id):
    """Admin/HR view for individual career application"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_login')
    
    career = get_object_or_404(Career, id=career_id)
    
    if request.method == 'POST':
        # Update application status and notes
        career.status = request.POST.get('status')
        career.notes = request.POST.get('notes')
        career.reviewed_by = request.user
        career.save()
        
        messages.success(request, 'Application updated successfully.')
        return redirect('admin_career_detail', career_id=career.id)
    
    context = {
        'employee': employee,
        'career': career,
        'status_choices': Career._meta.get_field('status').choices,
    }
    
    return render(request, 'employee/career_detail.html', context)

@login_required
def admin_jobs(request):
    """Employee portal - job postings management"""
    employee = get_object_or_404(Employee, user=request.user)
    
    if not is_hr_or_admin(request.user):
        messages.error(request, 'Access denied. Only HR and admin users can manage job postings.')
        return redirect('employee_dashboard')
    
    jobs = JobPosting.objects.all().order_by('-created_at')
    
    context = {
        'employee': employee,
        'jobs': jobs,
    }
    
    return render(request, 'employee/jobs.html', context)

@login_required
def admin_job_create(request):
    """Employee portal - create new job posting"""
    employee = get_object_or_404(Employee, user=request.user)
    
    if not is_hr_or_admin(request.user):
        messages.error(request, 'Access denied. Only HR and admin users can create job postings.')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            
            messages.success(request, f'Job posting "{job.title}" created successfully!')
            return redirect('admin_jobs')
    else:
        form = JobPostingForm()
    
    context = {
        'employee': employee,
        'form': form,
    }
    
    return render(request, 'employee/job_form.html', context)

@login_required
def admin_job_detail(request, job_id):
    """Employee portal - job posting detail"""
    employee = get_object_or_404(Employee, user=request.user)
    job = get_object_or_404(JobPosting, id=job_id)
    
    if not is_hr_or_admin(request.user):
        messages.error(request, 'Access denied. Only HR and admin users can view job details.')
        return redirect('employee_dashboard')
    
    applications = job.applications.all().order_by('-submitted_at')
    
    context = {
        'employee': employee,
        'job': job,
        'applications': applications,
    }
    
    return render(request, 'employee/job_detail.html', context)

@login_required
def admin_job_edit(request, job_id):
    """Employee portal - edit job posting"""
    employee = get_object_or_404(Employee, user=request.user)
    job = get_object_or_404(JobPosting, id=job_id)
    
    if not is_hr_or_admin(request.user):
        messages.error(request, 'Access denied. Only HR and admin users can edit job postings.')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f'Job posting "{job.title}" updated successfully!')
            return redirect('admin_job_detail', job_id=job.id)
    else:
        form = JobPostingForm(instance=job)
    
    context = {
        'employee': employee,
        'form': form,
        'job': job,
    }
    
    return render(request, 'employee/job_form.html', context)

@login_required
def admin_job_delete(request, job_id):
    """Employee portal - delete job posting"""
    employee = get_object_or_404(Employee, user=request.user)
    job = get_object_or_404(JobPosting, id=job_id)
    
    if not is_hr_or_admin(request.user):
        messages.error(request, 'Access denied. Only HR and admin users can delete job postings.')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        job_title = job.title
        job.delete()
        messages.success(request, f'Job posting "{job_title}" has been deleted successfully.')
        return redirect('admin_jobs')
    
    context = {
        'employee': employee,
        'job': job,
    }
    
    return render(request, 'employee/job_confirm_delete.html', context)

def career_apply(request, job_id):
    """Application form for specific job posting"""
    job = get_object_or_404(JobPosting, id=job_id, is_active=True)
    
    # Check if user is an employee - if so, redirect them away
    if request.user.is_authenticated:
        try:
            employee = Employee.objects.get(user=request.user)
            messages.error(request, 'Company employees cannot apply to job postings through the public portal. Please contact HR directly for internal opportunities.')
            return redirect('careers')
        except Employee.DoesNotExist:
            # User is not an employee, can proceed with application
            pass
    
    if request.method == 'POST':
        try:
            career = Career.objects.create(
                job_posting=job,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                experience_years=int(request.POST.get('experience_years', 0)),
                education=request.POST.get('education'),
                skills=request.POST.get('skills'),
                cover_letter=request.POST.get('cover_letter'),
                resume=request.FILES.get('resume'),
                linkedin_profile=request.POST.get('linkedin_profile'),
                portfolio_website=request.POST.get('portfolio_website'),
                available_start_date=request.POST.get('available_start_date'),
                salary_expectation=request.POST.get('salary_expectation') or None,
            )
            
            # AI analysis will be handled by the hourly script
            
            # Same email logic as careers view
            messages.success(request, f'Thank you for applying to {job.title}! We have received your application and sent a confirmation email.')
            return redirect('career_apply', job_id=job.id)
            
        except Exception as e:
            messages.error(request, 'There was an error submitting your application. Please try again.')
    
    return render(request, 'career_apply.html', {'job': job})@login_required

def admin_application_update_status(request, application_id):

    """Employee portal - update application status"""

    if not is_hr_or_admin(request.user):

        messages.error(request, 'Access denied. Only HR and admin users can update application status.')

        return redirect('employee_dashboard')

    

    application = get_object_or_404(Career, id=application_id)

    status = request.GET.get('status')

    

    if status in ['new', 'reviewed', 'interviewing', 'hired', 'rejected']:

        application.status = status

        application.reviewed_by = request.user

        application.save()

        messages.success(request, f'Application status updated to {status.title()}.')

    else:

        messages.error(request, 'Invalid application status.')

    

    # Redirect back to referring page or job detail

    if request.META.get('HTTP_REFERER'):

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect('admin_job_detail', job_id=application.job_posting.id)



@login_required

def admin_application_detail(request, application_id):

    """Employee portal - view detailed application"""

    if not is_hr_or_admin(request.user):

        messages.error(request, 'Access denied. Only HR and admin users can view application details.')

        return redirect('employee_dashboard')

    

    application = get_object_or_404(Career, id=application_id)

    

    context = {

        'employee': get_object_or_404(Employee, user=request.user),

        'application': application,

    }

    

    return render(request, 'employee/application_detail.html', context)

