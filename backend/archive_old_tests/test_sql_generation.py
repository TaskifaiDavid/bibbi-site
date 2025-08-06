#!/usr/bin/env python3
"""Test SQL generation without requiring external packages"""

import sys
import os
import re
from datetime import datetime

# Mock minimal dependencies
class MockLogger:
    def error(self, msg, **kwargs): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

# Mock required modules
sys.modules['openai'] = type(sys)('openai')
sys.modules['app'] = type(sys)('app')
sys.modules['app.services'] = type(sys)('app.services')
sys.modules['app.services.db_service'] = type(sys)('app.services.db_service')
sys.modules['app.utils'] = type(sys)('app.utils')
sys.modules['app.utils.config'] = type(sys)('app.utils.config')
sys.modules['app.utils.exceptions'] = type(sys)('app.utils.exceptions')

class MockDatabaseService:
    pass

class MockSettings:
    openai_api_key = "test"
    openai_model = "gpt-4"

class MockAppException(Exception):
    pass

# Add mock modules to sys.modules
sys.modules['app.services.db_service'].DatabaseService = MockDatabaseService
sys.modules['app.utils.config'].get_settings = lambda: MockSettings()
sys.modules['app.utils.exceptions'].AppException = MockAppException

# Now we can import our chat service
from app.services.chat_service import ChatService

def test_sql_generation():
    """Test the SQL generation logic"""
    print("🚀 TESTING SQL GENERATION LOGIC")
    print("=" * 60)
    
    # Create a simplified chat service for testing
    class TestChatService(ChatService):
        def __init__(self):
            # Skip the full initialization
            pass
        
        def _load_system_prompt(self):
            return "test prompt"
    
    chat_service = TestChatService()
    
    # Test different types of queries to ensure diverse SQL generation
    test_queries = [
        # Basic sales queries
        ("What are my total sales?", "Should generate basic total sales SQL"),
        ("How much revenue did I generate?", "Should generate basic total sales SQL"),
        
        # Temporal queries  
        ("What were my sales in July 2024?", "Should generate time-filtered SQL with month=7, year=2024"),
        ("Show me Q3 2024 performance", "Should generate quarterly SQL for Q3"),
        ("Monthly trends for 2024", "Should generate monthly trends SQL"),
        
        # Product queries
        ("Which are my top selling products?", "Should generate product analysis SQL"),
        ("Show me product breakdown", "Should generate product analysis SQL"),
        ("Performance of BIBBI products", "Should filter by BIBBI products"),
        
        # Reseller queries
        ("Who are my top 5 customers?", "Should generate reseller analysis with LIMIT 5"),
        ("Compare Galilu vs BoxNox", "Should generate comparative analysis"),
        ("Reseller performance breakdown", "Should generate reseller analysis SQL"),
        
        # Advanced queries
        ("What's my average order value?", "Should generate average price SQL"),
        ("Year over year growth", "Should generate yearly analysis SQL"),
    ]
    
    print("Testing SQL generation for different query types:")
    print("-" * 60)
    
    for i, (query, expected_behavior) in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print(f"   Expected: {expected_behavior}")
        
        try:
            # Test the enhanced natural language processing
            enhanced = chat_service._enhance_natural_language(query)
            print(f"   Enhanced: '{enhanced}'")
            
            # Test parameter extraction
            params = chat_service._extract_query_parameters(enhanced, query)
            print(f"   Parameters: {params}")
            
            # Test SQL generation
            sql_query = chat_service._generate_sql_from_intent(enhanced, query)
            
            # Clean up the SQL for display
            sql_clean = re.sub(r'\s+', ' ', sql_query.strip())
            sql_clean = sql_clean.replace('\n', ' ')
            
            print(f"   Generated SQL: {sql_clean}")
            
            # Verify it's a valid SELECT query
            if sql_clean.upper().strip().startswith('SELECT'):
                print(f"   ✅ Valid SELECT query generated")
            else:
                print(f"   ❌ Invalid query generated")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'=' * 60}")
    print("🎯 SQL GENERATION TEST COMPLETE")
    print("=" * 60)
    
    # Test that different queries generate different SQL patterns
    print("\n🔍 Testing SQL Diversity:")
    print("-" * 40)
    
    diverse_queries = [
        "What are my total sales?",
        "What were my sales in July 2024?", 
        "Which are my top selling products?",
        "Who are my top customers?",
        "Show me monthly trends"
    ]
    
    generated_sqls = []
    for query in diverse_queries:
        try:
            enhanced = chat_service._enhance_natural_language(query)
            sql = chat_service._generate_sql_from_intent(enhanced, query)
            # Extract key parts of the SQL to compare
            sql_signature = re.sub(r'\s+', ' ', sql.strip().split('WHERE')[0])
            generated_sqls.append(sql_signature)
            print(f"'{query}' -> {sql_signature[:100]}...")
        except Exception as e:
            print(f"'{query}' -> ERROR: {e}")
    
    # Check if we got diverse SQL patterns
    unique_patterns = len(set(generated_sqls))
    total_queries = len(diverse_queries)
    
    print(f"\n📊 SQL Diversity Results:")
    print(f"   Unique SQL patterns: {unique_patterns}/{total_queries}")
    if unique_patterns >= 4:
        print(f"   ✅ Good diversity - Different queries generate different SQL!")
    elif unique_patterns >= 2:
        print(f"   ⚠️  Some diversity - Could be improved")
    else:
        print(f"   ❌ Poor diversity - Same SQL being generated for different queries")
    
    print(f"\n🎉 Testing completed!")

if __name__ == "__main__":
    test_sql_generation()