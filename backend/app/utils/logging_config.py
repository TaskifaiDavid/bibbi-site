"""
Enhanced logging configuration for production-ready logging
"""
import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Dict, Any
import traceback
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 
                'relativeCreated', 'thread', 'threadName', 'processName', 'process',
                'message', 'exc_info', 'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class RequestContextFilter(logging.Filter):
    """Add request context to log records"""
    
    def __init__(self):
        super().__init__()
        self.request_id = None
        self.user_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context to the record"""
        record.request_id = getattr(self, 'request_id', None)
        record.user_id = getattr(self, 'user_id', None)
        return True
    
    def set_context(self, request_id: str = None, user_id: str = None):
        """Set request context"""
        self.request_id = request_id
        self.user_id = user_id

def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = True,
    development_mode: bool = False
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (optional)
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        json_format: Whether to use JSON formatting
        development_mode: If True, uses cleaner formatting for development
    
    Returns:
        Configured root logger
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatters
    if development_mode:
        # Simple, clean format for development
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
    elif json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s '
            '[%(module)s:%(funcName)s:%(lineno)d] '
            '(request_id=%(request_id)s, user_id=%(user_id)s)'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Only add request context filter in production mode
    if not development_mode:
        console_handler.addFilter(RequestContextFilter())
    
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors)
    if log_file:
        error_log_file = str(log_path.with_suffix('.error.log'))
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(error_handler)
    
    # Configure specific loggers for development
    if development_mode:
        # Reduce verbosity of third-party loggers
        logging.getLogger('watchfiles.main').setLevel(logging.WARNING)
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
        logging.getLogger('uvicorn.error').setLevel(logging.INFO)
        logging.getLogger('multipart').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        # Keep app loggers at specified level
        logging.getLogger('app').setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

def log_function_call(func):
    """Decorator to log function calls with parameters and results"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(
            f"Calling {func.__name__}",
            extra={
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
        )
        
        try:
            result = func(*args, **kwargs)
            logger.debug(
                f"Function {func.__name__} completed successfully",
                extra={"function": func.__name__}
            )
            return result
        except Exception as e:
            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                extra={
                    "function": func.__name__,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
    
    return wrapper

class LoggingContext:
    """Context manager for setting logging context"""
    
    def __init__(self, request_id: str = None, user_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.old_context = {}
    
    def __enter__(self):
        # Set context for all handlers with RequestContextFilter
        for handler in logging.getLogger().handlers:
            for filter_obj in handler.filters:
                if isinstance(filter_obj, RequestContextFilter):
                    self.old_context[filter_obj] = (filter_obj.request_id, filter_obj.user_id)
                    filter_obj.set_context(self.request_id, self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        for filter_obj, (old_request_id, old_user_id) in self.old_context.items():
            filter_obj.set_context(old_request_id, old_user_id)