"""
Input validation and sanitization utilities for the AI assistant
"""
import re
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class InputValidator:
    """Validates and sanitizes user inputs"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|#|/\*|\*/)",
        r"(\bxp_\w+\b)",
        r"(\bsp_\w+\b)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    @classmethod
    def validate_message(cls, message: str, max_length: int = 1000) -> Dict[str, Any]:
        """Validate a user message"""
        errors = []
        warnings = []
        
        if not message or not message.strip():
            errors.append("Message cannot be empty")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        message = message.strip()
        
        # Check length
        if len(message) > max_length:
            errors.append(f"Message too long (max {max_length} characters)")
        
        # Check for SQL injection attempts
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                errors.append("Potentially malicious SQL detected")
                logger.warning(f"SQL injection attempt detected: {message[:100]}...")
                break
        
        # Check for XSS attempts
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                errors.append("Potentially malicious content detected")
                logger.warning(f"XSS attempt detected: {message[:100]}...")
                break
        
        # Check for excessive special characters
        special_chars = len(re.findall(r'[^\w\s]', message))
        if special_chars > len(message) * 0.3:  # More than 30% special chars
            warnings.append("Message contains many special characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized": cls.sanitize_message(message)
        }
    
    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """Sanitize a message by removing potentially harmful content"""
        if not message:
            return ""
        
        # Remove null bytes
        message = message.replace('\x00', '')
        
        # Remove control characters (except newlines and tabs)
        message = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', message)
        
        # Trim whitespace
        message = message.strip()
        
        return message
    
    @classmethod
    def validate_conversation_title(cls, title: str) -> Dict[str, Any]:
        """Validate a conversation title"""
        errors = []
        
        if not title or not title.strip():
            errors.append("Title cannot be empty")
            return {"valid": False, "errors": errors}
        
        title = title.strip()
        
        if len(title) > 100:
            errors.append("Title too long (max 100 characters)")
        
        if len(title) < 3:
            errors.append("Title too short (min 3 characters)")
        
        # Check for special characters
        if not re.match(r'^[\w\s\-.,!?]+$', title):
            errors.append("Title contains invalid characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "sanitized": cls.sanitize_message(title)
        }
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # DeepSeek API key format: sk- followed by alphanumeric characters
        return bool(re.match(r'^sk-[a-zA-Z0-9]+$', api_key))
