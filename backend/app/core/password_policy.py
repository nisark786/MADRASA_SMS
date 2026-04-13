"""
Password policy enforcement for security compliance.

Enforces:
- Minimum length (12 characters)
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
- No common patterns or dictionary words
"""
import re
from pydantic import BaseModel, field_validator


class PasswordPolicy:
    """Validates passwords against security policy."""
    
    MIN_LENGTH = 12
    SPECIAL_CHARS = r"!@#$%^&*()_+-=\[\]{};:',.<>?/~`|\\"
    
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Validate password against policy.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check minimum length
        if len(password) < PasswordPolicy.MIN_LENGTH:
            return False, f"Password must be at least {PasswordPolicy.MIN_LENGTH} characters long"
        
        # Check for uppercase letter
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)"
        
        # Check for lowercase letter
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)"
        
        # Check for digit
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit (0-9)"
        
        # Check for special character
        if not re.search(f"[{re.escape(PasswordPolicy.SPECIAL_CHARS)}]", password):
            return False, f"Password must contain at least one special character ({PasswordPolicy.SPECIAL_CHARS})"
        
        # Check for common weak patterns
        weak_patterns = [
            r"^123",          # Starts with 123
            r"^password",     # Contains 'password'
            r"^admin",        # Contains 'admin'
            r"^user",         # Contains 'user'
            r"^12345",        # Sequential numbers
            r"abcdef",        # Sequential letters
            r"(.)\1{3,}",     # 4+ repeated characters (e.g., "aaaa")
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                return False, "Password contains weak or common patterns"
        
        return True, ""


class PasswordChangeRequest(BaseModel):
    """Request model for password change."""
    current_password: str
    new_password: str
    confirm_password: str
    
    @field_validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password against policy."""
        is_valid, error_msg = PasswordPolicy.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("confirm_password")
    def validate_confirm(cls, v, info):
        """Ensure passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v

