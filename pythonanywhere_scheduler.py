#!/usr/bin/env python
"""
PythonAnywhere Scheduler Script for AI Analysis
This script is designed to be run as a scheduled task on PythonAnywhere.
It processes a batch of queued AI analyses and exits.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project directory to the path
project_path = '/home/yourusername/computer-concepts'  # Update this path
sys.path.append(project_path)
os.chdir(project_path)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')

import django
django.setup()

from background_ai_processor import BackgroundAIProcessor

# Configure logging for PythonAnywhere
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/yourusername/ai_processing.log'),  # Update this path
    ]
)

logger = logging.getLogger(__name__)

def run_scheduled_processing():
    """Run scheduled AI processing batch"""
    logger.info("=== Starting scheduled AI processing ===")
    
    try:
        # Create processor with conservative settings for shared hosting
        processor = BackgroundAIProcessor(
            max_concurrent=2,  # Lower for shared hosting
            process_timeout=180  # 3 minutes timeout
        )
        
        # Process a small batch
        processed = processor.process_queue_batch(batch_size=3)
        
        logger.info(f"Scheduled processing completed. Processed {processed} analyses.")
        
        # Get final queue status
        queue_stats = processor.get_queue_status()
        logger.info(f"Final queue status: {queue_stats}")
        
        return processed
        
    except Exception as e:
        logger.error(f"Error in scheduled processing: {e}")
        raise

if __name__ == "__main__":
    try:
        run_scheduled_processing()
        logger.info("=== Scheduled processing finished successfully ===")
    except Exception as e:
        logger.error(f"Scheduled processing failed: {e}")
        sys.exit(1)
