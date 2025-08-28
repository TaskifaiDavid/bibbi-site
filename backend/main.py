from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import auth, upload, status, email, dashboard, webhook, chat
from app.utils.config import get_settings
from app.utils.exceptions import AppException
import logging
import os
from datetime import datetime
from app.utils.logging_config import setup_logging
from app.middleware.error_handler import ErrorHandlingMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware, SecurityHeadersMiddleware
from app.middleware.caching import CachingMiddleware, ResponseCompressionMiddleware

# Setup enhanced logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "logs/app.log")
json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"  # Default to False for cleaner dev logs
development_mode = os.getenv("ENVIRONMENT", "development").lower() == "development"

setup_logging(
    log_level=log_level,
    log_file=log_file,
    json_format=json_logs,
    development_mode=development_mode
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Cleaning Pipeline API",
    description="API for uploading and cleaning Excel files",
    version="1.0.0"
)

settings = get_settings()

# Middleware stack (order is important!)
debug_mode = os.getenv("DEBUG", "false").lower() == "true"
redis_url = os.getenv("REDIS_URL")

# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Response compression
app.add_middleware(ResponseCompressionMiddleware)

# 3. Caching (before rate limiting)
app.add_middleware(CachingMiddleware, redis_url=redis_url)

# 4. Rate limiting
default_rate_limit = int(os.getenv("RATE_LIMIT_DEFAULT", "100"))
app.add_middleware(RateLimitMiddleware, 
                  default_limit=default_rate_limit,
                  redis_url=redis_url)

# 5. Error handling
app.add_middleware(ErrorHandlingMiddleware, debug=debug_mode)

# 6. CORS middleware (innermost, closest to application)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(email.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api/dashboards")
app.include_router(webhook.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Data Cleaning Pipeline API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/security/status")
async def security_status():
    """Security monitoring endpoint"""
    from app.utils.security import security_auditor
    
    # Basic security status
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "security_headers": "enabled",
        "rate_limiting": "enabled",
        "caching": "enabled",
        "error_handling": "enhanced",
        "logging": "structured"
    }
    
    # Add environment-specific warnings
    warnings = []
    if debug_mode:
        warnings.append("Debug mode is enabled")
    
    if not redis_url:
        warnings.append("Redis not configured - using in-memory caching/rate limiting")
    
    if warnings:
        status["warnings"] = warnings
    
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )