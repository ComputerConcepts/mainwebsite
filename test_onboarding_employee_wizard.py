import os
import sys
import uuid
import django
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

# Configure Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import Employee, OnboardingForm, ProspectiveEmployee, OnboardingInvitation  # noqa: E402


class OnboardingEmployeeWizardTests(TestCase):
    """Smoke tests for the create employee wizard flow"""

    @classmethod
    def setUpTestData(cls):
        cls.hr_user = User.objects.create_user(
            username='wizard_hr',
            password='testpass123',
            first_name='Wizard',
            last_name='HR',
            email='wizard.hr@example.com',
        )
        Employee.objects.create(
            user=cls.hr_user,
            employee_id=f'EMP-{uuid.uuid4().hex[:6]}',
            department='HR',
            position='HR Manager',
            role='admin',
            phone='555-0101',
            address='1 Wizard Way',
            emergency_contact='Wizard Contact',
            emergency_phone='555-0102',
        )
        cls.form_one = OnboardingForm.objects.create(
            title='Employee Packet',
            description='Core onboarding documents.',
            created_by=cls.hr_user,
            pin_expiry_hours=48,
            allow_multiple_submissions=False,
            send_confirmation_email=True,
        )
        cls.form_two = OnboardingForm.objects.create(
            title='IT Setup Checklist',
            description='Gather access requirements for IT.',
            created_by=cls.hr_user,
            pin_expiry_hours=48,
            allow_multiple_submissions=False,
            send_confirmation_email=True,
        )

    def setUp(self):
        self.client.force_login(self.hr_user)

    def test_wizard_creates_prospect_and_invitations(self):
        payload = {
            'first_name': 'Taylor',
            'last_name': 'Morgan',
            'email': 'taylor.morgan@example.com',
            'phone': '555-9999',
            'form_ids': [str(self.form_one.id), str(self.form_two.id)],
            'custom_message': 'Welcome aboard!',
            # send_email omitted to avoid hitting the email service in tests
        }

        response = self.client.post(
            reverse('create_onboarding_employee'),
            data=payload,
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('hr_onboarding_dashboard'))

        prospect = ProspectiveEmployee.objects.get(email='taylor.morgan@example.com')
        self.assertEqual(prospect.first_name, 'Taylor')
        self.assertEqual(prospect.last_name, 'Morgan')

        invitation_one = OnboardingInvitation.objects.get(
            onboarding_form=self.form_one,
            prospective_employee=prospect,
        )
        invitation_two = OnboardingInvitation.objects.get(
            onboarding_form=self.form_two,
            prospective_employee=prospect,
        )

        self.assertEqual(invitation_one.custom_message, 'Welcome aboard!')
        self.assertEqual(invitation_two.custom_message, 'Welcome aboard!')

    def test_existing_prospect_updates_and_reuses_invitations(self):
        prospect = ProspectiveEmployee.objects.create(
            email='existing@example.com',
            first_name='Existing',
            last_name='Candidate',
            phone='555-1111',
            created_by=self.hr_user,
        )
        invitation = OnboardingInvitation.objects.create(
            onboarding_form=self.form_one,
            prospective_employee=prospect,
            sent_by=self.hr_user,
            custom_message='Original message',
        )

        payload = {
            'first_name': 'Existing',
            'last_name': 'Candidate',
            'email': 'existing@example.com',
            'phone': '555-2222',
            'form_ids': [str(self.form_one.id)],
            'custom_message': 'Updated instructions',
        }

        response = self.client.post(
            reverse('create_onboarding_employee'),
            data=payload,
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('hr_onboarding_dashboard'))

        prospect.refresh_from_db()
        self.assertEqual(prospect.phone, '555-2222')

        invitation.refresh_from_db()
        self.assertEqual(invitation.custom_message, 'Updated instructions')
        self.assertEqual(invitation.sent_by, self.hr_user)
