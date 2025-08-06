#!/usr/bin/env python3
"""Test the flexible intent detection to verify different questions generate different SQL"""

# Mock setup
class MockLogger:
    def error(self, msg, **kwargs): pass

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock required modules
sys.modules['openai'] = type(sys)('openai')
sys.modules['app'] = type(sys)('app')
sys.modules['app.services'] = type(sys)('app.services')
sys.modules['app.services.db_service'] = type(sys)('app.services.db_service')
sys.modules['app.utils'] = type(sys)('app.utils')
sys.modules['app.utils.config'] = type(sys)('app.utils.config')
sys.modules['app.utils.exceptions'] = type(sys)('app.utils.exceptions')

class MockSettings:
    openai_api_key = "test"
    openai_model = "gpt-4"

sys.modules['app.services.db_service'].DatabaseService = type('MockDB', (), {})
sys.modules['app.utils.config'].get_settings = lambda: MockSettings()
sys.modules['app.utils.exceptions'].AppException = Exception

def test_flexible_intent_detection():
    """Test that different questions now generate different SQL queries"""
    print("🚀 TESTING FLEXIBLE INTENT DETECTION")
    print("=" * 70)
    
    # Import after mocking
    from app.services.chat_service import ChatService
    
    # Create test chat service
    class TestChatService(ChatService):
        def __init__(self):
            pass  # Skip initialization
        
        def _load_system_prompt(self):
            return "test"
    
    chat_service = TestChatService()
    
    # Test different query variations that should match different intents
    test_queries = [
        # Product queries - should match product analysis
        ("Which are my top products?", "Product Analysis"),
        ("What are my best selling items?", "Product Analysis"),
        ("Show me product breakdown", "Product Analysis"),
        ("What products sell the most?", "Product Analysis"),
        
        # Reseller queries - should match reseller analysis
        ("Who are my top customers?", "Reseller Analysis"),
        ("Which are my best resellers?", "Reseller Analysis"),
        ("Show me customer breakdown", "Reseller Analysis"),
        ("Who are my biggest clients?", "Reseller Analysis"),
        
        # Time queries - should match time analysis
        ("What were my sales in 2024?", "Time Analysis"),
        ("Show me monthly trends", "Time Analysis"),
        ("Monthly breakdown please", "Time Analysis"),
        ("Year over year analysis", "Time Analysis"),
        
        # Comparison queries
        ("Compare Galilu vs BoxNox", "Comparison"),
        ("Show Galilu versus BoxNox", "Comparison"),
        
        # Should fall back to basic total
        ("What's my total sales?", "Total Sales (expected fallback)"),
        ("Hello there", "Total Sales (expected fallback)"),
    ]
    
    generated_queries = []
    successful_matches = 0
    
    print("Testing intent detection and SQL generation:")
    print("-" * 70)
    
    for i, (query, expected_intent) in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print(f"   Expected Intent: {expected_intent}")
        
        try:
            # Test enhancement
            enhanced = chat_service._enhance_natural_language(query)
            
            # Test SQL generation with debug output
            sql_query = chat_service._generate_sql_from_intent(enhanced, query)
            
            # Extract key SQL pattern for comparison
            sql_signature = sql_query.strip().split('\n')[0].strip()
            generated_queries.append((query, sql_signature))
            
            print(f"   Generated SQL: {sql_signature}")
            
            # Check if it's generating the expected type
            if "SELECT functional_name" in sql_query and "product" in expected_intent.lower():
                print(f"   ✅ Correctly matched product intent")
                successful_matches += 1
            elif "SELECT reseller" in sql_query and "reseller" in expected_intent.lower():
                print(f"   ✅ Correctly matched reseller intent")
                successful_matches += 1
            elif "SELECT year, month" in sql_query and "time" in expected_intent.lower():
                print(f"   ✅ Correctly matched time intent")
                successful_matches += 1
            elif "SELECT SUM(sales_eur) AS total_sales_eur" in sql_query and "total" in expected_intent.lower():
                print(f"   ✅ Correctly used fallback")
                successful_matches += 1
            else:
                print(f"   ⚠️ Unexpected SQL pattern for expected intent")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'=' * 70}")
    print("🎯 INTENT DETECTION RESULTS")
    print("=" * 70)
    
    # Check for SQL diversity
    unique_sql_patterns = len(set(sql for _, sql in generated_queries))
    total_queries = len(generated_queries)
    
    print(f"✅ Successful intent matches: {successful_matches}/{len(test_queries)}")
    print(f"✅ Unique SQL patterns generated: {unique_sql_patterns}/{total_queries}")
    
    # Show the diversity
    print(f"\n📋 SQL Pattern Diversity:")
    print("-" * 50)
    
    seen_patterns = set()
    for i, (query, sql) in enumerate(generated_queries, 1):
        if sql not in seen_patterns:
            print(f"{len(seen_patterns) + 1}. {sql[:60]}...")
            seen_patterns.add(sql)
    
    # Final assessment
    if unique_sql_patterns >= 4:
        print(f"\n🎉 EXCELLENT! Intent detection is working properly!")
        print(f"   Different questions now generate different SQL queries!")
        print(f"   The 'same query for different questions' bug is FIXED!")
    elif unique_sql_patterns >= 2:
        print(f"\n⚠️ GOOD! Some diversity achieved, but could be improved")
    else:
        print(f"\n❌ POOR! Still generating the same SQL for most queries")
    
    print(f"\n🔍 Test completed!")

if __name__ == "__main__":
    test_flexible_intent_detection()