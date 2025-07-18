#!/usr/bin/env python3
"""
AI Resume Processor - Standalone Script for PythonAnywhere
Run this script hourly to process job applications with AI analysis

Usage:
    python ai_resume_processor.py

This script will:
1. Find all unprocessed job applications
2. Extract text from resume files
3. Analyze job match using AI
4. Update database with results
5. Log all activities

Set up on PythonAnywhere:
1. Upload this script to your project directory
2. Set up a scheduled task to run every hour:
   python3.10 /home/yourusername/mysite/ai_resume_processor.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
import logging

# Add the project directory to Python path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_DIR)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

# Now import Django models and utilities
from pages.models import Career, JobPosting
from pages.ai_analysis import analyze_career_application
from django.utils import timezone
from django.conf import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_DIR, 'ai_processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main processing function"""
    start_time = datetime.now()
    logger.info("="*50)
    logger.info(f"Starting AI Resume Processor at {start_time}")
    
    try:
        # Find all applications that need processing
        pending_applications = Career.objects.filter(
            ai_analysis_completed=False,
            resume__isnull=False
        ).exclude(resume='')
        
        logger.info(f"Found {pending_applications.count()} applications to process")
        
        if pending_applications.count() == 0:
            logger.info("No applications to process. Exiting.")
            return
        
        processed_count = 0
        error_count = 0
        
        for application in pending_applications:
            try:
                logger.info(f"Processing application {application.id} - {application.first_name} {application.last_name}")
                
                # Check if resume file exists
                if not application.resume or not os.path.exists(application.resume.path):
                    logger.warning(f"Resume file not found for application {application.id}")
                    continue
                
                # Perform AI analysis
                result = analyze_career_application(application)
                
                if result:
                    processed_count += 1
                    logger.info(f"Successfully processed application {application.id} - Match Score: {result['overall_match']}%")
                else:
                    error_count += 1
                    logger.error(f"Failed to process application {application.id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing application {application.id}: {str(e)}")
                
                # Mark as failed to avoid reprocessing
                try:
                    application.ai_analysis_completed = False
                    application.ai_summary = f"Processing failed: {str(e)}"
                    application.ai_processed_at = timezone.now()
                    application.save()
                except Exception as save_error:
                    logger.error(f"Failed to save error state for application {application.id}: {str(save_error)}")
        
        # Log summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"Processing completed in {duration}")
        logger.info(f"Successfully processed: {processed_count} applications")
        logger.info(f"Errors encountered: {error_count} applications")
        logger.info("="*50)
        
        # Optional: Clean up old log files (keep last 30 days)
        cleanup_old_logs()
        
    except Exception as e:
        logger.error(f"Critical error in main processing: {str(e)}")
        raise


def cleanup_old_logs():
    """Clean up log files older than 30 days"""
    try:
        log_file = os.path.join(PROJECT_DIR, 'ai_processor.log')
        if os.path.exists(log_file):
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_age > timedelta(days=30):
                # Archive old log
                archive_name = f"ai_processor_{datetime.now().strftime('%Y%m%d')}.log"
                archive_path = os.path.join(PROJECT_DIR, 'logs', archive_name)
                
                # Create logs directory if it doesn't exist
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                
                # Move old log to archive
                os.rename(log_file, archive_path)
                logger.info(f"Archived old log file to {archive_path}")
                
    except Exception as e:
        logger.warning(f"Failed to cleanup old logs: {str(e)}")


def get_processing_stats():
    """Get statistics about processed applications"""
    try:
        total_applications = Career.objects.count()
        processed_applications = Career.objects.filter(ai_analysis_completed=True).count()
        pending_applications = Career.objects.filter(ai_analysis_completed=False).count()
        
        # Applications processed in last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        recent_processed = Career.objects.filter(
            ai_analysis_completed=True,
            ai_processed_at__gte=last_24h
        ).count()
        
        # Average match scores
        processed_apps = Career.objects.filter(
            ai_analysis_completed=True,
            ai_match_score__isnull=False
        )
        
        if processed_apps.exists():
            avg_match_score = sum(app.ai_match_score for app in processed_apps) / processed_apps.count()
        else:
            avg_match_score = 0
        
        logger.info(f"Processing Statistics:")
        logger.info(f"  Total Applications: {total_applications}")
        logger.info(f"  Processed: {processed_applications}")
        logger.info(f"  Pending: {pending_applications}")
        logger.info(f"  Processed in last 24h: {recent_processed}")
        logger.info(f"  Average Match Score: {avg_match_score:.2f}%")
        
    except Exception as e:
        logger.error(f"Error getting processing stats: {str(e)}")


def test_ai_analysis():
    """Test function to verify AI analysis is working"""
    try:
        logger.info("Testing AI analysis system...")
        
        # Find a sample application
        sample_app = Career.objects.filter(resume__isnull=False).first()
        
        if not sample_app:
            logger.warning("No applications with resumes found for testing")
            return
        
        logger.info(f"Testing with application: {sample_app.id}")
        
        # Temporarily reset analysis flags
        original_completed = sample_app.ai_analysis_completed
        sample_app.ai_analysis_completed = False
        sample_app.save()
        
        # Run analysis
        result = analyze_career_application(sample_app)
        
        if result:
            logger.info(f"Test successful! Match score: {result['overall_match']}%")
        else:
            logger.error("Test failed - no results returned")
            
        # Restore original state if it was already processed
        if original_completed:
            sample_app.ai_analysis_completed = original_completed
            sample_app.save()
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")


if __name__ == "__main__":
    # Check if we're running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_ai_analysis()
    elif len(sys.argv) > 1 and sys.argv[1] == 'stats':
        get_processing_stats()
    else:
        main()
