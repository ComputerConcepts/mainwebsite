import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0026_add_tax_client_waiver'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnboardingOfferLetter',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('position_title', models.CharField(max_length=200)),
                ('employment_type', models.CharField(blank=True, max_length=100)),
                ('salary_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('salary_currency', models.CharField(default='USD', max_length=10)),
                ('pay_frequency', models.CharField(choices=[('annual', 'Per Year'), ('monthly', 'Per Month'), ('biweekly', 'Per Pay Period'), ('weekly', 'Per Week'), ('hourly', 'Per Hour')], default='annual', max_length=20)),
                ('compensation_notes', models.TextField(blank=True, help_text='Additional compensation details (bonuses, benefits, etc.)')),
                ('start_date', models.DateField(blank=True, null=True)),
                ('offer_expires_at', models.DateField(blank=True, null=True)),
                ('additional_terms', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending_employee', 'Awaiting Employee Signature'), ('signed', 'Fully Signed'), ('declined', 'Declined')], default='draft', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employer_signature_name', models.CharField(blank=True, max_length=200)),
                ('employer_signed_at', models.DateTimeField(blank=True, null=True)),
                ('employee_signature_name', models.CharField(blank=True, max_length=200)),
                ('employee_signed_at', models.DateTimeField(blank=True, null=True)),
                ('employee_signature_data', models.TextField(blank=True, help_text='Base64 encoded signature image or payload')),
                ('decline_reason', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offer_letters_created', to=settings.AUTH_USER_MODEL)),
                ('employer_signed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offer_letters_signed', to=settings.AUTH_USER_MODEL)),
                ('submission', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='offer_letter', to='pages.onboardingsubmission')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
