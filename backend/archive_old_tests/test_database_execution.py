#!/usr/bin/env python3
"""Test actual database execution to debug the response issue"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock modules for testing
class MockLogger:
    def error(self, msg, **kwargs): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def info(self, msg): print(f"INFO: {msg}")

# Add minimal mocks
sys.modules['openai'] = type(sys)('openai')

async def test_database_execution():
    """Test database execution with real connection"""
    try:
        print("🔬 TESTING DATABASE EXECUTION")
        print("=" * 60)
        
        # Import database service
        from app.services.db_service import DatabaseService
        
        db_service = DatabaseService()
        
        # Test 1: Check database connection
        print("\n1. Testing database connection...")
        try:
            test_query = "SELECT 1 as test_connection;"
            test_result = await db_service.fetch_all(test_query)
            print(f"✅ Database connection: {test_result}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return
        
        # Test 2: Check if sellout_entries2 table exists and has data
        print("\n2. Testing sellout_entries2 table...")
        try:
            count_query = "SELECT COUNT(*) as total_records FROM sellout_entries2;"
            count_result = await db_service.fetch_all(count_query)
            total_records = count_result[0]['total_records'] if count_result else 0
            print(f"📊 Total records in sellout_entries2: {total_records}")
            
            if total_records == 0:
                print("⚠️  No data in sellout_entries2 table!")
            
        except Exception as e:
            print(f"❌ Error checking sellout_entries2: {e}")
            return
        
        # Test 3: Check uploads table and user data
        print("\n3. Testing uploads table and user filtering...")
        try:
            uploads_query = "SELECT id, user_id, filename FROM uploads LIMIT 5;"
            uploads_result = await db_service.fetch_all(uploads_query)
            print(f"📋 Sample uploads: {uploads_result}")
            
            if uploads_result:
                # Test with first user ID
                test_user_id = uploads_result[0]['user_id']
                print(f"🧪 Testing with user ID: {test_user_id}")
                
                user_data_query = """
                SELECT se.*, u.user_id, u.filename
                FROM sellout_entries2 se 
                JOIN uploads u ON se.upload_id = u.id 
                WHERE u.user_id = %s 
                LIMIT 3;
                """
                user_data = await db_service.fetch_all(user_data_query, (test_user_id,))
                print(f"👤 User data sample: {len(user_data)} records")
                if user_data:
                    print(f"🔍 Sample record keys: {list(user_data[0].keys())}")
                    print(f"🔍 Sample record values: {dict(list(user_data[0].items())[:5])}")
                else:
                    print("⚠️  No data found for this user!")
            
        except Exception as e:
            print(f"❌ Error checking user data: {e}")
        
        # Test 4: Test our SQL template queries
        print("\n4. Testing intent-based SQL templates...")
        
        if uploads_result:
            test_user_id = uploads_result[0]['user_id']
            
            # Test total sales query
            total_sales_query = """
            SELECT SUM(sales_eur) AS total_sales_eur,
                   SUM(quantity) AS total_units,
                   COUNT(*) AS transactions,
                   COUNT(DISTINCT functional_name) AS unique_products,
                   COUNT(DISTINCT reseller) AS unique_resellers
            FROM sellout_entries2 se 
            JOIN uploads u ON se.upload_id = u.id 
            WHERE u.user_id = %s;
            """
            
            try:
                total_result = await db_service.fetch_all(total_sales_query, (test_user_id,))
                print(f"💰 Total sales result: {total_result}")
                
                if total_result and total_result[0]['total_sales_eur']:
                    print(f"✅ Data exists! Total sales: €{total_result[0]['total_sales_eur']:,.2f}")
                else:
                    print("⚠️  No sales data or NULL values!")
                    
            except Exception as e:
                print(f"❌ Error executing total sales query: {e}")
            
            # Test product analysis query
            product_query = """
            SELECT functional_name AS product, 
                   SUM(sales_eur) AS total_sales, 
                   SUM(quantity) AS total_units,
                   COUNT(*) AS transactions
            FROM sellout_entries2 se 
            JOIN uploads u ON se.upload_id = u.id 
            WHERE u.user_id = %s
            GROUP BY functional_name 
            ORDER BY total_sales DESC 
            LIMIT 5;
            """
            
            try:
                product_result = await db_service.fetch_all(product_query, (test_user_id,))
                print(f"🛍️  Product analysis result: {len(product_result) if product_result else 0} products")
                if product_result:
                    print(f"🔍 Top product: {product_result[0]}")
                    
            except Exception as e:
                print(f"❌ Error executing product query: {e}")
        
        print(f"\n{'=' * 60}")
        print("🎯 Database testing completed!")
        
    except Exception as e:
        print(f"❌ Critical error in database testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_execution())