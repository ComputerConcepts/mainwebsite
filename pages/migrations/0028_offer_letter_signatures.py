from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0027_onboardingofferletter'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardingofferletter',
            name='employer_signature_data',
            field=models.TextField(blank=True, help_text='Base64 encoded employer signature image'),
        ),
        migrations.AddField(
            model_name='onboardingofferletter',
            name='offer_pdf_path',
            field=models.CharField(blank=True, help_text='Stored PDF path for the signed offer letter', max_length=500),
        ),
        migrations.AlterField(
            model_name='onboardingofferletter',
            name='employee_signature_data',
            field=models.TextField(blank=True, help_text='Base64 encoded employee signature image'),
        ),
    ]
