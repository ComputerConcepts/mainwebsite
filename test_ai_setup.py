#!/usr/bin/env python3
"""
Test script to verify AI analysis setup
"""
import os
import sys
import django

# Add the project directory to Python path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_DIR)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import Career, JobPosting
from pages.ai_analysis import analyze_career_application

def test_ai_setup():
    """Test basic AI analysis setup"""
    print("Testing AI Analysis Setup...")
    print("=" * 40)
    
    # Check if we have any applications
    applications = Career.objects.all()
    print(f"Total applications: {applications.count()}")
    
    # Check unprocessed applications
    unprocessed = Career.objects.filter(ai_analysis_completed=False)
    print(f"Unprocessed applications: {unprocessed.count()}")
    
    # Check processed applications
    processed = Career.objects.filter(ai_analysis_completed=True)
    print(f"Processed applications: {processed.count()}")
    
    # Test with a sample application if available
    sample_app = Career.objects.filter(resume__isnull=False).first()
    if sample_app:
        print(f"\nTesting with sample application: {sample_app.first_name} {sample_app.last_name}")
        print(f"Job: {sample_app.job_posting.title}")
        print(f"Resume: {sample_app.resume.name if sample_app.resume else 'No resume'}")
        
        # Test analysis
        if sample_app.resume:
            print("Running AI analysis...")
            result = analyze_career_application(sample_app)
            if result:
                print("✓ AI analysis successful!")
                print(f"  Match Score: {result['overall_match']}%")
                print(f"  Skills Match: {result['skills_match']}%")
                print(f"  Experience Match: {result['experience_match']}%")
                print(f"  Education Match: {result['education_match']}%")
                print(f"  Recommendation: {result['recommendation']}")
            else:
                print("✗ AI analysis failed")
        else:
            print("No resume to analyze")
    else:
        print("No applications found for testing")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    test_ai_setup()
