from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0028_offer_letter_signatures'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardingofferletter',
            name='job_posting',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offer_letters', to='pages.jobposting'),
        ),
    ]
