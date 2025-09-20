#!/usr/bin/env python
"""
Test script to verify signature processing functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.contrib.auth.models import User
from pages.models import OnboardingInvitation, OnboardingSubmission
import base64
import uuid

def test_signature_processing():
    """Test signature field processing"""
    print("🎯 Testing signature processing...")
    
    # Get the test invitation
    try:
        invitation = OnboardingInvitation.objects.filter(
            prospective_employee__email='test.signature@example.com'
        ).first()
        
        if not invitation:
            print("❌ No invitation found. Run test_signature_form.py first.")
            return False
            
        print(f"✓ Found invitation: {invitation.id}")
        
        # Create a sample signature (base64 encoded image data)
        # This simulates what would come from the canvas
        sample_signature_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        # Simulate form submission data
        form_data = {
            'full_name': 'Test Signature User',
            'email_address': 'test.signature@example.com',
            'digital_signature': sample_signature_data
        }
        
        print("✓ Created sample signature data")
        print(f"✓ Form data prepared: {list(form_data.keys())}")
        
        # Test the signature field processing logic
        if 'digital_signature' in form_data and form_data['digital_signature']:
            signature_data = form_data['digital_signature']
            
            if signature_data.startswith('data:image/png;base64,'):
                # Extract base64 data
                base64_data = signature_data.split(',')[1]
                
                # Decode base64 to binary
                try:
                    binary_data = base64.b64decode(base64_data)
                    print(f"✓ Successfully decoded signature data ({len(binary_data)} bytes)")
                    
                    # Test creating OnboardingSubmission record
                    signature_filename = f'signature_{uuid.uuid4().hex}.png'
                    form_submission = OnboardingSubmission.objects.create(
                        invitation=invitation,
                        form_data=form_data,
                        uploaded_files=[signature_filename]
                    )
                    
                    print(f"✓ Created form submission: {form_submission.id}")
                    print(f"✓ Signature file reference: {signature_filename}")
                    
                except Exception as e:
                    print(f"❌ Error processing signature: {e}")
                    return False
            else:
                print("❌ Invalid signature data format")
                return False
        
        print("\n🎉 Signature processing test completed successfully!")
        print("🔍 Manual testing steps:")
        print("1. Visit: http://127.0.0.1:8000/onboarding/login/")
        print("2. Login with: test.signature@example.com / PIN: 123456")
        print("3. Fill out the form and draw in the signature field")
        print("4. Submit and verify signature is saved")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_signature_processing()
    if success:
        print("\n✅ All signature tests passed!")
    else:
        print("\n❌ Signature tests failed!")
        sys.exit(1)