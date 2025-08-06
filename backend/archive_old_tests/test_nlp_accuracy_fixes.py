#!/usr/bin/env python3
"""Test the NLP accuracy fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_query_detection_fixes():
    """Test the database service query detection fixes"""
    print("🧪 TESTING QUERY DETECTION FIXES")
    print("=" * 60)
    
    # Import after path setup
    from app.services.db_service import DatabaseService
    
    db_service = DatabaseService()
    
    # Test cases
    test_cases = [
        # Reseller queries that should NOT be detected as product queries
        {
            'query': 'SELECT reseller, SUM(sales_eur) AS total_sales FROM sellout_entries2 se JOIN uploads u ON se.upload_id = u.id WHERE u.user_id = %s GROUP BY reseller ORDER BY total_sales DESC LIMIT 5;',
            'expected_type': 'reseller',
            'description': 'Top 5 resellers query'
        },
        {
            'query': 'SELECT reseller, COUNT(*) FROM sellout_entries2 GROUP BY reseller',
            'expected_type': 'reseller', 
            'description': 'Reseller count query'
        },
        # Product queries
        {
            'query': 'SELECT functional_name, SUM(sales_eur) FROM sellout_entries2 GROUP BY functional_name',
            'expected_type': 'product',
            'description': 'Product sales query'
        },
        # Time queries
        {
            'query': 'SELECT year, month, SUM(sales_eur) FROM sellout_entries2 WHERE year = 2024 GROUP BY year, month',
            'expected_type': 'time',
            'description': 'Time-based query for 2024'
        }
    ]
    
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        query_upper = test_case['query'].upper()
        expected = test_case['expected_type']
        description = test_case['description']
        
        print(f"\n{i}. Testing: {description}")
        print(f"   Query: {test_case['query'][:80]}...")
        
        # Test detection methods
        is_reseller = db_service._is_reseller_analysis_query(query_upper)
        is_product = db_service._is_product_analysis_query(query_upper)
        is_time = db_service._is_time_based_query(query_upper)
        
        detected_type = None
        if is_reseller:
            detected_type = 'reseller'
        elif is_product:
            detected_type = 'product'
        elif is_time:
            detected_type = 'time'
        
        print(f"   Expected: {expected}")
        print(f"   Detected: {detected_type}")
        
        if detected_type == expected:
            print(f"   ✅ CORRECT")
            passed_tests += 1
        else:
            print(f"   ❌ INCORRECT")
            print(f"   Debug: reseller={is_reseller}, product={is_product}, time={is_time}")
    
    print(f"\n{'=' * 60}")
    print(f"🎯 QUERY DETECTION TEST RESULTS")
    print(f"✅ Passed: {passed_tests}/{len(test_cases)}")
    
    if passed_tests == len(test_cases):
        print("🎉 All query detection tests passed!")
        return True
    else:
        print("⚠️ Some query detection tests failed")
        return False

def test_year_parameter_extraction():
    """Test year parameter extraction and application"""
    print(f"\n🧪 TESTING YEAR PARAMETER EXTRACTION")
    print("=" * 60)
    
    # Import after path setup
    from app.services.chat_service import ChatService
    
    chat_service = ChatService()
    
    test_cases = [
        {
            'message': 'what did I sell for 2024?',
            'should_have_year': True,
            'expected_year': 2024
        },
        {
            'message': 'show me sales in 2023',
            'should_have_year': True,
            'expected_year': 2023
        },
        {
            'message': 'what are my total sales?',
            'should_have_year': False,
            'expected_year': None
        }
    ]
    
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case['message']
        should_have_year = test_case['should_have_year']
        expected_year = test_case['expected_year']
        
        print(f"\n{i}. Testing: '{message}'")
        
        # Test parameter extraction
        enhanced_message = chat_service._enhance_natural_language(message)
        params = chat_service._extract_query_parameters(enhanced_message, message)
        
        actual_year = params.get('year')
        
        print(f"   Enhanced: '{enhanced_message}'")
        print(f"   Expected year: {expected_year}")
        print(f"   Extracted year: {actual_year}")
        
        if should_have_year:
            if actual_year == expected_year:
                print(f"   ✅ CORRECT: Year {actual_year} extracted")
                passed_tests += 1
            else:
                print(f"   ❌ INCORRECT: Expected {expected_year}, got {actual_year}")
        else:
            if actual_year is None:
                print(f"   ✅ CORRECT: No year extracted (as expected)")
                passed_tests += 1
            else:
                print(f"   ❌ INCORRECT: Expected no year, got {actual_year}")
    
    print(f"\n{'=' * 60}")
    print(f"🎯 YEAR EXTRACTION TEST RESULTS")
    print(f"✅ Passed: {passed_tests}/{len(test_cases)}")
    
    if passed_tests == len(test_cases):
        print("🎉 All year extraction tests passed!")
        return True
    else:
        print("⚠️ Some year extraction tests failed")
        return False

def test_sql_generation_accuracy():
    """Test that SQL generation produces the expected query types"""
    print(f"\n🧪 TESTING SQL GENERATION ACCURACY")
    print("=" * 60)
    
    # Import after path setup  
    from app.services.chat_service import ChatService
    
    chat_service = ChatService()
    
    test_cases = [
        {
            'message': 'Show me my top 5 resellers',
            'should_contain': ['reseller', 'GROUP BY reseller'],
            'should_not_contain': ['functional_name'],
            'description': 'Reseller query should group by reseller'
        },
        {
            'message': 'what did I sell for 2024?',
            'should_contain': ['year = 2024', 'WHERE'],
            'should_not_contain': [],
            'description': '2024 query should filter by year'
        },
        {
            'message': 'top products',
            'should_contain': ['functional_name', 'GROUP BY functional_name'],
            'should_not_contain': ['reseller'],
            'description': 'Product query should group by functional_name'
        }
    ]
    
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case['message']
        should_contain = test_case['should_contain']
        should_not_contain = test_case['should_not_contain']
        description = test_case['description']
        
        print(f"\n{i}. Testing: '{message}'")
        print(f"   Expectation: {description}")
        
        try:
            # Generate SQL using the enhanced system
            enhanced_message = chat_service._enhance_natural_language(message)
            sql_query = chat_service._generate_sql_from_intent(enhanced_message, message)
            
            sql_upper = sql_query.upper()
            
            print(f"   Generated SQL: {sql_query[:100]}...")
            
            # Check required patterns
            contains_all = all(pattern.upper() in sql_upper for pattern in should_contain)
            contains_none_forbidden = all(pattern.upper() not in sql_upper for pattern in should_not_contain)
            
            if contains_all and contains_none_forbidden:
                print(f"   ✅ CORRECT: SQL matches expected patterns")
                passed_tests += 1
            else:
                print(f"   ❌ INCORRECT: SQL doesn't match expected patterns")
                if not contains_all:
                    missing = [p for p in should_contain if p.upper() not in sql_upper]
                    print(f"   Missing required: {missing}")
                if not contains_none_forbidden:
                    found_forbidden = [p for p in should_not_contain if p.upper() in sql_upper]
                    print(f"   Contains forbidden: {found_forbidden}")
                    
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"🎯 SQL GENERATION TEST RESULTS")
    print(f"✅ Passed: {passed_tests}/{len(test_cases)}")
    
    if passed_tests == len(test_cases):
        print("🎉 All SQL generation tests passed!")
        return True
    else:
        print("⚠️ Some SQL generation tests failed")
        return False

def main():
    """Run all NLP accuracy tests"""
    print("🚀 TESTING NLP ACCURACY FIXES")
    print("=" * 80)
    
    try:
        # Run all tests
        test1_passed = test_query_detection_fixes()
        test2_passed = test_year_parameter_extraction() 
        test3_passed = test_sql_generation_accuracy()
        
        print(f"\n{'=' * 80}")
        print("🎯 OVERALL TEST RESULTS")
        print("=" * 80)
        
        total_passed = sum([test1_passed, test2_passed, test3_passed])
        total_tests = 3
        
        print(f"✅ Query Detection: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Year Extraction: {'PASSED' if test2_passed else 'FAILED'}")
        print(f"✅ SQL Generation: {'PASSED' if test3_passed else 'FAILED'}")
        
        print(f"\n📊 Overall Score: {total_passed}/{total_tests}")
        
        if total_passed == total_tests:
            print("🎉 ALL NLP ACCURACY FIXES WORKING CORRECTLY!")
            print("✅ 'Show me my top 5 resellers' should now return resellers")
            print("✅ '2024' queries should now filter by year 2024") 
            print("✅ Query routing should work accurately")
        else:
            print("⚠️ Some fixes need additional work")
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()