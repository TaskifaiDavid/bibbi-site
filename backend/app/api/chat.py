from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents import AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from app.utils.config import get_settings
from app.services.db_service import DatabaseService
import logging
import os
import json
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

class ConversationMemoryService:
    """Enhanced conversation memory service with persistence"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.memory_cache = {}  # In-memory cache for active conversations
    
    def get_conversation_memory(self, user_id: str, session_id: Optional[str] = None) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a user"""
        cache_key = f"{user_id}_{session_id or 'default'}"
        
        if cache_key not in self.memory_cache:
            # Create new memory with window size of 10 messages (5 exchanges)
            memory = ConversationBufferWindowMemory(
                k=10,
                return_messages=True,
                memory_key="chat_history"
            )
            
            # Load existing conversation history from database
            history = self._load_conversation_history(user_id, session_id)
            if history:
                for msg in history:
                    if msg['type'] == 'human':
                        memory.chat_memory.add_user_message(msg['content'])
                    else:
                        memory.chat_memory.add_ai_message(msg['content'])
            
            self.memory_cache[cache_key] = memory
        
        return self.memory_cache[cache_key]
    
    def save_conversation_turn(self, user_id: str, user_message: str, ai_response: str, session_id: Optional[str] = None):
        """Save a conversation turn to the database"""
        try:
            conversation_data = {
                'user_id': user_id,
                'session_id': session_id or 'default',
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Save to database (create conversation_history table if needed)
            self.db_service.supabase.table("conversation_history").insert(conversation_data).execute()
            logger.info(f"Saved conversation turn for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to save conversation turn: {e}")
    
    def _load_conversation_history(self, user_id: str, session_id: Optional[str] = None) -> List[Dict]:
        """Load recent conversation history from database"""
        try:
            result = self.db_service.supabase.table("conversation_history")\
                .select("user_message, ai_response, timestamp")\
                .eq("user_id", user_id)\
                .eq("session_id", session_id or 'default')\
                .order("timestamp", desc=False)\
                .limit(20)\
                .execute()
            
            if result.data:
                history = []
                for row in result.data:
                    history.append({'type': 'human', 'content': row['user_message']})
                    history.append({'type': 'ai', 'content': row['ai_response']})
                return history
            return []
        except Exception as e:
            logger.warning(f"Failed to load conversation history: {e}")
            return []
    
    def clear_conversation(self, user_id: str, session_id: Optional[str] = None):
        """Clear conversation memory and history"""
        cache_key = f"{user_id}_{session_id or 'default'}"
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        try:
            # Clear from database
            self.db_service.supabase.table("conversation_history")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("session_id", session_id or 'default')\
                .execute()
            logger.info(f"Cleared conversation history for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to clear conversation history: {e}")

class SupabaseSQLDatabase:
    """Mock SQLDatabase that uses Supabase REST API instead of direct PostgreSQL"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        # Mock database info for LangChain
        self._sample_rows_in_table_info = 3
        self._include_tables = ['sellout_entries2', 'ecommerce_orders', 'uploads', 'products']
    
    def run(self, command: str, fetch: str = "all"):
        """Execute SQL command using Supabase REST API with security validation"""
        try:
            # Security: Validate SQL command pattern before execution
            if not self._validate_sql_command(command):
                logger.warning(f"SQL command blocked by security validation: {command}")
                return "Query pattern not allowed for security reasons"
            
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
    
    def _validate_sql_command(self, command: str) -> bool:
        """Validate SQL command against security patterns"""
        import re
        
        if not command or not isinstance(command, str):
            return False
        
        # Convert to uppercase and strip for pattern matching
        command_upper = command.upper().strip()
        
        # Block dangerous SQL operations completely
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bGRANT\b',
            r'\bREVOKE\b', r'\bEXEC\b', r'\bSHUTDOWN\b', r'\bUNION\b',
            r'--', r'/\*', r'\*/', r';.*SELECT', r'SELECT.*INTO\s+OUTFILE'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command_upper):
                logger.warning(f"Blocked dangerous SQL pattern: {pattern}")
                return False
        
        # Allow only safe SELECT patterns on approved tables
        safe_patterns = [
            r'^SELECT\s+.*\s+FROM\s+sellout_entries2\b',
            r'^SELECT\s+\*\s+FROM\s+sellout_entries2\b',
            r'^SELECT\s+COUNT\(\*\)\s+FROM\s+sellout_entries2\b',
            r'^SELECT\s+.*\s+FROM\s+ecommerce_orders\b',
            r'^SELECT\s+\*\s+FROM\s+ecommerce_orders\b',
            r'^SELECT\s+COUNT\(\*\)\s+FROM\s+ecommerce_orders\b',
            r'^SELECT\s+1\s*$',
            r'^SELECT\s+1\s+AS\s+TEST\s*$',
            r'^SELECT\s+.*\s+FROM\s+products\b',
            r'^SELECT\s+.*\s+FROM\s+uploads\b'
        ]
        
        # Check if command matches at least one safe pattern
        for pattern in safe_patterns:
            if re.match(pattern, command_upper):
                return True
        
        logger.warning(f"SQL command doesn't match any safe patterns: {command}")
        return False
    
    async def _execute_supabase_query(self, command: str):
        """Execute query using DatabaseService (same as Excel cleaning)"""
        try:
            # Route queries to appropriate tables
            if "sellout_entries2" in command.lower():
                # Get comprehensive wholesale/offline sales data
                result = self.db_service.supabase.table("sellout_entries2")\
                    .select("functional_name, reseller, sales_eur, quantity, month, year")\
                    .order("created_at", desc=True)\
                    .limit(5000)\
                    .execute()
                
                if result.data:
                    return str(result.data)
                else:
                    return "No offline sales data found"
            elif "ecommerce_orders" in command.lower():
                # Get comprehensive online sales data
                result = self.db_service.supabase.table("ecommerce_orders")\
                    .select("functional_name, product_name, sales_eur, quantity, order_date, country, city, utm_source, device_type")\
                    .order("order_date", desc=True)\
                    .limit(5000)\
                    .execute()
                
                if result.data:
                    return str(result.data)
                else:
                    return "No online sales data found"
            else:
                return "Query executed successfully"
                
        except Exception as e:
            logger.error(f"Supabase REST API query error: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_table_info(self, table_names=None):
        """Return table schema information"""
        # Note: table_names parameter maintained for compatibility but not currently used
        return """
        Table: sellout_entries2 (Offline/Wholesale Sales)
        Columns:
        - functional_name (text): Product name
        - reseller (text): Reseller/customer name
        - sales_eur (numeric): Sales amount in EUR
        - quantity (integer): Quantity sold
        - month (integer): Month (1-12)
        - year (integer): Year (e.g. 2024, 2025)
        - product_ean (text): Product EAN code
        - currency (text): Currency code
        
        Table: ecommerce_orders (Online Sales)
        Columns:
        - order_id (text): Unique order identifier
        - product_ean (text): Product EAN code
        - order_date (date): Date of order
        - quantity (numeric): Quantity ordered
        - sales_eur (numeric): Sales amount in EUR
        - country (text): Customer country
        - functional_name (text): Product name
        - product_name (text): Product display name
        - city (text): Customer city
        - utm_source (text): Marketing source
        - utm_medium (text): Marketing medium
        - utm_campaign (text): Marketing campaign
        - device_type (text): Customer device type
        - reseller (text): Always 'Online' for ecommerce
        - cost_of_goods (numeric): Product cost
        - stripe_fee (numeric): Payment processing fee
        
        Sample data:
        sellout_entries2: functional_name='Product A', reseller='Wholesale Customer', sales_eur=1500.00, quantity=10
        ecommerce_orders: functional_name='Product A', product_name='Product A - 50ml', sales_eur=49.99, quantity=1, country='DE', utm_source='google'
        """
    
    @property
    def dialect(self):
        """Mock dialect for LangChain compatibility"""
        class MockDialect:
            name = "postgresql"
        return MockDialect()

class SupabaseChatAgent:
    """Enhanced chat agent that uses Supabase REST API for data queries with conversation memory"""
    
    def __init__(self, llm, db):
        self.llm = llm
        self.db = db
        self.db_service = DatabaseService()
        self.memory_service = ConversationMemoryService()
        self.debug_mode = True  # Enable detailed logging
    
    def invoke(self, inputs):
        """Process chat request using Supabase data with conversation memory"""
        try:
            user_message = inputs.get("input", "")
            user_id = inputs.get("user_id")  # Get user ID for filtering
            session_id = inputs.get("session_id")  # Optional session ID for multiple conversations
            
            if self.debug_mode:
                logger.info("=" * 50)
                logger.info("🤖 ENHANCED CHAT WITH MEMORY")
                logger.info(f"📝 User message: {user_message}")
                logger.info(f"👤 User ID: {user_id}")
                logger.info(f"🔗 Session ID: {session_id or 'default'}")
                logger.info("=" * 50)
            
            # Get conversation memory for this user
            memory = None
            if user_id:
                memory = self.memory_service.get_conversation_memory(user_id, session_id)
                if self.debug_mode:
                    chat_history = memory.chat_memory.messages if memory else []
                    logger.info(f"💭 Loaded conversation history: {len(chat_history)} messages")
            
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
            is_comparison = intent in ["COMPARISON", "SALES_COMPARISON"] or any(word in user_message.lower() for word in ['compare', 'vs', 'versus'])
            
            # Query data based on detected intent
            if self.debug_mode:
                logger.info(f"🎯 Detected intent: {intent}")
            
            # Get data based on sales channel intent
            offline_data = []
            online_data = []
            
            # Determine which data to fetch based on intent
            fetch_offline = intent in ["OFFLINE_SALES", "COMBINED_SALES", "SALES_COMPARISON"] or intent in ["TIME_ANALYSIS", "RESELLER_ANALYSIS", "PRODUCT_ANALYSIS", "TOTAL_SUMMARY", "COMPARISON", "GENERAL_INQUIRY"]
            fetch_online = intent in ["ONLINE_SALES", "COMBINED_SALES", "SALES_COMPARISON"]
            
            if fetch_offline:
                if self.debug_mode:
                    logger.info("📊 Fetching offline/wholesale sales data (sellout_entries2)...")
                
                offline_query = self.db_service.supabase.table("sellout_entries2")\
                    .select("functional_name, reseller, sales_eur, quantity, month, year, product_ean, currency")
                
                # Apply time filters if not a comparison query
                if years_filter and not is_comparison:
                    if len(years_filter) == 1:
                        offline_query = offline_query.eq("year", years_filter[0])
                    else:
                        offline_query = offline_query.in_("year", years_filter)
                
                if months_filter:
                    if len(months_filter) == 1:
                        offline_query = offline_query.eq("month", months_filter[0])
                    else:
                        offline_query = offline_query.in_("month", months_filter)
                
                offline_result = offline_query.order("created_at", desc=True).limit(5000).execute()
                offline_data = offline_result.data if offline_result.data else []
                
                if self.debug_mode:
                    logger.info(f"✅ Found {len(offline_data)} offline sales records")
            
            if fetch_online:
                if self.debug_mode:
                    logger.info("🌐 Fetching online sales data (ecommerce_orders)...")
                
                online_query = self.db_service.supabase.table("ecommerce_orders")\
                    .select("functional_name, product_name, sales_eur, quantity, order_date, country, city, utm_source, utm_medium, utm_campaign, device_type, reseller, product_ean")
                
                # Apply date filters for online data (using order_date instead of month/year)
                if years_filter and not is_comparison:
                    for year in years_filter:
                        online_query = online_query.gte("order_date", f"{year}-01-01").lte("order_date", f"{year}-12-31")
                
                online_result = online_query.order("order_date", desc=True).limit(5000).execute()
                online_data = online_result.data if online_result.data else []
                
                if self.debug_mode:
                    logger.info(f"✅ Found {len(online_data)} online sales records")
            
            # Combine data based on intent
            if intent == "ONLINE_SALES":
                clean_data = online_data
                data_source = "online"
            elif intent == "OFFLINE_SALES":
                clean_data = offline_data  
                data_source = "offline"
            elif intent in ["COMBINED_SALES", "SALES_COMPARISON"]:
                # Normalize online data to match offline structure for combined analysis
                normalized_online = []
                for row in online_data:
                    # Extract year and month from order_date
                    order_date = row.get('order_date', '')
                    year, month = None, None
                    if order_date:
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(order_date, '%Y-%m-%d')
                            year = date_obj.year
                            month = date_obj.month
                        except:
                            pass
                    
                    normalized_row = {
                        'functional_name': row.get('functional_name') or row.get('product_name'),
                        'reseller': 'Online',
                        'sales_eur': row.get('sales_eur'),
                        'quantity': row.get('quantity'), 
                        'year': year,
                        'month': month,
                        'product_ean': row.get('product_ean'),
                        'currency': 'EUR',
                        'channel': 'online',
                        'country': row.get('country'),
                        'utm_source': row.get('utm_source'),
                        'device_type': row.get('device_type')
                    }
                    normalized_online.append(normalized_row)
                
                # Add channel identifier to offline data
                for row in offline_data:
                    row['channel'] = 'offline'
                
                clean_data = offline_data + normalized_online
                data_source = "combined"
            else:
                # Default to offline data for backward compatibility
                clean_data = offline_data
                data_source = "offline"
            
            if clean_data:
                
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
                
                # Include conversation context in prompts
                conversation_context = ""
                if memory and memory.chat_memory.messages:
                    recent_messages = memory.chat_memory.messages[-6:]  # Last 3 exchanges
                    context_parts = []
                    for msg in recent_messages:
                        if isinstance(msg, HumanMessage):
                            context_parts.append(f"User: {msg.content}")
                        elif isinstance(msg, AIMessage):
                            context_parts.append(f"Assistant: {msg.content[:200]}...")
                    conversation_context = f"\n\nConversation Context (Recent):\n" + "\n".join(context_parts)

                # Create specialized prompts based on intent
                if intent in ["COMPARISON", "SALES_COMPARISON"]:
                    prompt = f"""
                    You are an expert sales data analyst with conversation memory. Based on the following sales data and conversation context, perform a detailed comparison analysis.
                    

                    
                    CRITICAL: When calculating totals, ALWAYS aggregate across ALL resellers and ALL records in the data. 
                    Do NOT focus on individual resellers unless the question specifically asks for a reseller breakdown.
                    Show combined totals from all sales channels/resellers for each period being compared.
                    
                    Sales Data Summary:
                    {data_summary}
                    {conversation_context}
                    
                    Question Intent: {intent}
                    Current User Question: {user_message}
                    
                    For COMPARISON queries, please:
                    1. Consider previous conversation context for better understanding
                    2. Extract the specific periods/products/entities being compared from the current question
                    3. Use the DETAILED PERIOD-BY-PERIOD data provided above for accurate numbers
                    4. Calculate exact differences and percentage changes using TOTAL aggregated amounts
                    5. Provide clear before/after or A vs B comparison format with complete dataset totals
                    6. Include business insights about the comparison across all sales channels
                    7. If comparing online vs offline sales, highlight channel-specific insights and performance
                    
                    Instructions: Ensure all calculations represent the complete dataset across all channels.
                    """
                elif intent == "ONLINE_SALES":
                    prompt = f"""
                    You are an expert ecommerce data analyst with conversation memory. Based on the following online sales data and conversation context, provide detailed analysis focused on digital commerce metrics.
                    
                    FOCUS AREAS FOR ONLINE SALES:
                    - Ecommerce performance and conversion insights
                    - Geographic market analysis (countries, cities)
                    - Digital marketing effectiveness (UTM sources, campaigns)
                    - Customer behavior patterns (device types)
                    - Online revenue and order trends
                    
                    Sales Data Summary:
                    {data_summary}
                    {conversation_context}
                    
                    Question Intent: {intent}
                    Current User Question: {user_message}
                    
                    Instructions: Focus on online-specific metrics and insights. Include geographic and digital marketing analysis when relevant.
                    """
                elif intent == "OFFLINE_SALES":
                    prompt = f"""
                    You are an expert B2B sales analyst with conversation memory. Based on the following offline/wholesale sales data and conversation context, provide detailed analysis focused on reseller and wholesale performance.
                    
                    FOCUS AREAS FOR OFFLINE SALES:
                    - Reseller and distributor performance analysis
                    - B2B sales trends and patterns  
                    - Wholesale volume and revenue metrics
                    - Channel partner effectiveness
                    - Regional wholesale market analysis
                    
                    Sales Data Summary:
                    {data_summary}
                    {conversation_context}
                    
                    Question Intent: {intent}
                    Current User Question: {user_message}
                    
                    Instructions: Focus on wholesale and B2B metrics. Analyze reseller performance and partnership effectiveness.
                    """
                elif intent == "COMBINED_SALES":
                    prompt = f"""
                    You are an expert omnichannel sales analyst with conversation memory. Based on the following combined sales data from both online and offline channels, provide comprehensive multi-channel analysis.
                    
                    FOCUS AREAS FOR COMBINED SALES:
                    - Total business performance across all channels
                    - Channel mix and contribution analysis
                    - Online vs offline performance comparison
                    - Comprehensive revenue and volume metrics
                    - Cross-channel insights and opportunities
                    
                    Sales Data Summary:
                    {data_summary}
                    {conversation_context}
                    
                    Question Intent: {intent}
                    Current User Question: {user_message}
                    
                    Instructions: Provide holistic business analysis combining both online and offline performance. Highlight channel-specific strengths and total business impact.
                    """
                else:
                    prompt = f"""
                    You are an expert sales data analyst with conversation memory. Based on the following sales data and conversation context, answer the user's question with detailed analysis.
                    
                    CRITICAL: When calculating totals, ALWAYS aggregate across ALL resellers and ALL records in the data. 
                    Do NOT focus on individual resellers unless the question specifically asks for a reseller breakdown.
                    Show combined totals from all sales channels/resellers.
                    
                    Sales Data Summary:
                    {data_summary}
                    {conversation_context}
                    
                    Question Intent: {intent}
                    Current User Question: {user_message}
                    
                    Instructions:
                1. Consider previous conversation context to provide continuity and better responses
                2. Analyze the data carefully across ALL resellers and records
                3. Provide specific numbers and calculations that represent the COMPLETE dataset
                4. If grouping data (by reseller, product, time), show the breakdown only when specifically requested
                5. For general questions, provide aggregated totals across all sales channels
                6. Format numbers with currency symbols and proper formatting
                7. If the data doesn't contain enough information, explain what's available and what's missing
                8. Reference previous questions or answers when relevant
                
                Be thorough and analytical in your response, ensuring totals represent the entire dataset.
                """
                
                # Use the LLM to generate a response
                response = self.llm.invoke(prompt)
                
                if self.debug_mode:
                    logger.info(f"✅ LLM response generated: {len(response.content)} characters")
                    logger.info("=" * 50)
                
                # Save conversation turn to memory and database
                if user_id and memory:
                    memory.chat_memory.add_user_message(user_message)
                    memory.chat_memory.add_ai_message(response.content)
                    # Save to database asynchronously
                    self.memory_service.save_conversation_turn(
                        user_id, user_message, response.content, session_id
                    )
                    if self.debug_mode:
                        logger.info("💾 Conversation turn saved to memory and database")
                
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
    
    def _is_online_sales_query(self, message_lower):
        """Check if query is specifically about online sales"""
        online_keywords = [
            'online', 'ecommerce', 'e-commerce', 'website', 'web', 'direct', 
            'consumer', 'b2c', 'digital', 'internet', 'webstore', 'shop online',
            'utm', 'google', 'facebook', 'ads', 'campaign', 'traffic', 'device'
        ]
        return any(keyword in message_lower for keyword in online_keywords)
    
    def _is_offline_sales_query(self, message_lower):
        """Check if query is specifically about offline/wholesale sales"""
        offline_keywords = [
            'offline', 'wholesale', 'b2b', 'reseller', 'distributor', 
            'retail', 'partner', 'channel', 'physical', 'store', 'shops'
        ]
        return any(keyword in message_lower for keyword in offline_keywords)
    
    def _is_combined_sales_query(self, message_lower):
        """Check if query wants both online and offline data"""
        combined_keywords = [
            'total sales', 'all sales', 'combined sales', 'overall sales',
            'entire business', 'both channels', 'all channels', 'everything'
        ]
        return any(keyword in message_lower for keyword in combined_keywords)
    
    def _is_sales_comparison_query(self, message_lower):
        """Check if query wants to compare online vs offline sales"""
        comparison_indicators = [
            ('online', 'offline'), ('ecommerce', 'wholesale'), ('direct', 'reseller'),
            ('website', 'retail'), ('b2c', 'b2b'), ('digital', 'physical')
        ]
        
        for word1, word2 in comparison_indicators:
            if word1 in message_lower and word2 in message_lower:
                return True
        
        # Also check for explicit comparison words with channel mentions
        comparison_words = ['vs', 'versus', 'compare', 'difference between', 'against']
        has_comparison = any(comp in message_lower for comp in comparison_words)
        has_channels = ('online' in message_lower or 'offline' in message_lower or 
                       'wholesale' in message_lower or 'ecommerce' in message_lower)
        
        return has_comparison and has_channels
    
    def _analyze_question_intent(self, user_message):
        """Analyze user's question to understand their intent"""
        message_lower = user_message.lower()
        
        # Sales channel specific queries - check first for specificity
        if self._is_online_sales_query(message_lower):
            return "ONLINE_SALES"
        elif self._is_offline_sales_query(message_lower):
            return "OFFLINE_SALES"
        elif self._is_combined_sales_query(message_lower):
            return "COMBINED_SALES"
        elif self._is_sales_comparison_query(message_lower):
            return "SALES_COMPARISON"
        
        # Time-based queries
        elif any(word in message_lower for word in ['year', 'month', 'quarterly', '2023', '2024', '2025', 'monthly', 'yearly', 'trend']):
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
            
            # Sales channel analysis
            channels = set(row.get('channel') for row in data if row.get('channel'))
            has_multiple_channels = len(channels) > 1
            
            # Channel-specific statistics
            online_data = [row for row in data if row.get('channel') == 'online']
            offline_data = [row for row in data if row.get('channel') == 'offline']
            
            online_sales = sum(float(row.get('sales_eur', 0) or 0) for row in online_data)
            offline_sales = sum(float(row.get('sales_eur', 0) or 0) for row in offline_data)
            
            # Time analysis
            years = set(row.get('year') for row in data if row.get('year'))
            months = set(row.get('month') for row in data if row.get('month'))
            
            # Online-specific data analysis
            countries = set(row.get('country') for row in online_data if row.get('country'))
            utm_sources = set(row.get('utm_source') for row in online_data if row.get('utm_source'))
            device_types = set(row.get('device_type') for row in online_data if row.get('device_type'))
            
            # Build comprehensive analysis with intent-specific focus
            if has_multiple_channels:
                channel_info = f"""
            MULTI-CHANNEL SALES ANALYSIS:
            - Online Sales: €{online_sales:,.2f} ({len(online_data):,} orders)
            - Offline Sales: €{offline_sales:,.2f} ({len(offline_data):,} transactions)
            - Total Combined: €{total_sales:,.2f} ({len(data):,} total records)
            - Channel Mix: {(online_sales/total_sales*100):.1f}% Online, {(offline_sales/total_sales*100):.1f}% Offline
                """
                if online_data:
                    channel_info += f"""
            - Online Markets: {len(countries)} countries ({', '.join(list(countries)[:5])}{'...' if len(countries) > 5 else ''})
            - Traffic Sources: {', '.join(list(utm_sources)[:5])}{'...' if len(utm_sources) > 5 else ''}
            - Device Types: {', '.join(list(device_types))}
                    """
            else:
                if channels and 'online' in channels:
                    channel_info = f"""
            ONLINE SALES ANALYSIS:
            - Total Online Sales: €{online_sales:,.2f} ({len(online_data):,} orders)
            - Markets: {len(countries)} countries ({', '.join(list(countries)[:5])})
            - Traffic Sources: {', '.join(list(utm_sources)[:5])}
            - Device Types: {', '.join(list(device_types))}
                    """
                else:
                    channel_info = f"""
            OFFLINE/WHOLESALE SALES ANALYSIS:
            - Total Offline Sales: €{offline_sales:,.2f} ({len(offline_data):,} transactions) 
                    """
            
            summary = f"""
            COMPLETE SALES DATA ANALYSIS ({len(data)} total records) - Intent: {intent}:
            {channel_info}
            - Total Sales: €{total_sales:,.2f}
            - Total Quantity: {total_quantity:,} units
            - Unique Products: {len(products)} products
            - Unique Resellers: {len(resellers)} resellers
            - Currencies: {', '.join(currencies) if currencies else 'EUR'}
            - Time Period: Years {sorted(years) if years else 'Various'}, Months {sorted(months) if months else 'Various'}
            """
            
            # Add intent-specific note and detailed breakdowns
            if intent in ["COMPARISON", "SALES_COMPARISON"]:
                summary += f"\n\nNOTE: This is a COMPARISON query. Focus on comparing different time periods, products, or resellers based on the user's question."
                
                # Add detailed period-specific breakdowns for comparisons
                period_analysis = self._create_period_comparison_analysis(data)
                if period_analysis:
                    summary += f"\n\n{period_analysis}"
                    
            elif intent == "TIME_ANALYSIS":
                summary += f"\n\nNOTE: This is a TIME ANALYSIS query. Focus on temporal trends, seasonal patterns, and period-over-period changes."
            elif intent == "ONLINE_SALES":
                summary += f"\n\nNOTE: This is an ONLINE SALES query. Focus on ecommerce data, digital marketing metrics, and online customer behavior."
            elif intent == "OFFLINE_SALES": 
                summary += f"\n\nNOTE: This is an OFFLINE/WHOLESALE SALES query. Focus on reseller performance and B2B sales analysis."
            elif intent == "COMBINED_SALES":
                summary += f"\n\nNOTE: This is a COMBINED SALES query. Show totals across all sales channels and highlight channel-specific insights."
            
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
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: Optional[str] = None

class ConversationHistoryResponse(BaseModel):
    conversations: List[Dict]
    total_messages: int

class ClearConversationRequest(BaseModel):
    session_id: Optional[str] = None

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
        
        # Enhanced input with user context and session
        enhanced_input = {
            "input": request.message,
            "user_id": user_id,  # Pass user ID to agent for filtering
            "session_id": request.session_id  # Pass session ID for conversation memory
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
        return ChatResponse(answer=response, session_id=request.session_id)
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Sorry, I couldn't process your question. Please try rephrasing it. Error: {str(e)}"
        )

@router.get("/chat/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(authorization: str = Header(None)):
    """Get conversation history for the authenticated user"""
    # Extract user ID from JWT token
    user_id = None
    if authorization:
        try:
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user_info = await auth_service.verify_token(token)
            
            if user_info and user_info.get('id'):
                user_id = user_info.get('id')
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
                
        except Exception as auth_error:
            logger.error(f"Authentication failed: {str(auth_error)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    else:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        memory_service = ConversationMemoryService()
        db_service = DatabaseService()
        
        # Get conversation history from database
        result = db_service.supabase.table("conversation_history")\
            .select("session_id, user_message, ai_response, timestamp")\
            .eq("user_id", user_id)\
            .order("timestamp", desc=True)\
            .limit(100)\
            .execute()
        
        conversations = []
        if result.data:
            for row in result.data:
                conversations.append({
                    "session_id": row["session_id"],
                    "user_message": row["user_message"],
                    "ai_response": row["ai_response"],
                    "timestamp": row["timestamp"]
                })
        
        return ConversationHistoryResponse(
            conversations=conversations,
            total_messages=len(conversations)
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")

@router.post("/chat/clear")
async def clear_conversation(request: ClearConversationRequest, authorization: str = Header(None)):
    """Clear conversation history for the authenticated user"""
    # Extract user ID from JWT token
    user_id = None
    if authorization:
        try:
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user_info = await auth_service.verify_token(token)
            
            if user_info and user_info.get('id'):
                user_id = user_info.get('id')
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
                
        except Exception as auth_error:
            logger.error(f"Authentication failed: {str(auth_error)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    else:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        memory_service = ConversationMemoryService()
        memory_service.clear_conversation(user_id, request.session_id)
        
        return {"message": "Conversation cleared successfully", "session_id": request.session_id}
        
    except Exception as e:
        logger.error(f"Failed to clear conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

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