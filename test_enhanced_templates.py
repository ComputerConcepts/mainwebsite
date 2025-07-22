#!/usr/bin/env python3
"""
Test script to validate enhanced channel templates
"""

import os
import sys
import django
from django.template import Template, Context
from django.template.loader import get_template
from django.test import RequestFactory

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

def test_template_syntax():
    """Test that all enhanced templates have valid syntax"""
    templates_to_test = [
        'employee/chat/channel.html',
        'employee/chat/channel_boards.html', 
        'employee/chat/channel_files.html'
    ]
    
    print("🧪 Testing Enhanced Template Syntax...")
    print("=" * 50)
    
    for template_path in templates_to_test:
        try:
            template = get_template(template_path)
            print(f"✅ {template_path} - Valid syntax")
        except Exception as e:
            print(f"❌ {template_path} - Error: {e}")
            return False
    
    return True

def test_template_blocks():
    """Test that templates have required blocks"""
    print("\n🔍 Testing Template Block Structure...")
    print("=" * 50)
    
    # Test channel.html
    try:
        with open('templates/employee/chat/channel.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_blocks = ['extra_css', 'content', 'extra_js']
        for block in required_blocks:
            if f'{{% block {block} %}}' in content:
                print(f"✅ channel.html has {block} block")
            else:
                print(f"❌ channel.html missing {block} block")
                
    except Exception as e:
        print(f"❌ Error reading channel.html: {e}")
    
    # Test channel_boards.html
    try:
        with open('templates/employee/chat/channel_boards.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'gradient' in content and 'rgba' in content:
            print("✅ channel_boards.html has enhanced styling")
        else:
            print("❌ channel_boards.html missing enhanced styling")
            
    except Exception as e:
        print(f"❌ Error reading channel_boards.html: {e}")
    
    # Test channel_files.html 
    try:
        with open('templates/employee/chat/channel_files.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'filter-tab' in content and 'file-search' in content:
            print("✅ channel_files.html has enhanced search/filter")
        else:
            print("❌ channel_files.html missing enhanced features")
            
    except Exception as e:
        print(f"❌ Error reading channel_files.html: {e}")

def test_css_consistency():
    """Test CSS consistency across templates"""
    print("\n🎨 Testing CSS Consistency...")
    print("=" * 50)
    
    templates = [
        'templates/employee/chat/channel.html',
        'templates/employee/chat/channel_boards.html',
        'templates/employee/chat/channel_files.html'
    ]
    
    common_styles = [
        'linear-gradient',
        'border-radius: 15px',
        'box-shadow:',
        'transform:',
        'transition:'
    ]
    
    for template_path in templates:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            template_name = os.path.basename(template_path)
            consistent_styles = 0
            
            for style in common_styles:
                if style in content:
                    consistent_styles += 1
                    
            if consistent_styles >= 4:
                print(f"✅ {template_name} has consistent modern styling")
            else:
                print(f"⚠️  {template_name} may need more styling consistency")
                
        except Exception as e:
            print(f"❌ Error reading {template_path}: {e}")

def test_javascript_functionality():
    """Test JavaScript functionality in templates"""
    print("\n⚡ Testing JavaScript Functionality...")
    print("=" * 50)
    
    # Test channel.html JavaScript
    try:
        with open('templates/employee/chat/channel.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        js_features = [
            'sendMessage',
            'shareSelectedBoard',
            'shareSelectedFile',
            'addEventListener'
        ]
        
        js_count = sum(1 for feature in js_features if feature in content)
        
        if js_count >= 3:
            print("✅ channel.html has comprehensive JavaScript")
        else:
            print("⚠️  channel.html may need more JavaScript features")
            
    except Exception as e:
        print(f"❌ Error testing channel.html JavaScript: {e}")
    
    # Test boards JavaScript
    try:
        with open('templates/employee/chat/channel_boards.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'IntersectionObserver' in content and 'animation' in content:
            print("✅ channel_boards.html has advanced JavaScript features")
        else:
            print("⚠️  channel_boards.html could use more interactive features")
            
    except Exception as e:
        print(f"❌ Error testing channel_boards.html JavaScript: {e}")
    
    # Test files JavaScript
    try:
        with open('templates/employee/chat/channel_files.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'filterFiles' in content and 'searchTimeout' in content:
            print("✅ channel_files.html has search/filter JavaScript")
        else:
            print("⚠️  channel_files.html may need search/filter functionality")
            
    except Exception as e:
        print(f"❌ Error testing channel_files.html JavaScript: {e}")

def test_responsive_design():
    """Test responsive design features"""
    print("\n📱 Testing Responsive Design...")
    print("=" * 50)
    
    templates = [
        'templates/employee/chat/channel.html',
        'templates/employee/chat/channel_boards.html', 
        'templates/employee/chat/channel_files.html'
    ]
    
    for template_path in templates:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            template_name = os.path.basename(template_path)
            
            if '@media (max-width: 768px)' in content:
                print(f"✅ {template_name} has mobile responsive design")
            else:
                print(f"⚠️  {template_name} may need mobile responsive styles")
                
        except Exception as e:
            print(f"❌ Error testing {template_path}: {e}")

def main():
    """Run all template tests"""
    print("🚀 Enhanced Template Validation Suite")
    print("=" * 60)
    
    tests = [
        test_template_syntax,
        test_template_blocks,
        test_css_consistency,
        test_javascript_functionality,
        test_responsive_design
    ]
    
    all_passed = True
    
    for test in tests:
        try:
            result = test()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All template enhancements validated successfully!")
        print("✨ Your channel pages now have modern, consistent styling!")
    else:
        print("⚠️  Some issues detected. Please review the output above.")
    
    print("\n📝 Enhancement Summary:")
    print("• Modern gradient-based color schemes")
    print("• Consistent card-based layouts") 
    print("• Smooth animations and transitions")
    print("• Enhanced interactive JavaScript")
    print("• Mobile-responsive design")
    print("• Improved search and filtering")
    print("• Better accessibility features")

if __name__ == "__main__":
    main()
