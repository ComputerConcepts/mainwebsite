from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0031_onboardingassessment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardingassessmentquestion',
            name='allow_multiple_answers',
            field=models.BooleanField(default=False, help_text='When true, candidates may select multiple choices'),
        ),
    ]
