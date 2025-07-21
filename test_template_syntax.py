#!/usr/bin/env python
"""
Test script to validate Django template syntax
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from django.template.loader import get_template
from django.template import TemplateDoesNotExist, TemplateSyntaxError

def test_template_syntax():
    """Test if channel.html template has valid syntax"""
    print("🧪 Testing channel.html template syntax...")
    
    try:
        template = get_template('employee/chat/channel.html')
        print("✅ Template loaded successfully - no syntax errors!")
        return True
    except TemplateSyntaxError as e:
        print(f"❌ Template syntax error: {e}")
        print(f"   Line: {getattr(e, 'lineno', 'unknown')}")
        return False
    except TemplateDoesNotExist as e:
        print(f"❌ Template not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_template_syntax()
    if success:
        print("\n🎉 Template validation passed!")
    else:
        print("\n💥 Template validation failed!")
    sys.exit(0 if success else 1)
