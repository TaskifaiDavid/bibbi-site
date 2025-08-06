"""
Security utilities for enhanced API security
"""
import hashlib
import secrets
import re
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from app.utils.logging_config import get_logger
from app.utils.config import get_settings

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordValidator:
    """Enhanced password validation"""
    
    def __init__(self):
        self.min_length = 8
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        warnings = []
        
        # Length checks
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        elif len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        # Character requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special and not re.search(f'[{re.escape(self.special_chars)}]', password):
            errors.append(f"Password must contain at least one special character: {self.special_chars}")
        
        # Common password checks
        common_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'abc123',
            r'admin'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                warnings.append("Password contains common patterns that are easy to guess")
                break
        
        # Sequential characters
        if re.search(r'(.)\1{2,}', password):
            warnings.append("Avoid repeating the same character multiple times")
        
        # Calculate strength score
        score = 0
        if len(password) >= self.min_length:
            score += 20
        if re.search(r'[A-Z]', password):
            score += 20
        if re.search(r'[a-z]', password):
            score += 20
        if re.search(r'\d', password):
            score += 20
        if re.search(f'[{re.escape(self.special_chars)}]', password):
            score += 20
        
        # Bonus points for length
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Deduct points for warnings
        score -= len(warnings) * 10
        
        strength = "Very Weak"
        if score >= 80:
            strength = "Very Strong"
        elif score >= 60:
            strength = "Strong"
        elif score >= 40:
            strength = "Medium"
        elif score >= 20:
            strength = "Weak"
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": max(0, min(100, score)),
            "strength": strength
        }

class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', input_str)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        
        # RFC 5322 regex (simplified)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename for upload security"""
        if not filename or len(filename) > 255:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # Check for dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js']
        filename_lower = filename.lower()
        for ext in dangerous_extensions:
            if filename_lower.endswith(ext):
                return False
        
        return True
    
    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """Sanitize SQL identifier (table/column names)"""
        # Only allow alphanumeric characters and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        
        # Limit length
        if len(sanitized) > 63:  # PostgreSQL limit
            sanitized = sanitized[:63]
        
        return sanitized

class TokenManager:
    """Manage JWT tokens and API keys"""
    
    def __init__(self):
        settings = get_settings()
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def generate_api_key(self, prefix: str = "ak_") -> str:
        """Generate secure API key"""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}{random_part}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

class RateLimitTracker:
    """Track rate limits and suspicious activity"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.suspicious_ips: Dict[str, datetime] = {}
    
    def record_failed_attempt(self, identifier: str) -> bool:
        """Record failed attempt and return if IP should be blocked"""
        now = datetime.utcnow()
        
        # Initialize or clean old attempts
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Remove attempts older than 15 minutes
        cutoff = now - timedelta(minutes=15)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        # Add current attempt
        self.failed_attempts[identifier].append(now)
        
        # Check if threshold exceeded (5 attempts in 15 minutes)
        if len(self.failed_attempts[identifier]) >= 5:
            self.suspicious_ips[identifier] = now
            logger.warning(
                f"Suspicious activity detected from {identifier}",
                extra={"identifier": identifier, "attempts": len(self.failed_attempts[identifier])}
            )
            return True
        
        return False
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked"""
        if identifier not in self.suspicious_ips:
            return False
        
        # Check if block has expired (1 hour)
        block_time = self.suspicious_ips[identifier]
        if datetime.utcnow() - block_time > timedelta(hours=1):
            del self.suspicious_ips[identifier]
            return False
        
        return True

# Security utilities
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)

def constant_time_compare(a: str, b: str) -> bool:
    """Compare strings in constant time to prevent timing attacks"""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0

# Security audit utilities
class SecurityAuditor:
    """Audit security configuration and practices"""
    
    @staticmethod
    def audit_cors_config(allowed_origins: List[str]) -> Dict[str, Any]:
        """Audit CORS configuration"""
        issues = []
        warnings = []
        
        if "*" in allowed_origins:
            issues.append("Wildcard (*) in CORS origins is dangerous in production")
        
        for origin in allowed_origins:
            if origin.startswith("http://") and "localhost" not in origin:
                warnings.append(f"HTTP origin detected: {origin} (consider HTTPS)")
        
        return {
            "secure": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    @staticmethod
    def audit_jwt_config(secret_key: str) -> Dict[str, Any]:
        """Audit JWT configuration"""
        issues = []
        warnings = []
        
        if len(secret_key) < 32:
            issues.append("JWT secret key is too short (minimum 32 characters)")
        
        if secret_key.isalnum():
            warnings.append("JWT secret key lacks special characters")
        
        return {
            "secure": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }

# Global instances
password_validator = PasswordValidator()
input_sanitizer = InputSanitizer()
token_manager = TokenManager()
rate_limit_tracker = RateLimitTracker()
security_auditor = SecurityAuditor()