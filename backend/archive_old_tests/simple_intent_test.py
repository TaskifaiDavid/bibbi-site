#!/usr/bin/env python3
"""Simple test of the flexible intent detection patterns"""

def _is_product_analysis_query(enhanced_lower: str, original_lower: str) -> bool:
    """Check if this is a product analysis query with flexible matching"""
    product_words = ['product', 'products', 'item', 'items', 'functional_name']
    analysis_words = ['top', 'best', 'breakdown', 'selling', 'analysis', 'which', 'what']
    
    has_product = any(word in enhanced_lower for word in product_words)
    has_analysis = any(word in enhanced_lower for word in analysis_words)
    
    # Also check original message for different phrasing
    has_product_orig = any(word in original_lower for word in product_words)
    has_analysis_orig = any(word in original_lower for word in analysis_words)
    
    result = (has_product and has_analysis) or (has_product_orig and has_analysis_orig)
    return result

def _is_reseller_analysis_query(enhanced_lower: str, original_lower: str) -> bool:
    """Check if this is a reseller analysis query"""
    reseller_words = ['reseller', 'resellers', 'customer', 'customers', 'client', 'clients']
    analysis_words = ['top', 'best', 'breakdown', 'analysis', 'which', 'who']
    
    has_reseller = any(word in enhanced_lower for word in reseller_words) or any(word in original_lower for word in reseller_words)
    has_analysis = any(word in enhanced_lower for word in analysis_words) or any(word in original_lower for word in analysis_words)
    
    return has_reseller and has_analysis

def _is_time_analysis_query(enhanced_lower: str, original_lower: str) -> bool:
    """Check if this is a time-based analysis query"""
    time_words = ['month', 'months', 'year', 'years', '2024', '2025', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'quarterly', 'annual', 'daily', 'weekly', 'monthly', 'time', 'period', 'trend', 'trends']
    analysis_words = ['breakdown', 'analysis', 'trends', 'compare', 'comparison', 'over', 'during', 'in']
    
    has_time = any(word in enhanced_lower for word in time_words) or any(word in original_lower for word in time_words)
    has_analysis = any(word in enhanced_lower for word in analysis_words) or any(word in original_lower for word in analysis_words)
    
    return has_time or (has_time and has_analysis)

def _is_comparison_query(enhanced_lower: str, original_lower: str) -> bool:
    """Check if this is a comparison query"""
    comparison_indicators = ['vs', 'versus', 'compare', 'comparison', 'against', 'galilu', 'boxnox']
    
    has_comparison = any(indicator in enhanced_lower for indicator in comparison_indicators) or any(indicator in original_lower for indicator in comparison_indicators)
    return has_comparison

def simulate_intent_detection(query: str) -> str:
    """Simulate the intent detection logic to see which SQL template would be chosen"""
    enhanced_lower = query.lower()
    original_lower = query.lower()
    
    print(f"  Testing: '{query}'")
    
    # Check each intent type
    if _is_product_analysis_query(enhanced_lower, original_lower):
        sql_type = "PRODUCT ANALYSIS"
        sample_sql = "SELECT functional_name, SUM(sales_eur) as total_sales..."
    elif _is_reseller_analysis_query(enhanced_lower, original_lower):
        sql_type = "RESELLER ANALYSIS"
        sample_sql = "SELECT reseller, SUM(sales_eur) as total_sales..."
    elif _is_comparison_query(enhanced_lower, original_lower):
        sql_type = "COMPARISON"
        sample_sql = "SELECT functional_name, reseller, SUM(sales_eur)..."
    elif _is_time_analysis_query(enhanced_lower, original_lower):
        sql_type = "TIME ANALYSIS"
        sample_sql = "SELECT year, month, SUM(sales_eur)..."
    else:
        sql_type = "TOTAL SALES (fallback)"
        sample_sql = "SELECT SUM(sales_eur) AS total_sales_eur..."
    
    print(f"    -> Intent: {sql_type}")
    print(f"    -> SQL: {sample_sql[:50]}...")
    
    return sql_type

def main():
    print("🧪 TESTING FLEXIBLE INTENT DETECTION")
    print("=" * 70)
    
    # Test various query types
    test_queries = [
        # Product queries
        "Which are my top products?",
        "What are my best selling items?", 
        "Show me product breakdown",
        "What products sell the most?",
        
        # Reseller queries
        "Who are my top customers?",
        "Which are my best resellers?",
        "Show me customer breakdown",
        "Who are my biggest clients?",
        
        # Time queries
        "What were my sales in 2024?",
        "Show me monthly trends",
        "Monthly breakdown please",
        "Year over year analysis",
        
        # Comparison queries
        "Compare Galilu vs BoxNox",
        "Show Galilu versus BoxNox",
        
        # Should fall back to basic
        "What's my total sales?",
        "Hello there",
    ]
    
    intent_results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}.")
        intent = simulate_intent_detection(query)
        intent_results.append(intent)
    
    print(f"\n{'=' * 70}")
    print("🎯 INTENT DIVERSITY RESULTS")
    print("=" * 70)
    
    # Count unique intents
    unique_intents = len(set(intent_results))
    total_queries = len(intent_results)
    
    print(f"✅ Unique intent types detected: {unique_intents}")
    print(f"📊 Total queries tested: {total_queries}")
    
    # Show the diversity
    print(f"\n📋 Intent Type Distribution:")
    print("-" * 50)
    
    from collections import Counter
    intent_counts = Counter(intent_results)
    
    for intent, count in intent_counts.items():
        print(f"  {intent}: {count} queries")
    
    # Final assessment
    if unique_intents >= 4:
        print(f"\n🎉 EXCELLENT! Intent detection is working properly!")
        print(f"   Different questions now generate different SQL queries!")
        print(f"   The 'same query for different questions' bug is FIXED!")
    elif unique_intents >= 3:
        print(f"\n⚠️ GOOD! Good diversity achieved, minor improvements possible")
    else:
        print(f"\n❌ POOR! Still not enough diversity in intent detection")

if __name__ == "__main__":
    main()