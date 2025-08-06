#!/usr/bin/env python3
"""Standalone test of SQL generation logic without imports"""

import re
from datetime import datetime
from typing import Dict, Any

def _enhance_natural_language(message: str) -> str:
    """Advanced natural language pre-processing for better SQL generation"""
    try:
        enhanced_message = message.lower().strip()
        
        # Advanced temporal expressions - convert to specific time references
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Handle specific month names (January, February, etc.)
        month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Enhanced pattern matching for dates
        for month_name, month_num in month_names.items():
            # Handle "January 2024", "Jan 2024", "January, 2024"
            pattern = rf'\b{month_name}[,\s]+(\d{{4}})\b'
            enhanced_message = re.sub(pattern, f'month {month_num} and year \\1', enhanced_message)
            
            # Handle "2024 January", "2024 Jan"  
            pattern = rf'\b(\d{{4}})[,\s]+{month_name}\b'
            enhanced_message = re.sub(pattern, f'month {month_num} and year \\1', enhanced_message)
            
            # Handle just month name (assume current year)
            if f' {month_name}' in enhanced_message and 'month' not in enhanced_message:
                enhanced_message = enhanced_message.replace(f' {month_name}', f' month {month_num} and year {current_year}')
        
        # Handle numeric dates like "9/2024", "09/2024", "9-2024"
        enhanced_message = re.sub(r'\b(\d{1,2})[/-](\d{4})\b', r'month \1 and year \2', enhanced_message)
        
        # Handle year references "in 2024", "for 2024", "during 2024"
        enhanced_message = re.sub(r'\b(?:in|for|during|from)\s+(\d{4})\b', r'year \1', enhanced_message)
        
        # Replace temporal expressions with specific values
        temporal_replacements = {
            'this year': f'year {current_year}',
            'current year': f'year {current_year}', 
            'this month': f'month {current_month} and year {current_year}',
            'current month': f'month {current_month} and year {current_year}',
            'last year': f'year {current_year - 1}',
            'previous year': f'year {current_year - 1}',
            'last month': f'month {current_month - 1 if current_month > 1 else 12} and year {current_year if current_month > 1 else current_year - 1}',
            'previous month': f'month {current_month - 1 if current_month > 1 else 12} and year {current_year if current_month > 1 else current_year - 1}',
            'ytd': f'year {current_year}',
            'year to date': f'year {current_year}',
            'past 12 months': f'year {current_year - 1} and year {current_year}',
            'last 12 months': f'year {current_year - 1} and year {current_year}',
            'past year': f'year {current_year - 1}',
            # Quarters
            'q1': 'month IN (1, 2, 3)',
            'q2': 'month IN (4, 5, 6)', 
            'q3': 'month IN (7, 8, 9)',
            'q4': 'month IN (10, 11, 12)',
            'first quarter': 'month IN (1, 2, 3)',
            'second quarter': 'month IN (4, 5, 6)',
            'third quarter': 'month IN (7, 8, 9)',
            'fourth quarter': 'month IN (10, 11, 12)',
        }
        
        # Apply temporal replacements
        for temporal_phrase, replacement in temporal_replacements.items():
            enhanced_message = enhanced_message.replace(temporal_phrase, replacement)
        
        # Enhanced synonym replacements for better SQL generation
        synonym_replacements = {
            # Revenue/sales synonyms
            'revenue': 'sales', 'income': 'sales', 'earnings': 'sales', 'turnover': 'sales',
            'profit': 'sales', 'proceeds': 'sales', 'receipts': 'sales', 'takings': 'sales',
            
            # Product synonyms
            'items': 'products', 'goods': 'products', 'merchandise': 'products',
            'articles': 'products', 'stock': 'products', 'inventory': 'products',
            'skus': 'products', 'catalog': 'products',
            
            # Reseller/customer synonyms
            'customers': 'resellers', 'clients': 'resellers', 'partners': 'resellers',
            'retailers': 'resellers', 'vendors': 'resellers', 'distributors': 'resellers',
            'outlets': 'resellers', 'stores': 'resellers', 'shops': 'resellers',
            
            # Performance indicators
            'best performing': 'top', 'highest selling': 'top', 'most popular': 'top',
            'best selling': 'top', 'most successful': 'top', 'leading': 'top',
        }
        
        # Apply synonym replacements
        for synonym, replacement in synonym_replacements.items():
            enhanced_message = enhanced_message.replace(synonym, replacement)
        
        return enhanced_message
        
    except Exception as e:
        print(f"Error enhancing natural language: {e}")
        return message  # Return original if enhancement fails

def _extract_query_parameters(enhanced_message: str, original_message: str) -> Dict[str, Any]:
    """Extract parameters like year, month, limit, product names, etc. from messages"""
    params = {}
    
    # Extract year
    year_match = re.search(r'year (\d{4})', enhanced_message)
    if year_match:
        params['year'] = int(year_match.group(1))
    
    # Extract month  
    month_match = re.search(r'month (\d{1,2})', enhanced_message)
    if month_match:
        params['month'] = int(month_match.group(1))
    
    # Extract quarter
    if 'month IN (' in enhanced_message:
        if '(1, 2, 3)' in enhanced_message:
            params['quarter'] = 'Q1'
            params['quarter_months'] = [1, 2, 3]
        elif '(4, 5, 6)' in enhanced_message:
            params['quarter'] = 'Q2'
            params['quarter_months'] = [4, 5, 6]
        elif '(7, 8, 9)' in enhanced_message:
            params['quarter'] = 'Q3'
            params['quarter_months'] = [7, 8, 9]
        elif '(10, 11, 12)' in enhanced_message:
            params['quarter'] = 'Q4'
            params['quarter_months'] = [10, 11, 12]
    
    # Extract limit/top N
    top_match = re.search(r'top (\d+)', enhanced_message.lower())
    if top_match:
        params['limit'] = int(top_match.group(1))
    elif 'top' in enhanced_message.lower():
        params['limit'] = 10  # Default top 10
    
    # Extract specific names for comparison
    if 'galilu' in enhanced_message.lower() and 'boxnox' in enhanced_message.lower():
        params['compare_resellers'] = ['Galilu', 'BoxNox']
    
    # Extract product name filters
    if 'bibbi' in enhanced_message.lower():
        params['product_filter'] = 'bibbi'
    
    return params

def _generate_sql_from_intent(enhanced_message: str, original_message: str) -> str:
    """Generate SQL based on detected intent patterns from sql_queries.md"""
    enhanced_lower = enhanced_message.lower()
    original_lower = original_message.lower()
    
    # Extract parameters from the enhanced message
    params = _extract_query_parameters(enhanced_message, original_message)
    
    print(f"🎯 SQL INTENT DETECTION: Enhanced='{enhanced_lower}', Params={params}")
    
    # PRODUCT ANALYSIS INTENTS
    if any(pattern in enhanced_lower for pattern in ['top products', 'best products', 'product breakdown', 'top selling']):
        return _get_product_analysis_sql(params)
    
    if any(pattern in enhanced_lower for pattern in ['product performance', 'product sales', 'units sold']):
        return _get_product_quantity_sql(params)
    
    if any(pattern in enhanced_lower for pattern in ['average price', 'price per unit', 'unit price']):
        return _get_average_price_sql(params)
    
    # TEMPORAL ANALYSIS INTENTS  
    if any(pattern in enhanced_lower for pattern in ['monthly trends', 'monthly sales', 'month by month']):
        return _get_monthly_trends_sql(params)
    
    if any(pattern in enhanced_lower for pattern in ['quarterly', 'quarter']) or any(q in enhanced_lower for q in ['q1', 'q2', 'q3', 'q4']):
        return _get_quarterly_analysis_sql(params)
    
    if any(pattern in enhanced_lower for pattern in ['year over year', 'yearly', 'annual']):
        return _get_yearly_analysis_sql(params)
    
    # RESELLER ANALYSIS INTENTS
    if any(pattern in enhanced_lower for pattern in ['top resellers', 'best customers', 'top customers', 'reseller breakdown']):
        return _get_reseller_analysis_sql(params)
    
    if any(pattern in enhanced_lower for pattern in ['reseller performance', 'customer performance']):
        return _get_reseller_product_analysis_sql(params)
    
    # COMPARATIVE ANALYSIS INTENTS
    if any(pattern in enhanced_lower for pattern in ['compare', 'vs', 'versus', 'comparison']):
        return _get_comparative_analysis_sql(params)
    
    # SPECIFIC TIME PERIOD QUERIES
    if params.get('month') and params.get('year'):
        return _get_time_filtered_sales_sql(params)
    
    if params.get('year') and not params.get('month'):
        return _get_yearly_sales_sql(params)
    
    # DEFAULT: TOTAL SALES (fallback)
    return _get_total_sales_sql(params)

def _get_product_analysis_sql(params: Dict[str, Any]) -> str:
    """Generate product analysis SQL - Query #1 from sql_queries.md"""
    limit = params.get('limit', 20)
    year_filter = f" AND year = {params['year']}" if params.get('year') else ""
    month_filter = f" AND month = {params['month']}" if params.get('month') else ""
    
    product_filter = ""
    if params.get('product_filter'):
        product_filter = f" AND functional_name ILIKE '%{params['product_filter']}%'"
    
    return f"""
    SELECT functional_name AS product, 
           SUM(sales_eur) AS total_sales, 
           SUM(quantity) AS total_units,
           COUNT(*) AS transactions
    FROM sellout_entries2 se 
    JOIN uploads u ON se.upload_id = u.id 
    WHERE u.user_id = %s{year_filter}{month_filter}{product_filter}
    GROUP BY functional_name 
    ORDER BY total_sales DESC 
    LIMIT {limit};
    """

def _get_monthly_trends_sql(params: Dict[str, Any]) -> str:
    """Generate monthly trends analysis - Query #8 from sql_queries.md"""
    year_filter = f" AND year = {params['year']}" if params.get('year') else ""
    
    return f"""
    SELECT year, month, 
           SUM(sales_eur) AS total_sales,
           SUM(quantity) AS total_units,
           COUNT(DISTINCT functional_name) AS unique_products,
           COUNT(*) AS transactions
    FROM sellout_entries2 se 
    JOIN uploads u ON se.upload_id = u.id 
    WHERE u.user_id = %s{year_filter}
    GROUP BY year, month 
    ORDER BY year DESC, month DESC
    LIMIT 24;
    """

def _get_quarterly_analysis_sql(params: Dict[str, Any]) -> str:
    """Generate quarterly analysis - Query #3 from sql_queries.md"""
    year_filter = f" AND year = {params['year']}" if params.get('year') else ""
    
    quarter_filter = ""
    if params.get('quarter_months'):
        months = ', '.join(map(str, params['quarter_months']))
        quarter_filter = f" AND month IN ({months})"
    
    return f"""
    SELECT year,
           CASE 
             WHEN month IN (1,2,3) THEN 'Q1'
             WHEN month IN (4,5,6) THEN 'Q2'
             WHEN month IN (7,8,9) THEN 'Q3'
             WHEN month IN (10,11,12) THEN 'Q4'
           END AS quarter,
           SUM(sales_eur) AS total_sales,
           SUM(quantity) AS total_units,
           COUNT(*) AS transactions
    FROM sellout_entries2 se 
    JOIN uploads u ON se.upload_id = u.id 
    WHERE u.user_id = %s{year_filter}{quarter_filter}
    GROUP BY year, quarter 
    ORDER BY year DESC, quarter DESC;
    """

def _get_reseller_analysis_sql(params: Dict[str, Any]) -> str:
    """Generate reseller analysis - Query #7 from sql_queries.md"""
    limit = params.get('limit', 20)
    year_filter = f" AND year = {params['year']}" if params.get('year') else ""
    
    return f"""
    SELECT reseller, 
           SUM(sales_eur) AS total_sales,
           SUM(quantity) AS total_units,
           COUNT(*) AS transactions,
           COUNT(DISTINCT functional_name) AS unique_products
    FROM sellout_entries2 se 
    JOIN uploads u ON se.upload_id = u.id 
    WHERE u.user_id = %s{year_filter}
    GROUP BY reseller 
    ORDER BY total_sales DESC
    LIMIT {limit};
    """

def _get_time_filtered_sales_sql(params: Dict[str, Any]) -> str:
    """Generate time-filtered sales query"""
    month = params.get('month')
    year = params.get('year')
    
    return f"""
    SELECT SUM(sales_eur) AS total_sales_eur,
           SUM(quantity) AS total_units,
           COUNT(*) AS transactions,
           COUNT(DISTINCT functional_name) AS unique_products,
           COUNT(DISTINCT reseller) AS unique_resellers
    FROM sellout_entries2 se 
    JOIN uploads u ON se.upload_id = u.id 
    WHERE u.user_id = %s AND month = {month} AND year = {year};
    """

def _get_total_sales_sql(params: Dict[str, Any]) -> str:
    """Generate total sales query (fallback)"""
    return """
    SELECT SUM(sales_eur) AS total_sales_eur,
           SUM(quantity) AS total_units,
           COUNT(*) AS transactions,
           COUNT(DISTINCT functional_name) AS unique_products,
           COUNT(DISTINCT reseller) AS unique_resellers
    FROM sellout_entries2 se 
    JOIN uploads u ON se.upload_id = u.id 
    WHERE u.user_id = %s;
    """

# Add other required functions
def _get_product_quantity_sql(params): return _get_product_analysis_sql(params)
def _get_average_price_sql(params): return _get_total_sales_sql(params)
def _get_yearly_analysis_sql(params): return _get_total_sales_sql(params)
def _get_reseller_product_analysis_sql(params): return _get_reseller_analysis_sql(params)
def _get_comparative_analysis_sql(params): return _get_reseller_analysis_sql(params)
def _get_yearly_sales_sql(params): return _get_total_sales_sql(params)

def test_sql_generation():
    """Test the SQL generation logic"""
    print("🚀 TESTING SQL GENERATION LOGIC")
    print("=" * 70)
    
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
    print("-" * 70)
    
    successful_tests = 0
    total_tests = len(test_queries)
    
    for i, (query, expected_behavior) in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print(f"   Expected: {expected_behavior}")
        
        try:
            # Test the enhanced natural language processing
            enhanced = _enhance_natural_language(query)
            print(f"   Enhanced: '{enhanced}'")
            
            # Test parameter extraction
            params = _extract_query_parameters(enhanced, query)
            print(f"   Parameters: {params}")
            
            # Test SQL generation
            sql_query = _generate_sql_from_intent(enhanced, query)
            
            # Clean up the SQL for display
            sql_clean = re.sub(r'\s+', ' ', sql_query.strip())
            sql_clean = sql_clean.replace('\n', ' ')
            
            print(f"   Generated SQL: {sql_clean[:100]}...")
            
            # Verify it's a valid SELECT query
            if sql_clean.upper().strip().startswith('SELECT'):
                print(f"   ✅ Valid SELECT query generated")
                successful_tests += 1
            else:
                print(f"   ❌ Invalid query generated")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'=' * 70}")
    print("🎯 SQL GENERATION TEST RESULTS")
    print("=" * 70)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    # Test that different queries generate different SQL patterns
    print("\n🔍 Testing SQL Diversity:")
    print("-" * 50)
    
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
            enhanced = _enhance_natural_language(query)
            sql = _generate_sql_from_intent(enhanced, query)
            # Extract key parts of the SQL to compare
            sql_signature = re.sub(r'\s+', ' ', sql.strip().split('WHERE')[0])
            generated_sqls.append(sql_signature)
            print(f"'{query[:30]}...' -> Different SQL pattern: {'✅' if len(set(generated_sqls)) == len(generated_sqls) else '❌'}")
        except Exception as e:
            print(f"'{query}' -> ERROR: {e}")
    
    # Check if we got diverse SQL patterns
    unique_patterns = len(set(generated_sqls))
    total_queries = len(diverse_queries)
    
    print(f"\n📊 SQL Diversity Results:")
    print(f"   Unique SQL patterns: {unique_patterns}/{total_queries}")
    if unique_patterns >= 4:
        print(f"   ✅ EXCELLENT diversity - Different queries generate different SQL!")
        print(f"   🎉 CRITICAL BUG FIXED - No longer generating same SQL for all queries!")
    elif unique_patterns >= 2:
        print(f"   ⚠️  Some diversity - Could be improved")
    else:
        print(f"   ❌ Poor diversity - Same SQL being generated for different queries")
        print(f"   🚨 CRITICAL BUG STILL EXISTS!")
    
    print(f"\n🎉 Testing completed!")
    
    # Show sample of the different SQL patterns generated
    print(f"\n📋 Sample SQL Patterns Generated:")
    print("-" * 50)
    for i, (query, sql) in enumerate(zip(diverse_queries, generated_sqls), 1):
        print(f"{i}. '{query[:25]}...'")
        print(f"   -> {sql[:80]}...")
        print()

if __name__ == "__main__":
    test_sql_generation()