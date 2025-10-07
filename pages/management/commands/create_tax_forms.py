"""
Django management command to create predefined tax form templates
Based on the attached tax forms: Intake, Schedule C, Income Summary, etc.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import secrets
import string
from pages.models import TaxFormTemplate, TaxFormField


class Command(BaseCommand):
    help = 'Create predefined tax form templates'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user', 
            type=str, 
            help='Username of the user who will be marked as creator',
            default='admin'
        )
    
    def handle(self, *args, **options):
        username = options.get('user')

        user = None

        # If a username was provided, try to use it first
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(self.style.SUCCESS(f'Using provided user: {username}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Provided user "{username}" not found. Trying fallbacks...'))

        # If no user found yet, try to find any superuser
        if user is None:
            try:
                user = User.objects.filter(is_superuser=True).order_by('id').first()
                if user:
                    self.stdout.write(self.style.SUCCESS(f'Using superuser: {user.username}'))
            except Exception:
                user = None

        # If still no user, try any existing user
        if user is None:
            user = User.objects.order_by('id').first()
            if user:
                self.stdout.write(self.style.SUCCESS(f'No superuser found; using first available user: {user.username}'))

        # If no users exist at all, create a fallback admin user
        if user is None:
            # create a fallback admin user with a generated password
            pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            username = 'tax_admin'
            user = User.objects.create_superuser(username=username, email='', password=pwd)
            self.stdout.write(self.style.WARNING(f'No users found in database. Created fallback superuser "{username}" with generated password: {pwd}'))
        
        self.stdout.write('Creating predefined tax form templates...')
        
        # Create Tax Intake Form
        self.create_tax_intake_form(user)
        
        # Create Schedule C Form
        self.create_schedule_c_form(user)
        
        # Create Income Summary Form
        self.create_income_summary_form(user)
        
        # Create Dependent Care Form
        self.create_dependent_care_form(user)
        
        # Create Student Acknowledgment Form
        self.create_student_acknowledgment_form(user)
        
        # Create Photo ID and Voided Check Form
        self.create_photo_id_form(user)
        
        # Create Due Diligence Questionnaire
        self.create_due_diligence_form(user)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created all predefined tax form templates!')
        )
    
    def create_tax_intake_form(self, user):
        """Create Tax Intake Form based on attached document"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='intake',
            defaults={
                'name': 'Tax Intake Form',
                'description': 'Comprehensive tax information intake form for new and returning clients',
                'instructions': 'Please provide complete and accurate information for tax preparation. All fields marked with * are required.',
                'requires_signature': True,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Tax Intake Form already exists')
            return
            
        # Taxpayer Section
        fields_data = [
            # Taxpayer Information
            {'section': 'Taxpayer Information', 'type': 'section_header', 'name': 'taxpayer_header', 'label': 'Taxpayer Information'},
            {'section': 'Taxpayer Information', 'type': 'ssn', 'name': 'taxpayer_ssn', 'label': 'Social Security Number', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'name', 'name': 'taxpayer_first_name', 'label': 'First Name', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'text', 'name': 'taxpayer_mi', 'label': 'MI'},
            {'section': 'Taxpayer Information', 'type': 'name', 'name': 'taxpayer_last_name', 'label': 'Last Name', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'date', 'name': 'taxpayer_dob', 'label': 'Date of Birth', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'date', 'name': 'taxpayer_death_date', 'label': 'Date of Death (if applicable)'},
            {'section': 'Taxpayer Information', 'type': 'phone', 'name': 'taxpayer_work_phone', 'label': 'Work Phone'},
            {'section': 'Taxpayer Information', 'type': 'phone', 'name': 'taxpayer_cell_phone', 'label': 'Cell/Other Phone'},
            {'section': 'Taxpayer Information', 'type': 'text', 'name': 'taxpayer_occupation', 'label': 'Occupation'},
            {'section': 'Taxpayer Information', 'type': 'email', 'name': 'taxpayer_email', 'label': 'Email', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'yes_no', 'name': 'taxpayer_legally_blind', 'label': 'Legally Blind?'},
            {'section': 'Taxpayer Information', 'type': 'yes_no', 'name': 'taxpayer_dependent', 'label': 'Dependent of Other?'},
            
            # Spouse Information  
            {'section': 'Spouse Information', 'type': 'section_header', 'name': 'spouse_header', 'label': 'Spouse Information'},
            {'section': 'Spouse Information', 'type': 'ssn', 'name': 'spouse_ssn', 'label': 'Social Security Number'},
            {'section': 'Spouse Information', 'type': 'name', 'name': 'spouse_first_name', 'label': 'First Name'},
            {'section': 'Spouse Information', 'type': 'text', 'name': 'spouse_mi', 'label': 'MI'},
            {'section': 'Spouse Information', 'type': 'name', 'name': 'spouse_last_name', 'label': 'Last Name'},
            {'section': 'Spouse Information', 'type': 'date', 'name': 'spouse_dob', 'label': 'Date of Birth'},
            {'section': 'Spouse Information', 'type': 'date', 'name': 'spouse_death_date', 'label': 'Date of Death (if applicable)'},
            {'section': 'Spouse Information', 'type': 'phone', 'name': 'spouse_work_phone', 'label': 'Work Phone'},
            {'section': 'Spouse Information', 'type': 'phone', 'name': 'spouse_cell_phone', 'label': 'Cell/Other Phone'},
            {'section': 'Spouse Information', 'type': 'text', 'name': 'spouse_occupation', 'label': 'Occupation'},
            {'section': 'Spouse Information', 'type': 'email', 'name': 'spouse_email', 'label': 'Email'},
            {'section': 'Spouse Information', 'type': 'yes_no', 'name': 'spouse_legally_blind', 'label': 'Legally Blind?'},
            {'section': 'Spouse Information', 'type': 'yes_no', 'name': 'spouse_dependent', 'label': 'Dependent of Other?'},
            
            # Filing Status
            {'section': 'Filing Status', 'type': 'section_header', 'name': 'filing_header', 'label': 'Filing Status'},
            {'section': 'Filing Status', 'type': 'radio', 'name': 'filing_status', 'label': 'Filing Status', 'required': True, 
             'options': ['Single', 'Married Filing Joint', 'Married Filing Separately', 'Head of Household', 'Qualifying Widow(er)']},
            {'section': 'Filing Status', 'type': 'date', 'name': 'marriage_date', 'label': 'Marriage Date (if applicable)'},
            {'section': 'Filing Status', 'type': 'text', 'name': 'household_head', 'label': 'Head of Household'},
            {'section': 'Filing Status', 'type': 'yes_no', 'name': 'qualifying_widower', 'label': 'Qualifying Widower?'},
            
            # Address
            {'section': 'Address', 'type': 'section_header', 'name': 'address_header', 'label': 'Address Information'},
            {'section': 'Address', 'type': 'text', 'name': 'street_apt_no', 'label': 'Street & Apt. No.', 'required': True},
            {'section': 'Address', 'type': 'text', 'name': 'city', 'label': 'City', 'required': True},
            {'section': 'Address', 'type': 'text', 'name': 'state', 'label': 'State', 'required': True},
            {'section': 'Address', 'type': 'text', 'name': 'zip', 'label': 'Zip Code', 'required': True},
            {'section': 'Address', 'type': 'text', 'name': 'county', 'label': 'County'},
            
            # Dependents
            {'section': 'Dependents', 'type': 'section_header', 'name': 'dependents_header', 'label': 'Dependents Information'},
            {'section': 'Dependents', 'type': 'textarea', 'name': 'dependents_info', 'label': 'List all dependents (Name, DOB, SSN, Relationship)', 'help': 'Format: First, Middle Initial, Last Name | D.O.B | Social Security Number | Relationship'},
            
            # Affordable Care Act
            {'section': 'Affordable Care Act', 'type': 'section_header', 'name': 'aca_header', 'label': 'Affordable Care Act Information'},
            {'section': 'Affordable Care Act', 'type': 'yes_no', 'name': 'health_insurance_all_year', 'label': 'Did everyone on this tax return have health insurance all 12 months last year?', 'required': True},
            {'section': 'Affordable Care Act', 'type': 'textarea', 'name': 'insurance_details', 'label': 'If no, were you exempt and/or did you pay the shared responsibility fee? Please explain.'},
            
            # Signature
            {'section': 'Signature', 'type': 'section_header', 'name': 'signature_header', 'label': 'Electronic Signature'},
            {'section': 'Signature', 'type': 'signature', 'name': 'taxpayer_signature', 'label': 'Taxpayer Electronic Signature', 'required': True},
            {'section': 'Signature', 'type': 'date', 'name': 'signature_date', 'label': 'Date', 'required': True},
        ]
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Tax Intake Form with {len(fields_data)} fields')
    
    def create_schedule_c_form(self, user):
        """Create Schedule C Business Income Form"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='schedule_c',
            defaults={
                'name': 'Schedule C - Business Income and Expenses',
                'description': 'Report income and expenses from sole proprietorship or single-member LLC',
                'instructions': 'Complete this form if you operated a business or practiced a profession as a sole proprietor.',
                'requires_signature': True,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Schedule C Form already exists')
            return
        
        fields_data = [
            # Business Information
            {'section': 'Business Information', 'type': 'section_header', 'name': 'business_header', 'label': 'Business Information (Required for all)'},
            {'section': 'Business Information', 'type': 'text', 'name': 'taxpayer_name', 'label': 'Taxpayer Name', 'required': True},
            {'section': 'Business Information', 'type': 'text', 'name': 'business_name', 'label': 'Name of Business', 'required': True},
            {'section': 'Business Information', 'type': 'text', 'name': 'business_address', 'label': 'Address of Business', 'required': True},
            {'section': 'Business Information', 'type': 'text', 'name': 'business_ein', 'label': 'Business EIN (if any)'},
            {'section': 'Business Information', 'type': 'date', 'name': 'business_start_date', 'label': 'Date Business Started'},
            {'section': 'Business Information', 'type': 'yes_no', 'name': 'materially_participate', 'label': 'Did you materially participate in the business?', 'required': True},
            
            # Income Questions
            {'section': 'Income', 'type': 'section_header', 'name': 'income_header', 'label': 'Income Questions (Required if no P&L or Trial Balance Available)'},
            {'section': 'Income', 'type': 'currency', 'name': 'total_sales', 'label': 'Total Sales $'},
            {'section': 'Income', 'type': 'currency', 'name': 'other_income', 'label': 'Other Income $'},
            
            # General Expenses
            {'section': 'General Expenses', 'type': 'section_header', 'name': 'expenses_header', 'label': 'General Expenses (Required if no P&L or Trial Balance Available)'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'advertising', 'label': 'Advertising $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'auto_expense', 'label': 'Auto Expense $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'supplies', 'label': 'Supplies $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'contract_labor', 'label': 'Contract Labor $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'depletion', 'label': 'Depletion $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'employee_benefit_program', 'label': 'Employee Benefit Program $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'insurance', 'label': 'Insurance $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'interest_mortgage', 'label': 'Interest: Mortgage $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'interest_other', 'label': 'Interest: Other $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'legal_professional', 'label': 'Legal & Professional $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'office_expense', 'label': 'Office Expense $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'pension_sharing', 'label': 'Pension and Profit Sharing $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'rent_or_lease', 'label': 'Rent or Lease $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'repairs_maintenance', 'label': 'Repair & Maintenance $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'taxes_licenses', 'label': 'Taxes and Licenses $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'travel', 'label': 'Travel $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'meals_total', 'label': 'Meals (Total) $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'utilities', 'label': 'Utilities $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'other_expenses', 'label': 'Other Expenses $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'total_expenses', 'label': 'Total Expenses $'},
            {'section': 'General Expenses', 'type': 'currency', 'name': 'net_income', 'label': 'Total Income - Total Expenses = $ Net Income'},
            {'section': 'General Expenses', 'type': 'textarea', 'name': 'supporting_documents', 'label': 'Please attach any other supporting document(s) if available'},
            
            # Signature
            {'section': 'Signature', 'type': 'signature', 'name': 'client_signature', 'label': 'Client Signature', 'required': True},
            {'section': 'Signature', 'type': 'date', 'name': 'signature_date', 'label': 'Date', 'required': True},
        ]
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Schedule C Form with {len(fields_data)} fields')
    
    def create_income_summary_form(self, user):
        """Create Income Summary Form"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='income_summary',
            defaults={
                'name': 'Income Summary',
                'description': 'Monthly income breakdown for tax preparation',
                'instructions': 'Please provide your monthly income breakdown for accurate tax calculation.',
                'requires_signature': False,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Income Summary Form already exists')
            return
        
        fields_data = [
            {'section': 'Monthly Income', 'type': 'section_header', 'name': 'income_header', 'label': 'Monthly Income Summary'},
        ]
        
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        
        for month in months:
            fields_data.extend([
                {'section': 'Monthly Income', 'type': 'text', 'name': f'{month.lower()}_service', 'label': f'{month} - Service'},
                {'section': 'Monthly Income', 'type': 'currency', 'name': f'{month.lower()}_amount', 'label': f'{month} - $ Made'},
            ])
        
        fields_data.append({'section': 'Total', 'type': 'currency', 'name': 'total_income', 'label': 'TOTAL $'})
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Income Summary Form with {len(fields_data)} fields')
    
    def create_dependent_care_form(self, user):
        """Create Dependent Care Form"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='dependent_care',
            defaults={
                'name': 'Dependent Care Form',
                'description': 'Information about dependent care expenses for tax credits',
                'instructions': 'Complete this form if you paid for care of dependents so you could work or look for work.',
                'requires_signature': True,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Dependent Care Form already exists')
            return
        
        fields_data = [
            {'section': 'Taxpayer Information', 'type': 'ssn', 'name': 'taxpayer_ssn', 'label': 'Taxpayer SSN', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'name', 'name': 'taxpayer_name', 'label': 'Taxpayer Name', 'required': True},
            
            # Standard Dependents (4 slots)
            {'section': 'Standard Dependents', 'type': 'section_header', 'name': 'standard_header', 'label': 'STANDARD DEPENDENTS'},
        ]
        
        for i in range(1, 5):
            fields_data.extend([
                {'section': 'Standard Dependents', 'type': 'name', 'name': f'dependent_{i}_name', 'label': f'{i}. Name of child'},
                {'section': 'Standard Dependents', 'type': 'ssn', 'name': f'dependent_{i}_ssn', 'label': f'{i}. SSN'},
                {'section': 'Standard Dependents', 'type': 'text', 'name': f'dependent_{i}_daycare_name', 'label': f'{i}. Daycare or provider Name'},
                {'section': 'Standard Dependents', 'type': 'ein', 'name': f'dependent_{i}_fein', 'label': f'{i}. FEIN (or social of caregiver)'},
                {'section': 'Standard Dependents', 'type': 'currency', 'name': f'dependent_{i}_amount', 'label': f'{i}. Total amount paid $'},
            ])
        
        # Additional questions
        fields_data.extend([
            {'section': 'Additional Information', 'type': 'section_header', 'name': 'additional_header', 'label': 'NON-STANDARD DEPENDENTS (Grandchild, niece, nephew, stepchild, foster child, etc.)'},
            {'section': 'Additional Information', 'type': 'textarea', 'name': 'non_standard_dependents', 'label': 'List any non-standard dependents and care details'},
            {'section': 'Additional Information', 'type': 'yes_no', 'name': 'court_custody', 'label': 'Do you have Court documentation of custody?'},
            {'section': 'Additional Information', 'type': 'text', 'name': 'custody_location', 'label': 'Where do they live?'},
            {'section': 'Additional Information', 'type': 'yes_no', 'name': 'child_relationship', 'label': 'What is your relationship to child?'},
            {'section': 'Additional Information', 'type': 'yes_no', 'name': 'filing_return', 'label': 'Why are they not filing their return?'},
            {'section': 'Additional Information', 'type': 'yes_no', 'name': 'claim_dependent', 'label': 'Can anyone else claim this dependent?'},
            
            # Signature
            {'section': 'Signature', 'type': 'signature', 'name': 'client_signature', 'label': 'Client Signature', 'required': True},
            {'section': 'Signature', 'type': 'date', 'name': 'signature_date', 'label': 'Date', 'required': True},
        ])
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Dependent Care Form with {len(fields_data)} fields')
    
    def create_student_acknowledgment_form(self, user):
        """Create Student Acknowledgment Form"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='student_ack',
            defaults={
                'name': 'Student Acknowledgment Form',
                'description': 'Student status and educational expense acknowledgment',
                'instructions': 'Complete this form to acknowledge your student status and educational expenses.',
                'requires_signature': True,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Student Acknowledgment Form already exists')
            return
        
        fields_data = [
            {'section': 'Student Information', 'type': 'text', 'name': 'student_name', 'label': 'I, _____________, was a student during the 20__ school year', 'required': True},
            {'section': 'Student Information', 'type': 'text', 'name': 'school_name', 'label': 'and attended ________________________', 'required': True},
            {'section': 'Student Information', 'type': 'textarea', 'name': 'acknowledgment_text', 'label': 'Acknowledgment Statement', 'help': 'I certify that all of the information found on this form is true and to the best of my knowledge...'},
            
            {'section': 'Student Status', 'type': 'section_header', 'name': 'status_header', 'label': 'My scholar status:'},
            {'section': 'Student Status', 'type': 'radio', 'name': 'student_status', 'label': 'Student Status', 'required': True,
             'options': ['( ) Full Time Student', '( ) Part Time Student']},
            
            {'section': 'Form Status', 'type': 'radio', 'name': 'form_1098t_status', 'label': '1098-T Form Status', 'required': True,
             'options': ['( ) DID receive a 1098-T Form', '( ) DID NOT receive a 1098-T Form (Please visit 1098t.com to download your 1098t in order to claim the credit)']},
            
            {'section': 'Educational Expenses', 'type': 'section_header', 'name': 'expenses_header', 'label': 'Below are my total educational expenses:'},
            {'section': 'Educational Expenses', 'type': 'currency', 'name': 'books_cost', 'label': 'Books: $'},
            {'section': 'Educational Expenses', 'type': 'currency', 'name': 'supplies_on_campus', 'label': 'Supplies (On campus): $'},
            {'section': 'Educational Expenses', 'type': 'currency', 'name': 'supplies_off_campus', 'label': 'Supplies (Off campus): $'},
            {'section': 'Educational Expenses', 'type': 'currency', 'name': 'other_expenses', 'label': 'Other expenses: $'},
            {'section': 'Educational Expenses', 'type': 'currency', 'name': 'total_expenses', 'label': 'Total: $'},
            
            {'section': 'Acknowledgment', 'type': 'textarea', 'name': 'responsibility_statement', 'label': 'Responsibility Statement', 'help': 'By signing below I certify all information is true, valid, and to the best of my knowledge...'},
            
            {'section': 'Signature', 'type': 'name', 'name': 'printed_name', 'label': 'Name First/Last Name printed', 'required': True},
            {'section': 'Signature', 'type': 'signature', 'name': 'student_signature', 'label': 'Student Signature', 'required': True},
            {'section': 'Signature', 'type': 'date', 'name': 'signature_date', 'label': 'Date', 'required': True},
        ]
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Student Acknowledgment Form with {len(fields_data)} fields')
    
    def create_photo_id_form(self, user):
        """Create Photo ID and Voided Check Form"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='photo_id',
            defaults={
                'name': 'Tax Client Photo ID and Voided Check - Required!',
                'description': 'Upload required identification and banking documents for tax preparation',
                'instructions': 'Please upload clear, readable copies of your photo ID and voided check or bank documents.',
                'requires_signature': True,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Photo ID Form already exists')
            return
        
        fields_data = [
            # Taxpayer Information
            {'section': 'Taxpayer Information', 'type': 'name', 'name': 'taxpayer_name', 'label': 'Taxpayer Name', 'required': True},
            {'section': 'Taxpayer Information', 'type': 'ssn', 'name': 'taxpayer_ssn', 'label': 'Taxpayer SSN', 'required': True},
            
            # Taxpayer Documents
            {'section': 'Taxpayer Documents', 'type': 'section_header', 'name': 'taxpayer_docs_header', 'label': 'Taxpayer Required Documents'},
            {'section': 'Taxpayer Documents', 'type': 'file', 'name': 'taxpayer_photo_id', 'label': 'PHOTO ID #1 - Required', 'required': True},
            {'section': 'Taxpayer Documents', 'type': 'file', 'name': 'taxpayer_other_id', 'label': '1 Other Form of ID - Required', 'required': True},
            
            # Spouse Information
            {'section': 'Spouse Information', 'type': 'name', 'name': 'spouse_name', 'label': 'Spouse Name'},
            {'section': 'Spouse Information', 'type': 'ssn', 'name': 'spouse_ssn', 'label': 'Spouse SSN'},
            
            # Spouse Documents
            {'section': 'Spouse Documents', 'type': 'section_header', 'name': 'spouse_docs_header', 'label': 'Spouse Required Documents (if applicable)'},
            {'section': 'Spouse Documents', 'type': 'file', 'name': 'spouse_photo_id', 'label': 'PHOTO ID #1 - Required'},
            {'section': 'Spouse Documents', 'type': 'file', 'name': 'spouse_other_id', 'label': '1 Other Form of ID - Required'},
            
            # Banking Information
            {'section': 'Banking Information', 'type': 'section_header', 'name': 'banking_header', 'label': 'Banking Information'},
            {'section': 'Banking Information', 'type': 'file', 'name': 'voided_check', 'label': 'Place Voided Check Here (only if you selected Direct deposit on page - 2)', 'help': 'Required only if selecting direct deposit for refund'},
            
            # Authorization
            {'section': 'Authorization', 'type': 'textarea', 'name': 'authorization_text', 'label': 'Authorization Statement', 'help': 'I hereby authorize the use of this identification above to electronically file my federal tax return according to IRS publication 1345'},
            
            # Signatures
            {'section': 'Signatures', 'type': 'signature', 'name': 'taxpayer_signature', 'label': 'Taxpayer Signature', 'required': True},
            {'section': 'Signatures', 'type': 'date', 'name': 'taxpayer_date', 'label': 'Date', 'required': True},
            {'section': 'Signatures', 'type': 'signature', 'name': 'spouse_signature', 'label': 'Spouse Signature'},
            {'section': 'Signatures', 'type': 'date', 'name': 'spouse_date', 'label': 'Date'},
        ]
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Photo ID Form with {len(fields_data)} fields')
    
    def create_due_diligence_form(self, user):
        """Create Due Diligence Questionnaire"""
        form, created = TaxFormTemplate.objects.get_or_create(
            form_type='due_diligence',
            defaults={
                'name': 'Due Diligence Questionnaire',
                'description': 'Required due diligence questions for tax preparation compliance',
                'instructions': 'Please answer all questions completely and accurately for IRS compliance requirements.',
                'requires_signature': False,
                'created_by': user
            }
        )
        
        if not created:
            self.stdout.write(f'Due Diligence Form already exists')
            return
        
        fields_data = [
            {'section': 'Household Information', 'type': 'number', 'name': 'adults_in_home', 'label': 'How many people live with you? _____ Adults _____ Children', 'required': True},
            {'section': 'Household Information', 'type': 'number', 'name': 'children_in_home', 'label': 'Children'},
            
            {'section': 'Support Information', 'type': 'yes_no', 'name': 'anyone_help_support', 'label': 'Did anyone else help support you during the year? ____ Yes ____ No'},
            {'section': 'Support Information', 'type': 'text', 'name': 'who_helped', 'label': 'If yes, who?'},
            {'section': 'Support Information', 'type': 'currency', 'name': 'support_amount', 'label': 'How much? $'},
            
            {'section': 'Dependency Questions', 'type': 'yes_no', 'name': 'dependents_claimed_by_others', 'label': 'Are any of the Dependents being claimed NOT your Son or Daughter? ____ Yes ____ No'},
            {'section': 'Dependency Questions', 'type': 'textarea', 'name': 'dependency_proof', 'label': 'If Yes, Provide proof of financial responsibility or residency (i.e copy of lease, medical records, school records, food stamps or benefit statements)'},
            {'section': 'Dependency Questions', 'type': 'textarea', 'name': 'parent_explanation', 'label': 'If Yes, Why are parents not claiming the child? (Please explain and list the child\'s name(s) if more than one listed on the return)'},
            
            {'section': 'Other Income', 'type': 'yes_no', 'name': 'other_income_received', 'label': 'Did you have any other income during the year? (Child support, alimony) ____ Yes ____ No'},
            {'section': 'Other Income', 'type': 'textarea', 'name': 'other_income_details', 'label': 'If yes, Please specify'},
            
            {'section': 'Additional Comments', 'type': 'textarea', 'name': 'other_comments', 'label': 'Other comments:'},
        ]
        
        self.create_form_fields(form, fields_data)
        self.stdout.write(f'Created Due Diligence Form with {len(fields_data)} fields')
    
    def create_form_fields(self, form, fields_data):
        """Helper method to create form fields"""
        for i, field_data in enumerate(fields_data):
            TaxFormField.objects.create(
                tax_form=form,
                field_type=field_data['type'],
                field_name=field_data['name'],
                field_label=field_data['label'],
                section=field_data.get('section', ''),
                is_required=field_data.get('required', False),
                help_text=field_data.get('help', ''),
                field_options=field_data.get('options', []),
                order=i * 10
            )