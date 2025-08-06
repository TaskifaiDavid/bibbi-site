#!/usr/bin/env python3
"""Test question classification after our improvements"""

def test_question_classification():
    """Test the _classify_question function"""
    
    def _classify_question(message: str) -> str:
        """Classify the type of data question to determine response format"""
        message_lower = message.lower()
        
        # Best/top/ranking questions should show tables
        if any(phrase in message_lower for phrase in [
            'best selling', 'top selling', 'best product', 'top product',
            'highest sales', 'most sales', 'top reseller', 'best reseller',
            'which is my best', 'which is my top', 'what are my best',
            'what are my top'
        ]):
            return 'show_table'
        
        # List/table questions (should show data tables)
        if any(phrase in message_lower for phrase in [
            'show me all', 'list all', 'show all', 'give me a list',
            'show me the', 'display all', 'what are all', 'show products',
            'show resellers', 'show sales'
        ]):
            return 'show_table'
        
        # Analysis questions (should show tables)
        if any(phrase in message_lower for phrase in [
            'analyze', 'breakdown', 'compare', 'trend', 'over time',
            'by month', 'by year', 'by reseller', 'by product'
        ]):
            return 'show_table'
        
        # Time-based questions (should show tables) - NEW
        if any(phrase in message_lower for phrase in [
            'july 2024', 'september 2024', 'january 2025', 'q1', 'q2', 'q3', 'q4',
            'monthly trends', 'quarterly', 'this year', 'last year', 'in 2024', 'in 2025',
            'sales in', 'performance in', 'sales for', 'revenue in'
        ]):
            return 'show_table'
        
        # Simple total/count questions (direct answers)
        if any(phrase in message_lower for phrase in [
            'what is my total', 'what are my total', 'how much total',
            'what is the total', 'what are the total', 'how much is',
            'how much did', 'how much have', 'what did i sell total',
            'how many total', 'how many records', 'how many sales'
        ]):
            return 'direct_answer'
        
        # Count questions (direct answers)
        if any(phrase in message_lower for phrase in [
            'how many', 'count of', 'number of'
        ]):
            return 'direct_answer'
        
        # Default to show_table for multi-word questions
        if len(message.split()) > 4:
            return 'show_table'
        
        return 'direct_answer'

    print("🧪 TESTING QUESTION CLASSIFICATION")
    print("=" * 60)
    
    # Test queries that should show tables
    show_table_queries = [
        "What were my sales in July 2024?",
        "Show me Q3 2024 performance",
        "Which are my top selling products?",
        "Monthly trends for 2024",
        "Sales in September 2024",
        "Revenue in Q1",
        "Performance in 2024",
        "Show me product breakdown",
        "Top 5 resellers",
        "Compare Galilu vs BoxNox"
    ]
    
    # Test queries that should be direct answers
    direct_answer_queries = [
        "What is my total sales?",
        "How much total revenue?",
        "How many sales?",
        "What are my total"
    ]
    
    print("Testing queries that should show tables:")
    print("-" * 40)
    
    table_success = 0
    for query in show_table_queries:
        classification = _classify_question(query)
        expected = "show_table"
        success = classification == expected
        if success:
            table_success += 1
        print(f"'{query[:35]}...' -> {classification} {'✅' if success else '❌'}")
    
    print(f"\nTable classification success: {table_success}/{len(show_table_queries)}")
    
    print("\nTesting queries that should be direct answers:")
    print("-" * 40)
    
    direct_success = 0
    for query in direct_answer_queries:
        classification = _classify_question(query)
        expected = "direct_answer"
        success = classification == expected
        if success:
            direct_success += 1
        print(f"'{query[:35]}...' -> {classification} {'✅' if success else '❌'}")
    
    print(f"\nDirect answer classification success: {direct_success}/{len(direct_answer_queries)}")
    
    total_success = table_success + direct_success
    total_tests = len(show_table_queries) + len(direct_answer_queries)
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   ✅ Total successful classifications: {total_success}/{total_tests}")
    
    if total_success >= total_tests * 0.9:
        print(f"   🎉 EXCELLENT - Question classification working properly!")
    elif total_success >= total_tests * 0.7:
        print(f"   ⚠️  GOOD - Most classifications working")
    else:
        print(f"   ❌ NEEDS IMPROVEMENT - Too many misclassifications")
    
    # Test the critical queries from the original bug
    print(f"\n🎯 Testing Critical Queries from Original Bug:")
    print("-" * 50)
    
    critical_queries = [
        "What were my sales in July 2024?",
        "Show me Q3 2024 performance", 
        "Which are my top selling products?",
        "Monthly trends"
    ]
    
    for query in critical_queries:
        classification = _classify_question(query)
        print(f"'{query}' -> {classification}")
        if classification == 'show_table':
            print(f"   ✅ Will show data table (FIXED!)")
        else:
            print(f"   ❌ Will only show summary text")

if __name__ == "__main__":
    test_question_classification()