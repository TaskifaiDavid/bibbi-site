#!/usr/bin/env python3
"""Simple test of intent detection patterns"""

def test_flexible_patterns():
    """Test the flexible pattern matching logic"""
    
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
        if result:
            print(f"🛍️ PRODUCT ANALYSIS: product={has_product or has_product_orig}, analysis={has_analysis or has_analysis_orig}")
        return result
    
    def _is_reseller_analysis_query(enhanced_lower: str, original_lower: str) -> bool:
        """Check if this is a reseller analysis query"""
        reseller_words = ['reseller', 'resellers', 'customer', 'customers', 'client', 'clients']
        analysis_words = ['top', 'best', 'breakdown', 'analysis', 'which', 'who']
        
        has_reseller = any(word in enhanced_lower for word in reseller_words) or any(word in original_lower for word in reseller_words)
        has_analysis = any(word in enhanced_lower for word in analysis_words) or any(word in original_lower for word in analysis_words)
        
        result = has_reseller and has_analysis
        if result:
            print(f"👥 RESELLER ANALYSIS: reseller={has_reseller}, analysis={has_analysis}")
        return result

    print("🧪 TESTING FLEXIBLE INTENT PATTERNS")
    print("=" * 60)
    
    test_cases = [
        # Product queries that should match
        ("Which are my top products?", "which are my top products?", "PRODUCT", True),
        ("What are my best selling items?", "what are my best selling items?", "PRODUCT", True),
        ("Show me product breakdown", "show me product breakdown", "PRODUCT", True),
        ("Top products please", "top products please", "PRODUCT", True),
        
        # Reseller queries that should match
        ("Who are my top customers?", "who are my top customers?", "RESELLER", True),
        ("Which are my best resellers?", "which are my best resellers?", "RESELLER", True),
        ("Show me customer breakdown", "show me customer breakdown", "RESELLER", True),
        
        # Queries that should NOT match
        ("What's my total sales?", "what's my total sales?", "PRODUCT", False),
        ("Hello there", "hello there", "PRODUCT", False),
        ("Random question", "random question", "RESELLER", False),
    ]
    
    successful_tests = 0
    
    for i, (original, enhanced, query_type, should_match) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{original}'")
        print(f"   Type: {query_type}, Should match: {should_match}")
        
        if query_type == "PRODUCT":
            result = _is_product_analysis_query(enhanced, original)
        elif query_type == "RESELLER":
            result = _is_reseller_analysis_query(enhanced, original)
        
        if result == should_match:
            print(f"   ✅ CORRECT: Pattern matching worked as expected")
            successful_tests += 1
        else:
            print(f"   ❌ INCORRECT: Expected {should_match}, got {result}")
    
    print(f"\n{'=' * 60}")
    print(f"🎯 PATTERN MATCHING RESULTS")
    print(f"✅ Successful tests: {successful_tests}/{len(test_cases)}")
    
    if successful_tests >= len(test_cases) * 0.9:
        print(f"🎉 EXCELLENT! Flexible patterns are working correctly!")
    elif successful_tests >= len(test_cases) * 0.7:
        print(f"⚠️ GOOD! Most patterns working, some tweaks needed")
    else:
        print(f"❌ POOR! Pattern matching needs more work")

if __name__ == "__main__":
    test_flexible_patterns()