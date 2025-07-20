#!/usr/bin/env python
"""
Background AI Analysis Processor
This script processes queued AI file analyses and can be scheduled to run periodically.
Usage: python background_ai_processor.py
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')

import django
django.setup()

from django.utils import timezone
from pages.models import AIFileAnalysis, FileDocument
from pages.ai_file_analysis import get_ai_file_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BackgroundAIProcessor:
    """Background processor for AI file analysis queue"""
    
    def __init__(self, max_concurrent=3, process_timeout=300):
        self.max_concurrent = max_concurrent
        self.process_timeout = process_timeout  # 5 minutes timeout per file
        self.analyzer = get_ai_file_analyzer()
        
    def get_queue_status(self):
        """Get current queue status"""
        stats = {}
        for status_dict in AIFileAnalysis.get_queue_stats():
            stats[status_dict['status']] = status_dict['count']
        return stats
    
    def process_next_analysis(self):
        """Process the next analysis in the queue"""
        analysis = AIFileAnalysis.get_next_in_queue()
        
        if not analysis:
            return False
            
        logger.info(f"Starting analysis of file: {analysis.document.name} (ID: {analysis.id})")
        
        try:
            # Mark as processing
            analysis.mark_processing()
            start_time = time.time()
            
            # Verify file exists
            if not analysis.document.file or not hasattr(analysis.document.file, 'path'):
                raise Exception("File not found or inaccessible")
            
            file_path = analysis.document.file.path
            if not os.path.exists(file_path):
                raise Exception(f"File does not exist at path: {file_path}")
            
            # Perform AI analysis using the existing analyzer
            result = self.analyzer.analyze_file(analysis.document)
            
            if result and result.status == 'completed':
                # Analysis completed successfully
                processing_time = int((time.time() - start_time) * 1000)
                analysis.mark_completed(processing_time)
                logger.info(f"Completed analysis of {analysis.document.name} in {processing_time}ms")
                return True
            else:
                # Analysis failed
                error_msg = result.error_message if result else "Unknown analysis error"
                analysis.mark_failed(error_msg)
                logger.error(f"Failed analysis of {analysis.document.name}: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            analysis.mark_failed(error_msg)
            logger.error(f"Exception during analysis of {analysis.document.name}: {error_msg}")
            return False
    
    def cleanup_stale_processing(self):
        """Clean up analyses that have been stuck in processing state"""
        timeout_threshold = timezone.now() - timedelta(seconds=self.process_timeout)
        
        stale_analyses = AIFileAnalysis.objects.filter(
            status='processing',
            processing_started_at__lt=timeout_threshold
        )
        
        for analysis in stale_analyses:
            logger.warning(f"Marking stale analysis as failed: {analysis.document.name}")
            analysis.mark_failed("Processing timeout - analysis was stuck")
    
    def process_queue_batch(self, batch_size=None):
        """Process a batch of analyses from the queue"""
        if batch_size is None:
            batch_size = self.max_concurrent
            
        processed_count = 0
        
        # Clean up any stale processing first
        self.cleanup_stale_processing()
        
        # Get queue status
        queue_stats = self.get_queue_status()
        logger.info(f"Queue status: {queue_stats}")
        
        # Process analyses
        for _ in range(batch_size):
            if self.process_next_analysis():
                processed_count += 1
            else:
                break  # No more analyses to process
                
        return processed_count
    
    def run_continuous(self, check_interval=30):
        """Run continuous processing with specified check interval (seconds)"""
        logger.info(f"Starting continuous AI processing (checking every {check_interval}s)")
        
        try:
            while True:
                processed = self.process_queue_batch()
                
                if processed > 0:
                    logger.info(f"Processed {processed} analyses this batch")
                else:
                    logger.debug("No analyses to process, waiting...")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error in continuous processing: {e}")
            raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Background AI Analysis Processor')
    parser.add_argument('--mode', choices=['single', 'batch', 'continuous'], 
                       default='batch', help='Processing mode')
    parser.add_argument('--batch-size', type=int, default=5, 
                       help='Number of analyses to process in batch mode')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Check interval in seconds for continuous mode')
    parser.add_argument('--max-concurrent', type=int, default=3,
                       help='Maximum concurrent analyses')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Timeout per analysis in seconds')
    
    args = parser.parse_args()
    
    processor = BackgroundAIProcessor(
        max_concurrent=args.max_concurrent,
        process_timeout=args.timeout
    )
    
    logger.info(f"Starting AI processor in {args.mode} mode")
    
    try:
        if args.mode == 'single':
            # Process just one analysis
            processed = processor.process_next_analysis()
            if processed:
                logger.info("Processed 1 analysis")
            else:
                logger.info("No analyses to process")
                
        elif args.mode == 'batch':
            # Process a batch of analyses
            processed = processor.process_queue_batch(args.batch_size)
            logger.info(f"Processed {processed} analyses")
            
        elif args.mode == 'continuous':
            # Run continuous processing
            processor.run_continuous(args.interval)
            
    except Exception as e:
        logger.error(f"Error in main processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
