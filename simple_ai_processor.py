#!/usr/bin/env python
"""
Simple AI Analysis Processor
Just processes queued analyses and marks them as completed.
Usage: python simple_ai_processor.py
"""

import os
import sys
import time

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')

import django
django.setup()

from pages.models import AIFileAnalysis
from pages.ai_file_analysis import get_ai_file_analyzer

def process_queued_analyses():
    """Process all queued analyses"""
    print("Checking for queued analyses...")
    
    # Get queued analyses
    queued_analyses = AIFileAnalysis.objects.filter(status='queued').order_by('queued_at')
    
    if not queued_analyses.exists():
        print("No queued analyses found.")
        return
    
    print(f"Found {queued_analyses.count()} analyses to process.")
    
    analyzer = get_ai_file_analyzer()
    
    for analysis in queued_analyses:
        print(f"Processing: {analysis.document.name}")
        
        try:
            # Mark as processing
            analysis.status = 'processing'
            analysis.save()
            
            # Do the analysis
            result = analyzer.analyze_file(analysis.document)
            
            if result:
                # Mark as completed
                analysis.status = 'completed'
                analysis.analysis_completed = True
                analysis.save()
                print(f"✓ Completed: {analysis.document.name}")
            else:
                # Mark as failed
                analysis.status = 'failed'
                analysis.error_message = "Analysis failed"
                analysis.save()
                print(f"✗ Failed: {analysis.document.name}")
                
        except Exception as e:
            # Mark as failed
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()
            print(f"✗ Error processing {analysis.document.name}: {str(e)}")

if __name__ == "__main__":
    try:
        process_queued_analyses()
        print("Processing completed.")
    except Exception as e:
        print(f"Error: {str(e)}")
