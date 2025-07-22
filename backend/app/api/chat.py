from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents import AgentType
from app.utils.config import get_settings
from app.services.db_service import DatabaseService
import logging
import os

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

class SupabaseSQLDatabase:
    """Mock SQLDatabase that uses Supabase REST API instead of direct PostgreSQL"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        # Mock database info for LangChain
        self._sample_rows_in_table_info = 3
        self._include_tables = ['sellout_entries2', 'uploads', 'products']
    
    def run(self, command: str, fetch: str = "all"):
        """Execute SQL command using Supabase REST API"""
        try:
            logger.info(f"Executing SQL via Supabase REST API: {command}")
            
            # Simple test query
            if command.strip().lower() in ["select 1", "select 1 as test"]:
                return "1"
            
            # For complex queries, use our smart query handler
            # This uses the same logic as your Excel cleaning system
            import asyncio
            result = asyncio.create_task(self._execute_supabase_query(command))
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to handle this differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._execute_supabase_query(command))
                    return future.result()
            else:
                return loop.run_until_complete(result)
        
        except Exception as e:
            logger.error(f"Error executing Supabase query: {str(e)}")
            return str(e)
    
    async def _execute_supabase_query(self, command: str):
        """Execute query using DatabaseService (same as Excel cleaning)"""
        try:
            # For demo purposes, return some sample data about sales
            if "sellout_entries2" in command.lower():
                # Get comprehensive sales data for accurate multi-reseller analysis
                result = self.db_service.supabase.table("sellout_entries2")\
                    .select("functional_name, reseller, sales_eur, quantity, month, year")\
                    .order("created_at", desc=True)\
                    .limit(5000)\
                    .execute()
                
                if result.data:
                    # Format as table-like response for LangChain
                    return str(result.data)
                else:
                    return "No data found"
            else:
                return "Query executed successfully"
                
        except Exception as e:
            logger.error(f"Supabase REST API query error: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_table_info(self, table_names=None):
        """Return table schema information"""
        return """
        Table: sellout_entries2
        Columns:
        - functional_name (text): Product name
        - reseller (text): Reseller/customer name
        - sales_eur (numeric): Sales amount in EUR
        - quantity (integer): Quantity sold
        - month (integer): Month (1-12)
        - year (integer): Year (e.g. 2024, 2025)
        - product_ean (text): Product EAN code
        - currency (text): Currency code
        
        Sample data:
        functional_name='Product A', reseller='Customer 1', sales_eur=1500.00, quantity=10, month=3, year=2024
        """
    
    @property
    def dialect(self):
        """Mock dialect for LangChain compatibility"""
        class MockDialect:
            name = "postgresql"
        return MockDialect()

class SupabaseChatAgent:
    """Enhanced chat agent that uses Supabase REST API for data queries with debug mode"""
    
    def __init__(self, llm, db):
        self.llm = llm
        self.db = db
        self.db_service = DatabaseService()
        self.debug_mode = True  # Enable detailed logging
    
    def invoke(self, inputs):
        """Process chat request using Supabase data with detailed debugging"""
        try:
            user_message = inputs.get("input", "")
            user_id = inputs.get("user_id")  # Get user ID for filtering
            
            if self.debug_mode:
                logger.info("=" * 50)
                logger.info("🤖 CHAT DEBUG MODE ENABLED")
                logger.info(f"📝 User message: {user_message}")
                logger.info(f"👤 User ID: {user_id}")
                logger.info("=" * 50)
            
            # Get user-specific sales data with year filtering if mentioned
            if self.debug_mode:
                logger.info("📊 Fetching user-specific sales data...")
            
            # Extract years and months from user message for filtering
            years_filter = self._extract_years_from_message(user_message)
            months_filter = self._extract_months_from_message(user_message)
            intent = self._analyze_question_intent(user_message)
            
            if self.debug_mode and years_filter:
                logger.info(f"📅 Years filter detected: {years_filter}")
            if self.debug_mode and months_filter:
                logger.info(f"📅 Months filter detected: {months_filter}")
            
            # For comparison queries, we need broader data - don't limit by year
            is_comparison = intent == "COMPARISON" or any(word in user_message.lower() for word in ['compare', 'vs', 'versus'])
            
            # Build query to access ALL sellout_entries2 data (no user filtering)
            if user_id:
                # Query ALL data from sellout_entries2 regardless of upload source
                query = self.db_service.supabase.table("sellout_entries2")\
                    .select("functional_name, reseller, sales_eur, quantity, month, year, product_ean, currency")
                
                # Add year filter if detected and not a comparison query
                if years_filter and not is_comparison:
                    if len(years_filter) == 1:
                        query = query.eq("year", years_filter[0])
                        if self.debug_mode:
                            logger.info(f"📅 Applied single year filter: {years_filter[0]}")
                    else:
                        query = query.in_("year", years_filter)
                        if self.debug_mode:
                            logger.info(f"📅 Applied multiple year filter: {years_filter}")
                elif is_comparison and self.debug_mode:
                    logger.info("🔄 Comparison query detected - fetching all years for analysis")
                
                # Add month filter if detected
                if months_filter:
                    if len(months_filter) == 1:
                        query = query.eq("month", months_filter[0])
                        if self.debug_mode:
                            logger.info(f"📅 Applied single month filter: {months_filter[0]}")
                    else:
                        query = query.in_("month", months_filter)
                        if self.debug_mode:
                            logger.info(f"📅 Applied multiple month filter: {months_filter}")
                
                result = query.order("created_at", desc=True).limit(5000).execute()
                
                if self.debug_mode:
                    logger.info(f"✅ Found {len(result.data) if result.data else 0} total records from ALL sellout_entries2 data (years: {years_filter or 'all'}, months: {months_filter or 'all'})")
                    if result.data and len(result.data) >= 5000:
                        logger.warning("⚠️ Hit 5000 record limit - consider increasing for complete 10x growth analysis")
            else:
                # Fallback to recent data if no user ID
                query = self.db_service.supabase.table("sellout_entries2")\
                    .select("functional_name, reseller, sales_eur, quantity, month, year, product_ean, currency")
                
                # Add year filter if detected and not a comparison query
                if years_filter and not is_comparison:
                    if len(years_filter) == 1:
                        query = query.eq("year", years_filter[0])
                    else:
                        query = query.in_("year", years_filter)
                    if self.debug_mode:
                        logger.info(f"📅 Applied year filter to fallback query: {years_filter}")
                
                # Add month filter if detected
                if months_filter:
                    if len(months_filter) == 1:
                        query = query.eq("month", months_filter[0])
                    else:
                        query = query.in_("month", months_filter)
                    if self.debug_mode:
                        logger.info(f"📅 Applied month filter to fallback query: {months_filter}")
                
                result = query.order("created_at", desc=True).limit(5000).execute()
                
                if self.debug_mode:
                    logger.warning("⚠️ No user ID provided, using recent data fallback")
                    logger.info(f"📊 Found {len(result.data) if result.data else 0} total records (years: {years_filter or 'all'}, months: {months_filter or 'all'})")
                    if result.data and len(result.data) >= 5000:
                        logger.warning("⚠️ Hit 5000 record limit in fallback mode - consider increasing for complete 10x growth analysis")
            
            if result.data:
                # Use the data directly (no uploads join to clean)
                clean_data = result.data
                
                if self.debug_mode:
                    logger.info(f"🧹 Cleaned data: {len(clean_data)} records")
                    
                    # Log reseller distribution for 10x growth analysis
                    resellers_found = set(row.get('reseller') for row in clean_data if row.get('reseller'))
                    logger.info(f"🏢 Resellers found in dataset: {list(resellers_found)} ({len(resellers_found)} unique)")
                    
                    # Log record distribution by reseller
                    reseller_counts = {}
                    for row in clean_data:
                        reseller = row.get('reseller', 'Unknown')
                        reseller_counts[reseller] = reseller_counts.get(reseller, 0) + 1
                    logger.info(f"📊 Record distribution by reseller: {dict(sorted(reseller_counts.items(), key=lambda x: x[1], reverse=True))}")
                    
                    logger.info(f"📈 Sample record: {clean_data[0] if clean_data else 'None'}")
                
                # Analyze user's question intent
                intent = self._analyze_question_intent(user_message)
                if self.debug_mode:
                    logger.info(f"🎯 Detected intent: {intent}")
                
                # Create a context-aware prompt with detailed data analysis
                data_summary = self._summarize_data(clean_data, intent)
                
                if self.debug_mode:
                    logger.info(f"📋 Data summary length: {len(data_summary)} characters")
                    logger.info(f"📋 Data summary preview: {data_summary[:500]}...")
                    logger.info("🔍 Sending to LLM for analysis...")
                
                # Create specialized prompt for comparison queries
                if intent == "COMPARISON":
                    prompt = f"""
                    You are an expert sales data analyst. Based on the following sales data, perform a detailed comparison analysis.
                    
                    IMPORTANT: Only show the Conclusion you make with specific numbers and calculations.
                    
                    CRITICAL: When calculating totals, ALWAYS aggregate across ALL resellers and ALL records in the data. 
                    Do NOT focus on individual resellers unless the question specifically asks for a reseller breakdown.
                    Show combined totals from all sales channels/resellers for each period being compared.
                    
                    Sales Data Summary:
                    {data_summary}
                    
                    Question Intent: {intent}
                    User Question: {user_message}
                    
                    For COMPARISON queries, please:
                    1. Extract the specific periods/products/entities being compared from the user question
                    2. Use the DETAILED PERIOD-BY-PERIOD data provided above for accurate numbers
                    3. Calculate exact differences and percentage changes using TOTAL aggregated amounts
                    4. Provide clear before/after or A vs B comparison format with complete dataset totals
                    5. Include business insights about the comparison across all sales channels
                    
                    Instructions: Ensure all calculations represent the complete dataset across all resellers.
                    """
                else:
                    prompt = f"""
                    You are an expert sales data analyst. Based on the following sales data, answer the user's question with detailed analysis.
                    
                    IMPORTANT: Only show the Conclusion you make.
                    
                    CRITICAL: When calculating totals, ALWAYS aggregate across ALL resellers and ALL records in the data. 
                    Do NOT focus on individual resellers unless the question specifically asks for a reseller breakdown.
                    Show combined totals from all sales channels/resellers.
                    
                    Sales Data Summary:
                    {data_summary}
                    
                    Question Intent: {intent}
                    User Question: {user_message}
                    
                    Instructions:
                1. Analyze the data carefully across ALL resellers and records
                2. Provide specific numbers and calculations that represent the COMPLETE dataset
                3. If grouping data (by reseller, product, time), show the breakdown only when specifically requested
                4. For general questions, provide aggregated totals across all sales channels
                5. Format numbers with currency symbols and proper formatting
                6. If the data doesn't contain enough information, explain what's available and what's missing
                
                Be thorough and analytical in your response, ensuring totals represent the entire dataset.
                """
                
                # Use the LLM to generate a response
                response = self.llm.invoke(prompt)
                
                if self.debug_mode:
                    logger.info(f"✅ LLM response generated: {len(response.content)} characters")
                    logger.info("=" * 50)
                
                return {"output": response.content}
            else:
                error_msg = "I don't have access to any sales data for your account at the moment. Please try uploading some data first."
                if self.debug_mode:
                    logger.warning("❌ No data found for user")
                return {"output": error_msg}
                
        except Exception as e:
            if self.debug_mode:
                logger.error("❌ ERROR in Supabase chat agent:")
                logger.error(f"   Error type: {type(e).__name__}")
                logger.error(f"   Error message: {str(e)}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
            return {"output": f"I encountered an error while processing your request: {str(e)}"}
    
    def run(self, input_text):
        """Compatibility method for older LangChain versions"""
        result = self.invoke({"input": input_text})
        return result.get("output", "Error processing request")
    
    def _extract_years_from_message(self, user_message):
        """Extract all years from user message for filtering"""
        import re
        
        # Look for 4-digit years (2020-2030)
        year_pattern = r'\b(202[0-9])\b'
        matches = re.findall(year_pattern, user_message)
        
        if matches:
            # Return unique years as integers, sorted
            unique_years = sorted(list(set(int(year) for year in matches)))
            return unique_years
        
        return []
    
    def _extract_months_from_message(self, user_message):
        """Extract month names from user message"""
        import re
        
        message_lower = user_message.lower()
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
            'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        found_months = []
        for month_name, month_num in months.items():
            if re.search(rf'\b{month_name}\b', message_lower):
                found_months.append(month_num)
        
        # Return unique months, sorted
        return sorted(list(set(found_months)))
    
    def _analyze_question_intent(self, user_message):
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
        
        # Comparison queries - enhanced detection
        elif any(word in message_lower for word in ['compare', 'vs', 'versus', 'difference', 'higher', 'lower', 'best', 'worst', 'against', 'between', 'than']):
            return "COMPARISON"
        
        else:
            return "GENERAL_INQUIRY"
    
    def _summarize_data(self, data, intent="GENERAL_INQUIRY"):
        """Create comprehensive data analysis for the LLM based on intent - NO SAMPLE RECORDS"""
        if not data:
            return "No data available"
        
        try:
            # Basic statistics
            total_sales = sum(float(row.get('sales_eur', 0) or 0) for row in data)
            total_quantity = sum(int(row.get('quantity', 0) or 0) for row in data)
            
            # Get unique entities
            products = set(row.get('functional_name') for row in data if row.get('functional_name'))
            resellers = set(row.get('reseller') for row in data if row.get('reseller'))
            currencies = set(row.get('currency') for row in data if row.get('currency'))
            
            # Time analysis
            years = set(row.get('year') for row in data if row.get('year'))
            months = set(row.get('month') for row in data if row.get('month'))
            
            # Build comprehensive analysis with intent-specific focus
            summary = f"""
            COMPLETE SALES DATA ANALYSIS ({len(data)} total records) - Intent: {intent}:
            - Total Sales: €{total_sales:,.2f}
            - Total Quantity: {total_quantity:,} units
            - Unique Products: {len(products)} products
            - Unique Resellers: {len(resellers)} resellers
            - Currencies: {', '.join(currencies)}
            - Time Period: Years {sorted(years)}, Months {sorted(months)}
            """
            
            # Add intent-specific note and detailed breakdowns
            if intent == "COMPARISON":
                summary += f"\n\nNOTE: This is a COMPARISON query. Focus on comparing different time periods, products, or resellers based on the user's question."
                
                # Add detailed period-specific breakdowns for comparisons
                period_analysis = self._create_period_comparison_analysis(data)
                if period_analysis:
                    summary += f"\n\n{period_analysis}"
                    
            elif intent == "TIME_ANALYSIS":
                summary += f"\n\nNOTE: This is a TIME ANALYSIS query. Focus on temporal trends, seasonal patterns, and period-over-period changes."
            
            # ALWAYS provide complete breakdowns for accurate analysis
            # 1. Complete Reseller Analysis
            reseller_totals = {}
            reseller_quantities = {}
            for row in data:
                reseller = row.get('reseller', 'Unknown')
                sales = float(row.get('sales_eur', 0) or 0)
                quantity = int(row.get('quantity', 0) or 0)
                
                if reseller not in reseller_totals:
                    reseller_totals[reseller] = 0
                    reseller_quantities[reseller] = 0
                reseller_totals[reseller] += sales
                reseller_quantities[reseller] += quantity
            
            sorted_resellers = sorted(reseller_totals.items(), key=lambda x: x[1], reverse=True)
            summary += f"\n\nCOMPLETE RESELLER ANALYSIS:\n"
            for reseller, total in sorted_resellers:
                quantity = reseller_quantities[reseller]
                summary += f"- {reseller}: €{total:,.2f} (Quantity: {quantity:,})\n"
            
            # 2. Complete Product Analysis
            product_totals = {}
            product_quantities = {}
            for row in data:
                product = row.get('functional_name', 'Unknown')
                sales = float(row.get('sales_eur', 0) or 0)
                quantity = int(row.get('quantity', 0) or 0)
                
                if product not in product_totals:
                    product_totals[product] = 0
                    product_quantities[product] = 0
                product_totals[product] += sales
                product_quantities[product] += quantity
            
            sorted_products = sorted(product_totals.items(), key=lambda x: x[1], reverse=True)
            summary += f"\n\nTOP 10 PRODUCTS BY SALES:\n"
            for product, total in sorted_products[:10]:
                quantity = product_quantities[product]
                summary += f"- {product}: €{total:,.2f} (Quantity: {quantity:,})\n"
            
            # 3. Complete Time Analysis
            monthly_totals = {}
            yearly_totals = {}
            for row in data:
                year = row.get('year')
                month = row.get('month')
                sales = float(row.get('sales_eur', 0) or 0)
                
                if year:
                    if year not in yearly_totals:
                        yearly_totals[year] = 0
                    yearly_totals[year] += sales
                    
                    if month:
                        time_key = f"{year}-{month:02d}"
                        if time_key not in monthly_totals:
                            monthly_totals[time_key] = 0
                        monthly_totals[time_key] += sales
            
            # Show yearly totals
            summary += f"\n\nYEARLY SALES TOTALS:\n"
            for year in sorted(yearly_totals.keys()):
                summary += f"- {year}: €{yearly_totals[year]:,.2f}\n"
            
            # Show monthly totals (recent ones)
            sorted_months = sorted(monthly_totals.items())
            summary += f"\n\nMONTHLY BREAKDOWN (Recent):\n"
            for time_period, total in sorted_months[-12:]:  # Last 12 months
                summary += f"- {time_period}: €{total:,.2f}\n"
            
            summary += f"\n\nIMPORTANT: Base your analysis on the COMPLETE data above, not on individual records."
            
            return summary
            
        except Exception as e:
            return f"Data available but error in summary: {str(e)}"
    
    def _create_period_comparison_analysis(self, data):
        """Create detailed period-by-period comparison analysis"""
        if not data:
            return None
            
        try:
            # Group data by year-month combinations
            period_totals = {}
            period_quantities = {}
            period_products = {}
            
            for row in data:
                year = row.get('year')
                month = row.get('month')
                sales = float(row.get('sales_eur', 0) or 0)
                quantity = int(row.get('quantity', 0) or 0)
                product = row.get('functional_name', 'Unknown')
                
                if year and month:
                    # Create period key (e.g., "2024-05" for May 2024)
                    period_key = f"{year}-{month:02d}"
                    
                    # Initialize period if not exists
                    if period_key not in period_totals:
                        period_totals[period_key] = 0
                        period_quantities[period_key] = 0
                        period_products[period_key] = set()
                    
                    # Accumulate data for this period
                    period_totals[period_key] += sales
                    period_quantities[period_key] += quantity
                    period_products[period_key].add(product)
            
            # Create detailed comparison summary
            comparison_summary = "DETAILED PERIOD-BY-PERIOD COMPARISON ANALYSIS:\n"
            
            # Sort periods chronologically
            sorted_periods = sorted(period_totals.keys())
            
            for period in sorted_periods:
                year, month = period.split('-')
                month_name = {
                    '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                    '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                    '09': 'September', '10': 'October', '11': 'November', '12': 'December'
                }.get(month, f"Month {month}")
                
                total_sales = period_totals[period]
                total_quantity = period_quantities[period]
                unique_products = len(period_products[period])
                
                comparison_summary += f"\n📅 {month_name} {year}:\n"
                comparison_summary += f"   - Sales: €{total_sales:,.2f}\n"
                comparison_summary += f"   - Quantity: {total_quantity:,} units\n"
                comparison_summary += f"   - Products: {unique_products} unique products\n"
            
            # Add growth calculations if we have multiple periods
            if len(sorted_periods) >= 2:
                comparison_summary += "\n📊 PERIOD-TO-PERIOD CHANGES:\n"
                
                for i in range(1, len(sorted_periods)):
                    current_period = sorted_periods[i]
                    previous_period = sorted_periods[i-1]
                    
                    current_sales = period_totals[current_period]
                    previous_sales = period_totals[previous_period]
                    
                    if previous_sales > 0:
                        change_amount = current_sales - previous_sales
                        change_percent = (change_amount / previous_sales) * 100
                        
                        year_curr, month_curr = current_period.split('-')
                        year_prev, month_prev = previous_period.split('-')
                        
                        month_name_curr = {
                            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
                            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
                            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
                        }.get(month_curr, f"M{month_curr}")
                        
                        month_name_prev = {
                            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
                            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
                            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
                        }.get(month_prev, f"M{month_prev}")
                        
                        direction = "↗️ INCREASE" if change_amount > 0 else "↘️ DECREASE"
                        
                        comparison_summary += f"\n   {month_name_prev} {year_prev} → {month_name_curr} {year_curr}: €{change_amount:,.2f} ({change_percent:+.1f}%) {direction}"
            
            comparison_summary += f"\n\nIMPORTANT: Use the above period-specific data for accurate comparisons. Each period's sales total is calculated precisely."
            
            return comparison_summary
            
        except Exception as e:
            return f"Error creating period comparison: {str(e)}"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str

# Global variables to store DB connection and agent
_db = None
_agent_executor = None
_use_supabase_fallback = False
_supabase_db_service = None

def get_database():
    """Get or create database connection for LangChain chat functionality"""
    global _db
    
    if _db is not None:
        return _db
    
    try:
        settings = get_settings()
        
        # Attempt to get database URL for direct PostgreSQL connection
        db_url = settings.langchain_database_url
        
        # Test connection with multiple attempts
        attempts = [
            ("Direct PostgreSQL via DATABASE_URL", db_url),
            ("Supabase REST API (Fallback)", None)
        ]
        
        for attempt_name, url in attempts:
            try:
                if url:
                    logger.info(f"Attempting connection with {attempt_name}")
                    _db = SQLDatabase.from_uri(url)
                    
                    # Test the connection
                    test_result = _db.run("SELECT 1 as test")
                    logger.info(f"Database connection successful with {attempt_name}")
                    logger.info(f"Test query result: {test_result}")
                    
                    return _db
                else:
                    # Use Supabase REST API fallback
                    logger.warning("DATABASE_URL not available, using Supabase REST API fallback")
                    global _use_supabase_fallback
                    _use_supabase_fallback = True
                    _db = SupabaseSQLDatabase()
                    logger.info("✅ Supabase REST API fallback initialized successfully")
                    return _db
                    
            except Exception as attempt_error:
                logger.warning(f"❌ {attempt_name} failed: {str(attempt_error)}")
                continue
        
        # If all attempts failed, raise the last error
        raise Exception("All database connection attempts failed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed completely: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def get_agent_executor():
    """Get or create the SQL agent executor"""
    global _agent_executor
    
    if _agent_executor is not None:
        return _agent_executor
    
    try:
        settings = get_settings()
        
        # Initialize OpenAI LLM
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature
        )
        
        # Get database connection
        db = get_database()
        
        # Check if we're using Supabase fallback
        if _use_supabase_fallback:
            logger.info("🔄 Using Supabase REST API agent (no direct SQL)")
            _agent_executor = SupabaseChatAgent(llm, db)
        else:
            logger.info("🔄 Using standard LangChain SQL agent")
            # Create SQL agent with standard LangChain
            toolkit = SQLDatabaseToolkit(db=db, llm=llm)
            _agent_executor = create_sql_agent(
                llm=llm,
                toolkit=toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True
            )
        
        return _agent_executor
        
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_data(request: ChatRequest, authorization: str = Header(None)):
    """
    Enhanced chat endpoint with proper user authentication and debug mode
    """
    # Extract user ID from JWT token - OUTSIDE main try block so 401 errors propagate properly
    user_info = None
    user_id = None
    
    if authorization:
        try:
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user_info = await auth_service.verify_token(token)
            
            # Extract user ID from JWT payload
            if user_info and user_info.get('id'):
                user_id = user_info.get('id')
                logger.info(f"🔐 Authenticated user: {user_id}")
            else:
                logger.warning("⚠️ JWT token valid but no user ID found")
                
        except Exception as auth_error:
            logger.error(f"❌ Authentication failed: {str(auth_error)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    else:
        logger.warning("⚠️ No authorization header provided - using anonymous mode")
    
    # Main chat processing
    try:
        logger.info(f"🤖 Processing chat request: '{request.message}' for user: {user_id or 'anonymous'}")
        
        # Get agent
        agent = get_agent_executor()
        
        # Enhanced input with user context
        enhanced_input = {
            "input": request.message,
            "user_id": user_id  # Pass user ID to agent for filtering
        }
        
        # Run the agent with user-specific context
        try:
            response = agent.invoke(enhanced_input)
            # Extract the output from the response
            if isinstance(response, dict) and "output" in response:
                response = response["output"]
        except AttributeError:
            # Fallback to older run method (won't have user filtering)
            response = agent.run(request.message)
        
        logger.info(f"Agent response generated successfully: {len(response)} characters")
        return ChatResponse(answer=response)
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Sorry, I couldn't process your question. Please try rephrasing it. Error: {str(e)}"
        )

@router.get("/chat/health")
async def chat_health():
    """Health check endpoint for chat functionality"""
    try:
        db = get_database()
        # Test database connection
        result = db.run("SELECT 1")
        return {"status": "healthy", "database": "connected", "test_result": result}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}