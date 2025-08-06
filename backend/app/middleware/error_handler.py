"""
Enhanced error handling middleware for comprehensive error management
"""
import logging
import traceback
import uuid
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from app.utils.logging_config import LoggingContext, get_logger

logger = get_logger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling middleware with logging and monitoring"""
    
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle requests with comprehensive error handling"""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get user ID if available (from auth header)
        user_id = None
        try:
            auth_header = request.headers.get("authorization")
            if auth_header:
                # This is a simplified extraction - you might want to decode JWT properly
                user_id = self._extract_user_id_from_token(auth_header)
        except Exception:
            pass  # Continue without user ID if extraction fails
        
        # Set logging context
        with LoggingContext(request_id=request_id, user_id=user_id):
            logger.info(
                f"Request started: {request.method} {request.url}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": self._get_client_ip(request)
                }
            )
            
            start_time = datetime.utcnow()
            
            try:
                # Process request
                response = await call_next(request)
                
                # Log successful response
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    f"Request completed successfully",
                    extra={
                        "status_code": response.status_code,
                        "duration_seconds": duration
                    }
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as exc:
                # Log error with full context
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Request failed: {str(exc)}",
                    extra={
                        "error_type": type(exc).__name__,
                        "duration_seconds": duration,
                        "method": request.method,
                        "url": str(request.url)
                    },
                    exc_info=True
                )
                
                # Return appropriate error response
                return await self._create_error_response(exc, request_id)
    
    def _extract_user_id_from_token(self, auth_header: str) -> Optional[str]:
        """Extract user ID from authorization token"""
        try:
            # This is a simplified version - implement proper JWT decoding
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # You would decode JWT here and extract user ID
                # For now, return None to avoid errors
                return None
        except Exception:
            pass
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _create_error_response(self, exc: Exception, request_id: str) -> JSONResponse:
        """Create appropriate error response based on exception type"""
        
        # Define error response structure
        error_response = {
            "error": True,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        # Handle different exception types
        if hasattr(exc, 'status_code'):
            # FastAPI HTTPException or similar
            status_code = exc.status_code
            error_response["message"] = getattr(exc, 'detail', str(exc))
            error_response["error_code"] = "HTTP_ERROR"
        
        elif isinstance(exc, ValueError):
            status_code = 400
            error_response["message"] = "Invalid input data"
            error_response["error_code"] = "VALIDATION_ERROR"
            if self.debug:
                error_response["details"] = str(exc)
        
        elif isinstance(exc, KeyError):
            status_code = 400
            error_response["message"] = "Missing required field"
            error_response["error_code"] = "MISSING_FIELD"
            if self.debug:
                error_response["details"] = f"Missing key: {str(exc)}"
        
        elif isinstance(exc, ConnectionError):
            status_code = 503
            error_response["message"] = "Service temporarily unavailable"
            error_response["error_code"] = "SERVICE_UNAVAILABLE"
        
        elif isinstance(exc, TimeoutError):
            status_code = 504
            error_response["message"] = "Request timeout"
            error_response["error_code"] = "TIMEOUT"
        
        else:
            # Generic server error
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            error_response["message"] = "Internal server error"
            error_response["error_code"] = "INTERNAL_ERROR"
        
        # Add debug information if enabled
        if self.debug:
            error_response["debug"] = {
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__)
            }
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )

# Custom exception classes
class DatabaseError(Exception):
    """Database operation error"""
    pass

class ChatProcessingError(Exception):
    """Chat processing error"""
    pass

class ValidationError(Exception):
    """Data validation error"""
    pass