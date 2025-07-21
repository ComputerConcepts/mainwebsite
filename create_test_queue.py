#!/usr/bin/env python
"""
Script to create test queued analyses for testing
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import AIFileAnalysis, FileDocument

def create_test_queued_analyses():
    """Create some test queued analyses"""
    print("Creating test queued analyses...")
    
    # Find files that don't have analysis or have failed analysis
    files_needing_analysis = FileDocument.objects.filter(
        ai_analysis__isnull=True
    ) | FileDocument.objects.filter(
        ai_analysis__status__in=['failed', 'retrying']
    )
    
    count = 0
    for file_doc in files_needing_analysis[:5]:  # Limit to 5 for testing
        analysis, created = AIFileAnalysis.objects.get_or_create(
            document=file_doc,
            defaults={
                'status': 'queued',
                'priority': 5
            }
        )
        
        if created:
            print(f"✓ Created queued analysis for: {file_doc.name}")
            count += 1
        else:
            # Reset existing analysis to queued
            analysis.status = 'queued'
            analysis.retry_count = 0
            analysis.error_message = ''
            analysis.save()
            print(f"✓ Reset analysis to queued for: {file_doc.name}")
            count += 1
    
    print(f"\n📊 Created/reset {count} queued analyses")
    return count

if __name__ == "__main__":
    create_test_queued_analyses()
