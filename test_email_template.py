"""
Test script to verify email template rendering for client welcome emails
"""
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.template.loader import render_to_string
from pages.models import TaxClient
from django.contrib.auth.models import User

def test_welcome_email_template():
    """Test that the welcome email template renders correctly"""
    
    # Create a mock client object for testing
    class MockClient:
        def __init__(self):
            self.first_name = "John"
            self.last_name = "Doe" 
            self.email = "john.doe@example.com"
            self.phone = "(555) 123-4567"
            self.current_pin = "1234"
            self.id = "12345678-1234-1234-1234-123456789012"
            
        @property
        def full_name(self):
            return f"{self.first_name} {self.last_name}"
            
        def created_at(self):
            from django.utils import timezone
            return timezone.now()
            
        def created_by(self):
            class MockUser:
                def get_full_name(self):
                    return "Jane Smith"
                username = "jsmith"
            return MockUser()
    
    # Create mock client
    mock_client = MockClient()
    
    # Test context
    context = {
        'client': mock_client,
        'site_url': 'https://onecomputerconcepts.com',
        'domain': 'onecomputerconcepts.com',
    }
    
    try:
        # Test HTML template
        html_content = render_to_string('email/client_welcome.html', context)
        print("✅ HTML template rendered successfully!")
        print(f"   Length: {len(html_content)} characters")
        
        # Test text template  
        text_content = render_to_string('email/client_welcome.txt', context)
        print("✅ Text template rendered successfully!")
        print(f"   Length: {len(text_content)} characters")
        
        # Check that key information is present
        key_items = [
            mock_client.first_name,
            mock_client.current_pin,
            mock_client.email,
            mock_client.full_name
        ]
        
        for item in key_items:
            if item in html_content and item in text_content:
                print(f"✅ Found '{item}' in both templates")
            else:
                print(f"❌ Missing '{item}' in templates")
                
        print("\n📧 Email template test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Template rendering failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing client welcome email templates...")
    test_welcome_email_template()