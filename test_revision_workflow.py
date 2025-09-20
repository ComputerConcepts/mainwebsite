#!/usr/bin/env python
"""
Test script to create a submission that needs revision
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.contrib.auth.models import User
from pages.models import OnboardingInvitation, OnboardingSubmission

def test_revision_workflow():
    """Test the revision workflow"""
    print("🧪 Testing revision workflow...")
    
    # Get the test invitation
    try:
        invitation = OnboardingInvitation.objects.filter(
            prospective_employee__email='test.signature@example.com'
        ).first()
        
        if not invitation:
            print("❌ No invitation found. Run test_signature_form.py first.")
            return False
            
        print(f"✓ Found invitation: {invitation.id}")
        
        # Get or create the submission
        submission, created = OnboardingSubmission.objects.get_or_create(
            invitation=invitation,
            defaults={
                'form_data': {
                    'full_name': 'Test Signature User',
                    'email_address': 'test.signature@example.com',
                    'digital_signature': 'data:image/png;base64,sample_data'
                },
                'uploaded_files': ['signature_sample.png']
            }
        )
        
        if created:
            print(f"✓ Created new submission: {submission.id}")
        else:
            print(f"✓ Using existing submission: {submission.id}")
        
        # Set the submission to need revision
        submission.review_status = 'needs_revision'
        submission.review_notes = 'Please update your signature - it appears to be incomplete. Also, please double-check your contact information.'
        submission.save()
        
        print(f"✓ Set submission to 'needs_revision'")
        print(f"✓ Added review notes: {submission.review_notes}")
        
        print("\n🎉 Revision test setup completed!")
        print("📍 To test the dashboard:")
        print("1. Go to: http://127.0.0.1:8000/onboarding/login/")
        print("2. Login with: test.signature@example.com / PIN: 123456")
        print("3. Check that the form appears in 'Pending Forms' with revision notice")
        print("4. Verify the revision comments are displayed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_revision_workflow()
    if success:
        print("\n✅ Revision workflow test setup complete!")
    else:
        print("\n❌ Revision workflow test setup failed!")
        sys.exit(1)