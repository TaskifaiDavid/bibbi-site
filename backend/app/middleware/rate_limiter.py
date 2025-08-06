"""
Rate limiting middleware for API performance and security
"""
import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from app.utils.logging_config import get_logger
import redis
import os

logger = get_logger(__name__)

class InMemoryRateLimiter:
    """In-memory rate limiter for development/single instance"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check if request is allowed and return remaining requests"""
        async with self.lock:
            now = time.time()
            window_start = now - window
            
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < window_start:
                self.requests[key].popleft()
            
            # Check if limit exceeded
            current_requests = len(self.requests[key])
            if current_requests >= limit:
                return False, 0
            
            # Add current request
            self.requests[key].append(now)
            remaining = limit - current_requests - 1
            
            return True, remaining

class RedisRateLimiter:
    """Redis-based rate limiter for production/distributed systems"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = None
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
            except ImportError:
                logger.warning("Redis not available, falling back to in-memory limiter")
    
    async def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check if request is allowed using Redis sliding window"""
        if not self.redis_client:
            return True, limit  # Allow all if Redis not available
        
        try:
            now = time.time()
            pipeline = self.redis_client.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(now): now})
            
            # Set expiry
            pipeline.expire(key, window + 1)
            
            results = pipeline.execute()
            current_count = results[1]
            
            if current_count >= limit:
                return False, 0
            
            remaining = limit - current_count - 1
            return True, remaining
            
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            return True, limit  # Allow on error

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with different limits for different endpoints"""
    
    def __init__(
        self,
        app,
        default_limit: int = 100,
        default_window: int = 60,
        redis_url: str = None
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        
        # Initialize rate limiter
        if redis_url:
            self.limiter = RedisRateLimiter(redis_url)
        else:
            self.limiter = InMemoryRateLimiter()
        
        # Define endpoint-specific limits
        self.endpoint_limits = {
            "/api/chat": {"limit": 20, "window": 60},  # 20 requests per minute for chat
            "/api/upload": {"limit": 10, "window": 60},  # 10 uploads per minute
            "/api/auth/login": {"limit": 5, "window": 300},  # 5 login attempts per 5 minutes
            "/api/auth/register": {"limit": 3, "window": 3600},  # 3 registrations per hour
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply rate limiting to requests"""
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get endpoint limits
        path = request.url.path
        limits = self._get_limits_for_path(path)
        
        # Create rate limit key
        rate_limit_key = f"rate_limit:{client_id}:{path}"
        
        # Check rate limit
        allowed, remaining = await self.limiter.is_allowed(
            rate_limit_key, 
            limits["limit"], 
            limits["window"]
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}",
                extra={
                    "client_id": client_id,
                    "path": path,
                    "limit": limits["limit"],
                    "window": limits["window"]
                }
            )
            
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limits['limit']} per {limits['window']} seconds",
                    "retry_after": limits["window"]
                },
                headers={
                    "Retry-After": str(limits["window"]),
                    "X-RateLimit-Limit": str(limits["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + limits["window"]))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limits["limit"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + limits["window"]))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from auth first
        user_id = None
        try:
            auth_header = request.headers.get("authorization")
            if auth_header:
                # You would extract user ID from JWT here
                pass
        except Exception:
            pass
        
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        if hasattr(request, "client") and request.client:
            return f"ip:{request.client.host}"
        
        return "unknown"
    
    def _get_limits_for_path(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for a specific path"""
        # Check for exact match first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for pattern matches
        for pattern, limits in self.endpoint_limits.items():
            if path.startswith(pattern):
                return limits
        
        # Return default limits
        return {"limit": self.default_limit, "window": self.default_window}

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to responses"""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Only add HSTS in production over HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response