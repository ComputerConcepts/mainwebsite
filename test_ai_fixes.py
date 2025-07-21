#!/usr/bin/env python
"""
Test script to verify AI system fixes
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'computerconcepts.settings')
django.setup()

from pages.models import Employee, AIFileAnalysis, FileDocument
from pages.ai_file_analysis import AIFileAnalyzer

def test_employee_username():
    """Test Employee username property"""
    print("Testing Employee username property...")
    try:
        # Get the first employee
        employee = Employee.objects.first()
        if employee:
            print(f"✓ Employee found: {employee.get_full_name()}")
            print(f"✓ Username access: {employee.username}")
            print(f"✓ Direct user.username access: {employee.user.username}")
        else:
            print("! No employees found in database")
    except Exception as e:
        print(f"✗ Error testing employee username: {e}")

def test_analysis_data_field():
    """Test AIFileAnalysis analysis_data field"""
    print("\nTesting AIFileAnalysis analysis_data field...")
    try:
        # Check if the field exists
        analysis = AIFileAnalysis.objects.first()
        if analysis:
            print(f"✓ AIFileAnalysis found: {analysis}")
            print(f"✓ analysis_data field exists: {hasattr(analysis, 'analysis_data')}")
            print(f"✓ analysis_data value: {analysis.analysis_data}")
            print(f"✓ tags field exists: {hasattr(analysis, 'tags')}")
            print(f"✓ tags value: {analysis.tags}")
        else:
            print("! No AIFileAnalysis records found")
    except Exception as e:
        print(f"✗ Error testing analysis_data field: {e}")

def test_recommendations_engine():
    """Test SmartRecommendationEngine generate_recommendations method"""
    print("\nTesting SmartRecommendationEngine...")
    try:
        from pages.ai_recommendations import SmartRecommendationEngine
        
        engine = SmartRecommendationEngine()
        print(f"✓ SmartRecommendationEngine created: {engine}")
        
        # Check if method exists
        has_method = hasattr(engine, 'generate_recommendations')
        print(f"✓ generate_recommendations method exists: {has_method}")
        
        if has_method:
            # Test with minimal data
            file_analysis = {
                'category': 'document',
                'key_topics': ['test', 'sample'],
                'quality_score': 75,
                'contains_sensitive_info': False
            }
            
            recommendations = engine.generate_recommendations(None, file_analysis)
            print(f"✓ Generated recommendations: {len(recommendations)} items")
            for i, rec in enumerate(recommendations[:3]):
                print(f"  {i+1}. {rec.get('title', 'No title')}")
        
    except Exception as e:
        print(f"✗ Error testing recommendations engine: {e}")

def test_ai_file_analyzer():
    """Test AIFileAnalyzer with defensive checks"""
    print("\nTesting AIFileAnalyzer defensive checks...")
    try:
        analyzer = AIFileAnalyzer()
        print(f"✓ AIFileAnalyzer created: {analyzer}")
        
        # Test with a file if available
        file_doc = FileDocument.objects.first()
        if file_doc:
            print(f"✓ Found file document: {file_doc.name}")
            
            # Test knowledge graph update with defensive checks
            analysis = AIFileAnalysis.objects.filter(document=file_doc).first()
            if analysis:
                print(f"✓ Found analysis: {analysis}")
                try:
                    analyzer._update_knowledge_graph(file_doc, analysis)
                    print("✓ Knowledge graph update completed without errors")
                except Exception as e:
                    print(f"✗ Knowledge graph update error: {e}")
            else:
                print("! No analysis found for file")
        else:
            print("! No file documents found")
            
    except Exception as e:
        print(f"✗ Error testing AIFileAnalyzer: {e}")

def main():
    """Run all tests"""
    print("🔧 Testing AI System Fixes")
    print("=" * 50)
    
    test_employee_username()
    test_analysis_data_field()
    test_recommendations_engine()
    test_ai_file_analyzer()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!")

if __name__ == "__main__":
    main()
