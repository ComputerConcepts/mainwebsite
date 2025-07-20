"""
Django management command for AI analysis queue management
Usage: python manage.py manage_ai_queue [options]
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models
from datetime import timedelta
from pages.models import AIFileAnalysis
from pages.ai_file_analysis import get_ai_file_analyzer


class Command(BaseCommand):
    help = 'Manage AI analysis queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show queue status',
        )
        parser.add_argument(
            '--reset-stale',
            action='store_true',
            help='Reset stale processing analyses to queued',
        )
        parser.add_argument(
            '--reset-failed',
            action='store_true',
            help='Reset failed analyses to queued for retry',
        )
        parser.add_argument(
            '--process-one',
            action='store_true',
            help='Process one analysis from the queue',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old completed analyses (older than 30 days)',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout threshold in seconds for stale analyses (default: 300)',
        )

    def handle(self, *args, **options):
        if options['status']:
            self.show_status()
        
        if options['reset_stale']:
            self.reset_stale_analyses(options['timeout'])
        
        if options['reset_failed']:
            self.reset_failed_analyses()
        
        if options['process_one']:
            self.process_one_analysis()
        
        if options['cleanup']:
            self.cleanup_old_analyses()

    def show_status(self):
        """Show current queue status"""
        self.stdout.write(self.style.SUCCESS('\n=== AI Analysis Queue Status ==='))
        
        stats = {}
        for stat in AIFileAnalysis.get_queue_stats():
            stats[stat['status']] = stat['count']
        
        total = sum(stats.values())
        
        self.stdout.write(f"Total analyses: {total}")
        self.stdout.write(f"Queued: {stats.get('queued', 0)}")
        self.stdout.write(f"Processing: {stats.get('processing', 0)}")
        self.stdout.write(f"Completed: {stats.get('completed', 0)}")
        self.stdout.write(f"Failed: {stats.get('failed', 0)}")
        self.stdout.write(f"Retrying: {stats.get('retrying', 0)}")
        
        # Show oldest queued analysis
        oldest_queued = AIFileAnalysis.objects.filter(
            status__in=['queued', 'retrying']
        ).order_by('queued_at').first()
        
        if oldest_queued:
            age = timezone.now() - oldest_queued.queued_at
            self.stdout.write(f"\nOldest queued analysis: {oldest_queued.document.name}")
            self.stdout.write(f"Queued {age.total_seconds():.0f} seconds ago")

    def reset_stale_analyses(self, timeout_seconds):
        """Reset analyses stuck in processing state"""
        timeout_threshold = timezone.now() - timedelta(seconds=timeout_seconds)
        
        stale_analyses = AIFileAnalysis.objects.filter(
            status='processing',
            processing_started_at__lt=timeout_threshold
        )
        
        count = stale_analyses.count()
        if count > 0:
            for analysis in stale_analyses:
                analysis.status = 'queued'
                analysis.processing_started_at = None
                analysis.error_message = f'Reset from stale processing state (timeout: {timeout_seconds}s)'
                analysis.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Reset {count} stale analyses to queued state')
            )
        else:
            self.stdout.write('No stale analyses found')

    def reset_failed_analyses(self):
        """Reset failed analyses that can be retried"""
        failed_analyses = AIFileAnalysis.objects.filter(
            status='failed',
            retry_count__lt=models.F('max_retries')
        )
        
        count = failed_analyses.count()
        if count > 0:
            for analysis in failed_analyses:
                analysis.status = 'queued'
                analysis.error_message = ''
                analysis.queued_at = timezone.now()
                analysis.processing_started_at = None
                analysis.analysis_completed_at = None
                analysis.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Reset {count} failed analyses to queued state')
            )
        else:
            self.stdout.write('No failed analyses available for retry')

    def process_one_analysis(self):
        """Process one analysis from the queue"""
        analysis = AIFileAnalysis.get_next_in_queue()
        
        if not analysis:
            self.stdout.write('No analyses in queue to process')
            return
        
        self.stdout.write(f'Processing: {analysis.document.name}')
        
        try:
            # Mark as processing
            analysis.mark_processing()
            
            # Get the analyzer and process
            analyzer = get_ai_file_analyzer()
            result = analyzer.analyze_file(analysis.document)
            
            if result and result.status == 'completed':
                analysis.mark_completed()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully completed analysis of {analysis.document.name}')
                )
            else:
                error_msg = result.error_message if result else "Unknown analysis error"
                analysis.mark_failed(error_msg)
                self.stdout.write(
                    self.style.ERROR(f'Analysis failed: {error_msg}')
                )
                
        except Exception as e:
            analysis.mark_failed(str(e))
            self.stdout.write(
                self.style.ERROR(f'Exception during analysis: {str(e)}')
            )

    def cleanup_old_analyses(self):
        """Clean up old completed analyses"""
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_analyses = AIFileAnalysis.objects.filter(
            status='completed',
            analysis_completed_at__lt=cutoff_date
        )
        
        count = old_analyses.count()
        if count > 0:
            # Ask for confirmation
            self.stdout.write(f'This will delete {count} completed analyses older than 30 days.')
            confirm = input('Are you sure? (yes/no): ')
            
            if confirm.lower() == 'yes':
                old_analyses.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {count} old completed analyses')
                )
            else:
                self.stdout.write('Cleanup cancelled')
        else:
            self.stdout.write('No old analyses to clean up')
