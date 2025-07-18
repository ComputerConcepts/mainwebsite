"""
Celery tasks for background processing of AI analysis
"""
from celery import shared_task
from django.apps import apps
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_resume_analysis(self, career_application_id):
    """
    Background task to process AI analysis for a career application
    """
    try:
        # Import here to avoid circular imports
        from pages.models import Career
        from pages.ai_analysis import analyze_career_application
        
        # Get the career application
        career_application = Career.objects.get(id=career_application_id)
        
        if career_application.ai_analysis_completed:
            logger.info(f"Analysis already completed for application {career_application_id}")
            return f"Analysis already completed for application {career_application_id}"
        
        # Perform AI analysis
        logger.info(f"Starting AI analysis for application {career_application_id}")
        analysis_results = analyze_career_application(career_application)
        
        if analysis_results:
            logger.info(f"Successfully completed AI analysis for application {career_application_id}")
            return f"Successfully analyzed application {career_application_id} - Score: {analysis_results['overall_match']}"
        else:
            logger.error(f"AI analysis failed for application {career_application_id}")
            return f"Analysis failed for application {career_application_id}"
            
    except Career.DoesNotExist:
        logger.error(f"Career application {career_application_id} not found")
        return f"Career application {career_application_id} not found"
    
    except Exception as exc:
        logger.error(f"Error in AI analysis task for application {career_application_id}: {str(exc)}")
        
        # Retry the task
        try:
            self.retry(countdown=60, exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for application {career_application_id}")
            
            # Mark as failed
            try:
                career_application = Career.objects.get(id=career_application_id)
                career_application.ai_analysis_completed = False
                career_application.ai_summary = "AI analysis failed after multiple attempts"
                career_application.ai_processed_at = timezone.now()
                career_application.save()
            except:
                pass
            
            return f"Analysis failed permanently for application {career_application_id}"


@shared_task
def batch_process_applications():
    """
    Background task to process all pending applications
    """
    try:
        from pages.models import Career
        
        # Get all applications that haven't been analyzed yet
        pending_applications = Career.objects.filter(
            ai_analysis_completed=False,
            resume__isnull=False
        ).exclude(resume='')
        
        processed_count = 0
        for application in pending_applications:
            try:
                # Launch individual analysis task
                process_resume_analysis.delay(str(application.id))
                processed_count += 1
                logger.info(f"Queued AI analysis for application {application.id}")
            except Exception as e:
                logger.error(f"Error queuing analysis for application {application.id}: {str(e)}")
        
        logger.info(f"Queued {processed_count} applications for AI analysis")
        return f"Queued {processed_count} applications for AI analysis"
        
    except Exception as exc:
        logger.error(f"Error in batch processing task: {str(exc)}")
        return f"Batch processing failed: {str(exc)}"


@shared_task
def cleanup_old_analysis():
    """
    Background task to cleanup old AI analysis data (optional)
    """
    try:
        from pages.models import Career
        from datetime import timedelta
        
        # Find applications older than 90 days that might need re-analysis
        cutoff_date = timezone.now() - timedelta(days=90)
        old_applications = Career.objects.filter(
            ai_processed_at__lt=cutoff_date,
            ai_analysis_completed=True
        )
        
        # You can implement cleanup logic here if needed
        logger.info(f"Found {old_applications.count()} old analyses")
        
        return f"Cleanup completed for {old_applications.count()} old analyses"
        
    except Exception as exc:
        logger.error(f"Error in cleanup task: {str(exc)}")
        return f"Cleanup failed: {str(exc)}"
