"""
Caching middleware for improved API performance
"""
import hashlib
import json
import pickle
import time
from typing import Dict, Optional, Any, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.utils.logging_config import get_logger
import redis
import os

logger = get_logger(__name__)

class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.max_size = max_size
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expires_at = self.cache[key]
            if time.time() < expires_at:
                return value
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        # Simple LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        expires_at = time.time() + ttl
        self.cache[key] = (value, expires_at)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    async def clear(self):
        """Clear all cache entries"""
        self.cache.clear()

class RedisCache:
    """Redis-based cache for production/distributed systems"""
    
    def __init__(self, redis_url: str):
        self.redis_client = None
        try:
            import redis
            self.redis_client = redis.from_url(redis_url)
        except ImportError:
            logger.warning("Redis not available for caching")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in Redis cache with TTL"""
        if not self.redis_client:
            return
        
        try:
            data = pickle.dumps(value)
            self.redis_client.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from Redis cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def clear(self):
        """Clear all cache entries (use with caution)"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

class CachingMiddleware(BaseHTTPMiddleware):
    """Caching middleware for GET requests"""
    
    def __init__(
        self,
        app,
        default_ttl: int = 300,
        redis_url: str = None,
        max_cache_size: int = 1000
    ):
        super().__init__(app)
        self.default_ttl = default_ttl
        
        # Initialize cache backend
        if redis_url:
            self.cache = RedisCache(redis_url)
        else:
            self.cache = InMemoryCache(max_cache_size)
        
        # Define cacheable endpoints and their TTLs
        self.cacheable_endpoints = {
            "/api/dashboards": {"ttl": 60, "vary_by_user": True},  # 1 minute
            "/api/status": {"ttl": 30, "vary_by_user": True},      # 30 seconds
            "/health": {"ttl": 30, "vary_by_user": False},         # 30 seconds
            "/api/chat/health": {"ttl": 60, "vary_by_user": False}, # 1 minute
        }
        
        # Endpoints to never cache
        self.no_cache_endpoints = {
            "/api/chat",         # Chat responses should be unique
            "/api/upload",       # File uploads
            "/api/auth",         # Authentication endpoints
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply caching logic to GET requests"""
        
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        path = request.url.path
        
        # Check if endpoint should not be cached
        if any(path.startswith(endpoint) for endpoint in self.no_cache_endpoints):
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        
        # Check if endpoint is cacheable
        cache_config = self._get_cache_config(path)
        if not cache_config:
            return await call_next(request)
        
        # Generate cache key
        cache_key = await self._generate_cache_key(request, cache_config)
        
        # Try to get from cache
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for {path}", extra={"cache_key": cache_key})
            
            # Return cached response
            response = JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response.get("headers", {})
            )
            response.headers["X-Cache"] = "HIT"
            response.headers["Cache-Control"] = f"public, max-age={cache_config['ttl']}"
            return response
        
        # Cache miss - process request
        logger.debug(f"Cache miss for {path}", extra={"cache_key": cache_key})
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(cache_key, response, cache_config)
        
        # Add cache headers
        response.headers["X-Cache"] = "MISS"
        response.headers["Cache-Control"] = f"public, max-age={cache_config['ttl']}"
        
        return response
    
    def _get_cache_config(self, path: str) -> Optional[Dict[str, Any]]:
        """Get cache configuration for a path"""
        # Check for exact match
        if path in self.cacheable_endpoints:
            return self.cacheable_endpoints[path]
        
        # Check for prefix match
        for endpoint, config in self.cacheable_endpoints.items():
            if path.startswith(endpoint):
                return config
        
        return None
    
    async def _generate_cache_key(self, request: Request, cache_config: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Include user ID if cache varies by user
        if cache_config.get("vary_by_user", False):
            user_id = self._get_user_id(request)
            if user_id:
                key_parts.append(f"user:{user_id}")
        
        # Include specific headers if needed
        vary_headers = cache_config.get("vary_by_headers", [])
        for header in vary_headers:
            header_value = request.headers.get(header.lower())
            if header_value:
                key_parts.append(f"{header}:{header_value}")
        
        # Create hash of all parts
        key_string = "|".join(key_parts)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"api_cache:{cache_key}"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request for cache keying"""
        try:
            auth_header = request.headers.get("authorization")
            if auth_header:
                # You would extract user ID from JWT here
                # For now, return None to avoid errors
                pass
        except Exception:
            pass
        
        return None
    
    async def _cache_response(
        self,
        cache_key: str,
        response: Response,
        cache_config: Dict[str, Any]
    ):
        """Cache the response"""
        try:
            # Read response content
            if isinstance(response, JSONResponse):
                # For JSON responses, we can cache the content directly
                cached_data = {
                    "content": json.loads(response.body.decode()),
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
                
                ttl = cache_config.get("ttl", self.default_ttl)
                await self.cache.set(cache_key, cached_data, ttl)
                
                logger.debug(
                    f"Response cached",
                    extra={
                        "cache_key": cache_key,
                        "ttl": ttl,
                        "size_bytes": len(response.body)
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")

class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """Compress responses to improve performance"""
    
    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply response compression"""
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # Only compress text responses above minimum size
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in ["text/", "application/json", "application/xml"]):
            return response
        
        # Check response size
        if hasattr(response, 'body') and len(response.body) < self.minimum_size:
            return response
        
        # Compress response (simplified - you might want to use a proper compression library)
        try:
            import gzip
            if hasattr(response, 'body'):
                compressed_body = gzip.compress(response.body)
                response.body = compressed_body
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Content-Length"] = str(len(compressed_body))
        except Exception as e:
            logger.error(f"Compression failed: {e}")
        
        return response