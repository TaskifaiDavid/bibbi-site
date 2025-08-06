#!/usr/bin/env python3
"""Test complex queries with the enhanced chat system"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.chat_service import ChatService

async def test_complex_queries():
    """Test the enhanced chat system with complex business queries"""
    try:
        print("🚀 Testing enhanced chat system with complex queries...")
        
        chat_service = ChatService()
        test_user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Test various complex business scenarios
        complex_queries = [
            # Temporal Analysis
            "What were my sales in Q3 2024?",
            "Compare my sales this year vs last year",
            "Show me monthly trends for 2024",
            "How did January 2025 perform compared to January 2024?",
            
            # Advanced Product Analysis
            "Which products are my best sellers?", 
            "What's the performance of BIBBI products?",
            "Show me product breakdown by revenue and quantity",
            "Which items have declining sales?",
            
            # Reseller/Customer Analysis
            "Who are my top 5 customers by revenue?",
            "Which resellers haven't ordered recently?",
            "Compare Galilu vs BoxNox performance",
            "Show me reseller analysis with transaction counts",
            
            # Complex Business Questions
            "What's my average order value?",
            "How many different products did I sell?",
            "What's my total revenue and unit sales?",
            "Show me a breakdown by reseller and month",
            
            # Date Format Variations
            "Sales for December 2024",
            "Revenue in 12/2024", 
            "Performance for winter 2024",
            "Show me spring sales data"
        ]
        
        for i, query in enumerate(complex_queries, 1):
            print(f"\n{'='*60}")
            print(f"{i}. TESTING: '{query}'")
            print('='*60)
            
            try:
                # Test the enhanced natural language processing
                enhanced_msg = chat_service._enhance_natural_language(query)
                print(f"📝 Enhanced: '{query}' → '{enhanced_msg}'")
                
                # Test intent detection
                intent = chat_service._detect_message_intent(query)
                print(f"🎯 Intent: {intent}")
                
                if intent == 'data_query':
                    # Test question classification
                    question_type = chat_service._classify_question(query)
                    print(f"🤖 Question Type: {question_type}")
                
                # Process the full query
                result = await chat_service.process_query(
                    user_id=test_user_id,
                    message=query,
                    session_id=None
                )
                
                print(f"✅ Success: {result.get('success')}")
                if result.get('sql_query'):
                    print(f"🔧 SQL Generated:")
                    print(f"   {result.get('sql_query')}")
                    print(f"📊 Results: {result.get('results_count')} rows")
                
                if result.get('error'):
                    print(f"❌ Error: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        print(f"\n{'='*60}")
        print("🎯 Complex query testing completed!")
        print('='*60)
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complex_queries())