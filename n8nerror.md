18:58:42 [INFO] app.middleware.error_handler: Request started: DELETE http://localhost:8000/api/dashboards/configs/51783730-50a5-4faf-8c3a-d1d10d069726
18:58:42 [INFO] app.services.auth_service: Attempting token verification for token ending with: ...ngQE
18:58:43 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/auth/v1/user "HTTP/2 200 OK"
18:58:43 [INFO] app.services.auth_service: Token verification successful for user: user@email.com
18:58:43 [INFO] app.api.dashboard: 🗑️ API: Starting dashboard deletion process
18:58:43 [INFO] app.api.dashboard: 🗑️ API: Config ID: 51783730-50a5-4faf-8c3a-d1d10d069726
18:58:43 [INFO] app.api.dashboard: 🗑️ API: User: user@email.com (ID: 26d3c1b7-d944-42a0-9336-e68b1b32ebbf)
18:58:43 [INFO] app.api.dashboard: 🗑️ API: Executing delete query with params: (51783730-50a5-4faf-8c3a-d1d10d069726, 26d3c1b7-d944-42a0-9336-e68b1b32ebbf)
18:58:43 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/rest/v1/dashboard_configs?select=%2A&id=eq.51783730-50a5-4faf-8c3a-d1d10d069726&user_id=eq.26d3c1b7-d944-42a0-9336-e68b1b32ebbf "HTTP/2 200 OK"
18:58:43 [INFO] app.api.dashboard: 🗑️ API: Delete query result: {'id': '51783730-50a5-4faf-8c3a-d1d10d069726', 'user_id': '26d3c1b7-d944-42a0-9336-e68b1b32ebbf', 'dashboard_name': 's', 'dashboard_type': 'looker', 'dashboard_url': 'https://lookerstudio.google.com/embed/reporting/8c4e6b01-59f8-4d6a-b7bb-cc7f49945f47/page/klnQF', 'authentication_method': 'none', 'authentication_config': {}, 'permissions': [], 'is_active': True, 'created_at': '2025-08-06T15:06:12.078403+00:00', 'updated_at': '2025-08-06T15:06:12.078403+00:00'}
18:58:43 [INFO] app.api.dashboard: ✅ API: Successfully deleted dashboard config 51783730-50a5-4faf-8c3a-d1d10d069726 for user user@email.com
18:58:43 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/rest/v1/dashboard_configs?select=%2A&id=eq.51783730-50a5-4faf-8c3a-d1d10d069726&user_id=eq.26d3c1b7-d944-42a0-9336-e68b1b32ebbf "HTTP/2 200 OK"
18:58:43 [INFO] app.api.dashboard: 🔍 API: Post-deletion verification result: {'id': '51783730-50a5-4faf-8c3a-d1d10d069726', 'user_id': '26d3c1b7-d944-42a0-9336-e68b1b32ebbf', 'dashboard_name': 's', 'dashboard_type': 'looker', 'dashboard_url': 'https://lookerstudio.google.com/embed/reporting/8c4e6b01-59f8-4d6a-b7bb-cc7f49945f47/page/klnQF', 'authentication_method': 'none', 'authentication_config': {}, 'permissions': [], 'is_active': True, 'created_at': '2025-08-06T15:06:12.078403+00:00', 'updated_at': '2025-08-06T15:06:12.078403+00:00'}
18:58:43 [ERROR] app.api.dashboard: ⚠️ API: WARNING - Dashboard config still exists after deletion!
18:58:43 [INFO] app.middleware.error_handler: Request completed successfully
18:58:43 [INFO] app.middleware.error_handler: Request started: GET http://localhost:8000/api/dashboards/configs
18:58:43 [INFO] app.services.auth_service: Attempting token verification for token ending with: ...ngQE
18:58:43 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/auth/v1/user "HTTP/2 200 OK"
18:58:43 [INFO] app.services.auth_service: Token verification successful for user: user@email.com
18:58:44 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/rest/v1/dashboard_configs?select=%2A&user_id=eq.26d3c1b7-d944-42a0-9336-e68b1b32ebbf&order=created_at.desc "HTTP/2 200 OK"
18:58:44 [INFO] app.middleware.error_handler: Request completed successfully
18:58:45 [INFO] app.middleware.error_handler: Request started: GET http://localhost:8000/api/status/uploads
18:58:45 [INFO] app.api.auth: get_current_user called
18:58:45 [INFO] app.api.auth: Authorization header: Present
18:58:45 [INFO] app.api.auth: Extracted token length: 722
18:58:45 [INFO] app.services.auth_service: Attempting token verification for token ending with: ...ngQE
18:58:45 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/auth/v1/user "HTTP/2 200 OK"
18:58:45 [INFO] app.services.auth_service: Token verification successful for user: user@email.com
18:58:45 [INFO] app.api.auth: Successfully authenticated user: user@email.com
18:58:45 [INFO] httpx: HTTP Request: GET https://edckqdrbgtnnjfnshjfq.supabase.co/rest/v1/uploads?select=%2A&user_id=eq.26d3c1b7-d944-42a0-9336-e68b1b32ebbf&order=uploaded_at.desc "HTTP/2 200 OK"
18:58:45 [INFO] app.middleware.error_handler: Request completed successfully
