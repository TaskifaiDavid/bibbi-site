025-07-21 22:03:23,173 - app.api.chat - WARNING - DATABASE_URL not available, using Supabase REST API fallback
2025-07-21 22:03:23,209 - app.api.chat - INFO - ✅ Supabase REST API fallback initialized successfully
2025-07-21 22:03:23,209 - app.api.chat - INFO - 🔄 Using Supabase REST API agent (no direct SQL)
2025-07-21 22:03:23,244 - app.api.chat - INFO - ==================================================
2025-07-21 22:03:23,244 - app.api.chat - INFO - 🤖 CHAT DEBUG MODE ENABLED
2025-07-21 22:03:23,244 - app.api.chat - INFO - 📝 User message: what was the best selling product in may 2025?
2025-07-21 22:03:23,244 - app.api.chat - INFO - 👤 User ID: 26d3c1b7-d944-42a0-9336-e68b1b32ebbf
2025-07-21 22:03:23,244 - app.api.chat - INFO - ==================================================
2025-07-21 22:03:23,245 - app.api.chat - INFO - 📊 Fetching user-specific sales data...
2025-07-21 22:03:23,245 - app.api.chat - INFO - 📅 Years filter detected: [2025]
2025-07-21 22:03:23,246 - app.api.chat - INFO - 📅 Months filter detected: [5]
2025-07-21 22:03:23,246 - app.api.chat - INFO - 🔍 TEMPORARY DEBUG: Testing fallback mode to check for multi-reseller data...
2025-07-21 22:03:23,464 - httpx - INFO - HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/rest/v1/sellout_entries2?select=functional_name%2C%20reseller%2C%20sales_eur%2C%20quantity%2C%20month%2C%20year%2C%20product_ean%2C%20currency&year=eq.2025&month=eq.5&order=created_at.desc&limit=5000 "HTTP/2 200 OK"
2025-07-21 22:03:23,467 - app.api.chat - INFO - 🔍 DEBUG FALLBACK: Found 98 total records across ALL users
2025-07-21 22:03:23,467 - app.api.chat - INFO - 🔍 DEBUG FALLBACK: Resellers in ALL data: ['Galilu', 'Liberty'] (2 unique)
2025-07-21 22:03:23,467 - app.api.chat - INFO - 🔍 DEBUG FALLBACK: Total quantity across ALL users: 383 units
2025-07-21 22:03:23,467 - app.api.chat - INFO - 📅 Applied single year filter: 2025
2025-07-21 22:03:23,467 - app.api.chat - INFO - 📅 Applied single month filter: 5
2025-07-21 22:03:23,518 - httpx - INFO - HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/rest/v1/sellout_entries2?select=functional_name%2C%20reseller%2C%20sales_eur%2C%20quantity%2C%20month%2C%20year%2C%20product_ean%2C%20currency%2C%20uploads%21inner%28user_id%29&uploads.user_id=eq.26d3c1b7-d944-42a0-9336-e68b1b32ebbf&year=eq.2025&month=eq.5&order=created_at.desc&limit=5000 "HTTP/2 200 OK"
2025-07-21 22:03:23,520 - app.api.chat - INFO - ✅ Found 77 records for user 26d3c1b7-d944-42a0-9336-e68b1b32ebbf (years: [2025], months: [5])
2025-07-21 22:03:23,520 - app.api.chat - INFO - 🧹 Cleaned data: 77 records
2025-07-21 22:03:23,520 - app.api.chat - INFO - 🏢 Resellers found in dataset: ['Liberty'] (1 unique)
2025-07-21 22:03:23,520 - app.api.chat - INFO - 📊 Record distribution by reseller: {'Liberty': 77}
2025-07-21 22:03:23,520 - app.api.chat - INFO - 📈 Sample record: {'functional_name': 'BBSB100', 'reseller': 'Liberty', 'sales_eur': 261.0, 'quantity': 1, 'month': 5, 'year': 2025, 'product_ean': '7350154320053', 'currency': 'GBP'}
2025-07-21 22:03:23,521 - app.api.chat - INFO - 🎯 Detected intent: TIME_ANALYSIS
2025-07-21 22:03:23,521 - app.api.chat - INFO - 📋 Data summary length: 1097 characters
2025-07-21 22:03:23,521 - app.api.chat - INFO - 📋 Data summary preview: 
            COMPLETE SALES DATA ANALYSIS (77 total records) - Intent: TIME_ANALYSIS:
            - Total Sales: €47,092.87
            - Total Quantity: 308 units
            - Unique Products: 23 products
            - Unique Resellers: 1 resellers
            - Currencies: GBP
            - Time Period: Years [2025], Months [5]
            

NOTE: This is a TIME ANALYSIS query. Focus on temporal trends, seasonal patterns, and period-over-period changes.

COMPLETE RESELLER ANALYSIS:
- Liberty:...
2025-07-21 22:03:23,521 - app.api.chat - INFO - 🔍 Sending to LLM for analysis...
2025-07-21 22:03:27,093 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-07-21 22:03:27,112 - app.api.chat - INFO - ✅ LLM response generated: 136 characters
2025-07-21 22:03:27,112 - app.api.chat - INFO - ==================================================
2025-07-21 22:03:27,113 - app.api.chat - INFO - Agent response generated successfully: 136 characters
INFO:     127.0.0.1:51922 - "POST /api/chat HTTP/1.1" 200 OK