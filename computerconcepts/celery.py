"""
Celery configuration for Computer Concepts
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')

app = Celery('computerconcepts')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'batch-process-applications': {
        'task': 'pages.tasks.batch_process_applications',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'cleanup-old-analysis': {
        'task': 'pages.tasks.cleanup_old_analysis',
        'schedule': 86400.0,  # Run daily
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
