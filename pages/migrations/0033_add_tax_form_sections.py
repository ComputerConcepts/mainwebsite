# Generated migration for tax form sections

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0032_onboardingassessmentquestion_allow_multiple_answers'),
    ]

    operations = [
        # Create TaxFormSection model
        migrations.CreateModel(
            name='TaxFormSection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(help_text="Section title (e.g., 'Personal Information')", max_length=200)),
                ('description', models.TextField(blank=True, help_text='Optional description or instructions for this section')),
                ('order', models.IntegerField(default=0, help_text='Display order within the form')),
                ('is_collapsible', models.BooleanField(default=False, help_text='Can this section be collapsed/expanded?')),
                ('is_expanded_by_default', models.BooleanField(default=True, help_text='Is section expanded by default?')),
                ('is_active', models.BooleanField(default=True)),
                ('show_border', models.BooleanField(default=True, help_text='Show border around section')),
                ('background_color', models.CharField(blank=True, help_text="Optional background color (e.g., '#f5f5f5')", max_length=20)),
                ('tax_form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='pages.taxformtemplate')),
            ],
            options={
                'ordering': ['tax_form', 'order', 'id'],
            },
        ),
        
        # Add unique constraint for TaxFormSection
        migrations.AddConstraint(
            model_name='taxformsection',
            constraint=models.UniqueConstraint(fields=['tax_form', 'title'], name='unique_tax_form_section'),
        ),
        
        # Rename old section field to section_name
        migrations.RenameField(
            model_name='taxformfield',
            old_name='section',
            new_name='section_name',
        ),
        
        # Add new section ForeignKey to TaxFormField
        migrations.AddField(
            model_name='taxformfield',
            name='section',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='fields', 
                to='pages.taxformsection',
                help_text='Section this field belongs to (leave blank for independent fields)'
            ),
        ),
        
        # Update help text for section_name
        migrations.AlterField(
            model_name='taxformfield',
            name='section_name',
            field=models.CharField(
                blank=True, 
                max_length=100, 
                help_text='Legacy section name (deprecated - use section relationship instead)'
            ),
        ),
        
        # Update help text for order field
        migrations.AlterField(
            model_name='taxformfield',
            name='order',
            field=models.IntegerField(default=0, help_text='Display order within section or form'),
        ),
    ]
