#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced chat system
Consolidates all chat-related tests into one organized file
"""
import os
import sys
import asyncio
import pytest
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock settings for testing
class MockSettings:
    openai_api_key = "test-key"
    openai_model = "gpt-4"
    supabase_url = "https://test.supabase.co"
    supabase_key = "test-key"

class TestChatConfiguration:
    """Test chat system configuration and setup"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        from app.utils.config import get_settings
        settings = get_settings()
        
        assert settings is not None
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'openai_model')
        assert hasattr(settings, 'supabase_url')
        
    def test_required_imports(self):
        """Test that all required packages can be imported"""
        try:
            import langchain
            import langchain_openai
            import langchain_community
            import supabase
            import fastapi
            assert True
        except ImportError as e:
            pytest.fail(f"Required package missing: {e}")

class TestIntentDetection:
    """Test intent detection and question classification"""
    
    def test_intent_patterns(self):
        """Test intent detection patterns"""
        
        def _analyze_question_intent(user_message):
            """Analyze user's question to understand their intent"""
            message_lower = user_message.lower()
            
            # Time-based queries
            if any(word in message_lower for word in ['year', 'month', 'quarterly', '2023', '2024', '2025', 'monthly', 'yearly', 'trend']):
                return "TIME_ANALYSIS"
            
            # Reseller/Customer analysis
            elif any(word in message_lower for word in ['reseller', 'customer', 'client', 'who', 'which reseller', 'top reseller', 'best reseller', 'highest']):
                return "RESELLER_ANALYSIS"
            
            # Product analysis
            elif any(word in message_lower for word in ['product', 'item', 'ean', 'functional_name', 'best selling', 'top selling']):
                return "PRODUCT_ANALYSIS"
            
            # Total/summary queries
            elif any(word in message_lower for word in ['total', 'sum', 'overall', 'all', 'entire']):
                return "TOTAL_SUMMARY"
            
            # Comparison queries
            elif any(word in message_lower for word in ['compare', 'vs', 'versus', 'difference', 'higher', 'lower', 'best', 'worst', 'against', 'between', 'than']):
                return "COMPARISON"
            
            else:
                return "GENERAL_INQUIRY"
        
        # Test cases
        test_cases = [
            ("What were my sales in 2024?", "TIME_ANALYSIS"),
            ("Show me monthly trends", "TIME_ANALYSIS"),
            ("Who is my top reseller?", "RESELLER_ANALYSIS"),
            ("Which customer bought the most?", "RESELLER_ANALYSIS"),
            ("What are my best selling products?", "PRODUCT_ANALYSIS"),
            ("Show me product breakdown", "PRODUCT_ANALYSIS"),
            ("What's my total revenue?", "TOTAL_SUMMARY"),
            ("Compare 2024 vs 2023", "COMPARISON"),
            ("How are sales performing?", "GENERAL_INQUIRY")
        ]
        
        for question, expected_intent in test_cases:
            actual_intent = _analyze_question_intent(question)
            assert actual_intent == expected_intent, f"Question '{question}' should be '{expected_intent}' but got '{actual_intent}'"
    
    def test_flexible_pattern_matching(self):
        """Test flexible pattern matching for different phrasings"""
        
        def _is_product_analysis_query(enhanced_lower: str, original_lower: str) -> bool:
            """Check if this is a product analysis query with flexible matching"""
            product_words = ['product', 'products', 'item', 'items', 'functional_name']
            analysis_words = ['top', 'best', 'breakdown', 'selling', 'analysis', 'which', 'what']
            
            has_product = any(word in enhanced_lower for word in product_words)
            has_analysis = any(word in enhanced_lower for word in analysis_words)
            
            # Also check original message for different phrasing
            has_product_orig = any(word in original_lower for word in product_words)
            has_analysis_orig = any(word in original_lower for word in analysis_words)
            
            return (has_product and has_analysis) or (has_product_orig and has_analysis_orig)
        
        test_cases = [
            ("What are my top products?", "what are my top products?", True),
            ("Show me product breakdown", "show me product breakdown", True),
            ("Which items sell best?", "which items sell best?", True),
            ("Total sales amount", "total sales amount", False),
        ]
        
        for enhanced, original, expected in test_cases:
            result = _is_product_analysis_query(enhanced.lower(), original.lower())
            assert result == expected, f"Query '{original}' should return {expected} but got {result}"

class TestConversationMemory:
    """Test conversation memory functionality"""
    
    @patch('app.services.db_service.DatabaseService')
    def test_conversation_memory_service(self, mock_db_service):
        """Test conversation memory service initialization"""
        from app.api.chat import ConversationMemoryService
        
        memory_service = ConversationMemoryService()
        assert memory_service is not None
        assert hasattr(memory_service, 'memory_cache')
        assert hasattr(memory_service, 'get_conversation_memory')
    
    def test_memory_window_size(self):
        """Test that memory window size is configured correctly"""
        from langchain.memory import ConversationBufferWindowMemory
        
        memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Add more than window size messages
        for i in range(15):
            memory.chat_memory.add_user_message(f"User message {i}")
            memory.chat_memory.add_ai_message(f"AI response {i}")
        
        # Should only keep the last 10 messages (window size)
        assert len(memory.chat_memory.messages) <= 10

class TestDatabaseIntegration:
    """Test database integration and queries"""
    
    @patch('app.services.db_service.DatabaseService')
    def test_supabase_connection(self, mock_db_service):
        """Test Supabase connection and basic queries"""
        # Mock the database service
        mock_instance = Mock()
        mock_instance.supabase.table.return_value.select.return_value.execute.return_value.data = []
        mock_db_service.return_value = mock_instance
        
        from app.api.chat import SupabaseSQLDatabase
        db = SupabaseSQLDatabase()
        
        result = db.run("SELECT 1")
        assert result is not None
    
    def test_query_type_detection(self):
        """Test SQL query type detection"""
        
        def detect_query_type(query: str) -> str:
            """Detect the type of SQL query"""
            query_lower = query.lower().strip()
            
            if 'reseller' in query_lower and ('group by reseller' in query_lower or 'reseller,' in query_lower):
                return 'reseller'
            elif 'functional_name' in query_lower or 'product' in query_lower:
                return 'product'
            elif 'sum(' in query_lower or 'total' in query_lower:
                return 'summary'
            else:
                return 'general'
        
        test_queries = [
            ("SELECT reseller, SUM(sales_eur) FROM sellout_entries2 GROUP BY reseller", "reseller"),
            ("SELECT functional_name, COUNT(*) FROM sellout_entries2 GROUP BY functional_name", "product"),
            ("SELECT SUM(sales_eur) as total FROM sellout_entries2", "summary"),
            ("SELECT * FROM sellout_entries2 LIMIT 10", "general")
        ]
        
        for query, expected_type in test_queries:
            result = detect_query_type(query)
            assert result == expected_type, f"Query type detection failed for: {query}"

class TestChatEndpoints:
    """Test chat API endpoints"""
    
    @patch('app.services.auth_service.AuthService')
    async def test_chat_endpoint_structure(self, mock_auth_service):
        """Test that chat endpoints have proper structure"""
        from app.api.chat import ChatRequest, ChatResponse, ConversationHistoryResponse
        
        # Test request model
        request = ChatRequest(message="Test message", session_id="test-session")
        assert request.message == "Test message"
        assert request.session_id == "test-session"
        
        # Test response model
        response = ChatResponse(answer="Test answer", session_id="test-session")
        assert response.answer == "Test answer"
        assert response.session_id == "test-session"
        
        # Test history response model
        history_response = ConversationHistoryResponse(conversations=[], total_messages=0)
        assert history_response.conversations == []
        assert history_response.total_messages == 0

class TestErrorHandling:
    """Test error handling in chat system"""
    
    def test_graceful_error_handling(self):
        """Test that errors are handled gracefully"""
        from app.api.chat import SupabaseChatAgent
        from langchain_openai import ChatOpenAI
        
        # Mock components
        mock_llm = Mock(spec=ChatOpenAI)
        mock_db = Mock()
        
        agent = SupabaseChatAgent(mock_llm, mock_db)
        
        # Test with invalid input
        result = agent.invoke({"input": "", "user_id": None})
        assert result is not None
        assert "output" in result

def run_tests():
    """Run all tests manually without pytest"""
    print("🧪 Running Chat System Tests")
    print("=" * 50)
    
    # Test configuration
    config_test = TestChatConfiguration()
    try:
        config_test.test_config_loading()
        print("✅ Configuration loading test passed")
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
    
    try:
        config_test.test_required_imports()
        print("✅ Required imports test passed")
    except Exception as e:
        print(f"❌ Required imports test failed: {e}")
    
    # Test intent detection
    intent_test = TestIntentDetection()
    try:
        intent_test.test_intent_patterns()
        print("✅ Intent detection test passed")
    except Exception as e:
        print(f"❌ Intent detection test failed: {e}")
    
    try:
        intent_test.test_flexible_pattern_matching()
        print("✅ Flexible pattern matching test passed")
    except Exception as e:
        print(f"❌ Flexible pattern matching test failed: {e}")
    
    # Test database integration
    db_test = TestDatabaseIntegration()
    try:
        db_test.test_query_type_detection()
        print("✅ Query type detection test passed")
    except Exception as e:
        print(f"❌ Query type detection test failed: {e}")
    
    print("\n🎉 Chat system tests completed!")

if __name__ == "__main__":
    run_tests()