# 2FA IMPLEMENTATION - DETAILED CODE EXAMPLES

## 1. BACKEND DATABASE CHANGES

### User Model Addition
```python
# app/models/user.py - Add these fields

two_fa_enabled: Mapped[bool] = mapped_column(
    Boolean, default=False, index=True
)
two_fa_method: Mapped[str] = mapped_column(
    String(20), nullable=True
)  # "totp" or "sms"
totp_secret: Mapped[str] = mapped_column(
    String(255), nullable=True
)  # Encrypted TOTP secret
totp_backup_codes: Mapped[list] = mapped_column(
    JSON, nullable=True
)  # List of hashed backup codes
last_2fa_verification: Mapped[datetime] = mapped_column(
    DateTime(timezone.utc), nullable=True
)
```

### New TwoFAAuditLog Model
```python
# app/models/two_fa_audit_log.py (NEW FILE)

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TwoFAAuditLog(Base):
    __tablename__ = "two_fa_audit_logs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(50))  
    # "setup_initiated", "setup_confirmed", "verify_success",
    # "verify_failed", "disable", "regenerate_codes"
    method: Mapped[str] = mapped_column(String(20))  
    # "totp", "sms", "backup_code"
    ip_address: Mapped[str] = mapped_column(String(45))
    success: Mapped[bool] = mapped_column(Boolean)
    attempts: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
```

## 2. BACKEND SERVICE IMPLEMENTATIONS

### TOTP Service
```python
# app/core/totp.py (NEW FILE)

import secrets
import pyotp
import qrcode
from io import BytesIO
import base64

class TOTPService:
    """Manages TOTP (Time-based One-Time Password) operations."""
    
    # 6-digit codes, 30-second time step
    TIME_STEP = 30
    DIGITS = 6
    BACKUP_CODE_LENGTH = 8
    BACKUP_CODES_COUNT = 10
    
    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret (base32 encoded)."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_backup_codes(count: int = BACKUP_CODES_COUNT) -> list[str]:
        """Generate cryptographically secure backup codes."""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_urlsafe(BACKUP_CODE_LENGTH)[:BACKUP_CODE_LENGTH]
            codes.append(code)
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """Hash a backup code using bcrypt."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"])
        return pwd_context.hash(code)
    
    @staticmethod
    def verify_backup_code(plain: str, hashed: str) -> bool:
        """Verify a backup code against its hash (constant-time)."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"])
        return pwd_context.verify(plain, hashed)
    
    @staticmethod
    def verify_totp(secret: str, code: str, 
                   time_window: int = 1) -> bool:
        """
        Verify TOTP code against secret.
        
        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit OTP code from user
            time_window: Allow ±N time steps (default 1 = ±30 seconds)
        
        Returns:
            True if code is valid, False otherwise
        """
        totp = pyotp.TOTP(secret, interval=TOTPService.TIME_STEP)
        return totp.verify(code, valid_window=time_window)
    
    @staticmethod
    def generate_qr_url(secret: str, email: str, 
                       issuer: str = "Students DS") -> str:
        """
        Generate QR code URL for TOTP setup.
        
        Args:
            secret: Base32-encoded TOTP secret
            email: User''s email address
            issuer: App name to display in authenticator
        
        Returns:
            Data URL for QR code image
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 data URL
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
```

### Redis 2FA State Management
```python
# app/core/redis_client.py - Add these functions

async def cache_2fa_challenge(
    user_id: str, challenge_token: str, 
    method: str, ttl: int = 300
) -> None:
    """Store 2FA challenge token (5 minutes)."""
    key = f"2fa:challenge:{challenge_token}"
    data = json.dumps({"user_id": user_id, "method": method})
    await redis_client.setex(key, ttl, data)

async def get_2fa_challenge(challenge_token: str) -> dict | None:
    """Retrieve 2FA challenge data."""
    key = f"2fa:challenge:{challenge_token}"
    data = await redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

async def invalidate_2fa_challenge(challenge_token: str) -> None:
    """Delete 2FA challenge (after verification attempt)."""
    key = f"2fa:challenge:{challenge_token}"
    await redis_client.delete(key)

async def increment_2fa_attempts(user_id: str) -> int:
    """Increment failed 2FA attempts counter."""
    key = f"2fa:attempts:{user_id}"
    current = await redis_client.incr(key)
    if current == 1:
        # First attempt in window, set expiry (10 minutes)
        await redis_client.expire(key, 600)
    return current

async def reset_2fa_attempts(user_id: str) -> None:
    """Reset failed 2FA attempts after successful verification."""
    key = f"2fa:attempts:{user_id}"
    await redis_client.delete(key)

async def get_2fa_attempts(user_id: str) -> int:
    """Get current failed 2FA attempts."""
    key = f"2fa:attempts:{user_id}"
    value = await redis_client.get(key)
    return int(value) if value else 0
```

## 3. BACKEND ENDPOINTS

### Modified Login Endpoint (excerpt)
```python
# app/api/v1/auth.py - Modify existing login() function

@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Enhanced login with 2FA support."""
    
    # ... existing rate limiting and auth checks ...
    
    # NEW: Check if 2FA is enabled
    if user.two_fa_enabled:
        from app.core.security import create_2fa_challenge_token
        from app.core import redis_client as rc
        
        challenge_token = create_2fa_challenge_token()
        
        # Store challenge in Redis (5 minutes)
        await rc.cache_2fa_challenge(
            user_id=user.id,
            challenge_token=challenge_token,
            method=user.two_fa_method
        )
        
        # Return 202 Accepted (not authenticated yet)
        response = JSONResponse(
            {
                "status": "2fa_required",
                "challenge_token": challenge_token,
                "method": user.two_fa_method,
                "message": f"Enter the 6-digit code from your authenticator",
            },
            status_code=202
        )
        return response
    
    # ... existing token generation for non-2FA users ...
```

### 2FA Verification Endpoint
```python
# app/api/v1/two_fa.py (NEW FILE)

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.core import redis_client as rc
from app.core.rate_limit import RateLimiter
from app.core.totp import TOTPService
from app.core.config import settings
from app.models.user import User
from app.models.two_fa_audit_log import TwoFAAuditLog

router = APIRouter(prefix="/auth/2fa", tags=["2FA"])

class TwoFAVerifyRequest(BaseModel):
    code: str  # 6-digit OTP or backup code
    challenge_token: str

@router.post("/verify")
async def verify_2fa(
    body: TwoFAVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify 2FA code during login."""
    
    ip = request.client.host if request.client else "unknown"
    
    # Validate challenge token exists
    challenge_data = await rc.get_2fa_challenge(body.challenge_token)
    if not challenge_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired 2FA challenge"
        )
    
    user_id = challenge_data["user_id"]
    
    # Rate limiting: 5 attempts per 10 minutes
    attempts = await rc.get_2fa_attempts(user_id)
    if attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many 2FA attempts. Try again later.",
            headers={"Retry-After": "600"}
        )
    
    # Fetch user
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    # Verify code
    is_valid = False
    method_used = "unknown"
    
    if body.code.isdigit() and len(body.code) == 6:
        # Try TOTP verification
        if user.two_fa_method == "totp":
            is_valid = TOTPService.verify_totp(user.totp_secret, body.code)
            method_used = "totp"
    else:
        # Try backup code
        if user.totp_backup_codes:
            for hashed_code in user.totp_backup_codes:
                if TOTPService.verify_backup_code(body.code, hashed_code):
                    is_valid = True
                    method_used = "backup_code"
                    # Remove used backup code
                    user.totp_backup_codes.remove(hashed_code)
                    await db.commit()
                    break
    
    # Log attempt
    audit_log = TwoFAAuditLog(
        user_id=user_id,
        action="verify_attempt",
        method=method_used,
        ip_address=ip,
        success=is_valid,
        attempts=attempts + 1
    )
    db.add(audit_log)
    
    if not is_valid:
        # Increment failed attempts
        await rc.increment_2fa_attempts(user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code"
        )
    
    # Success! Generate tokens
    await rc.reset_2fa_attempts(user_id)
    await rc.invalidate_2fa_challenge(body.challenge_token)
    
    token_data = {"sub": user_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Update last_login and last_2fa_verification
    await db.execute(
        update(User).where(User.id == user_id).values(
            last_login=datetime.now(timezone.utc),
            last_2fa_verification=datetime.now(timezone.utc)
        )
    )
    await db.commit()
    
    # Get permissions
    from app.dependencies.auth import get_user_permissions
    perms = await get_user_permissions(user_id, db)
    
    # Create response
    response = JSONResponse({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {...},
        "permissions": list(perms),
    })
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    # ... similar for refresh_token ...
    
    return response
```

## 4. FRONTEND IMPLEMENTATION

### Update Auth Store
```javascript
// src/store/authStore.js - Add to create()

export const useAuthStore = create((set, get) => ({
  // ... existing state ...
  
  // NEW: 2FA state
  twoFAPending: false,
  twoFAChallengeToken: null,
  twoFAMethod: null,
  
  // NEW: 2FA methods
  setup2FA: async (password) => {
    const { data } = await api.post('/auth/2fa/setup', { password });
    // Returns: setup_token, secret, qr_code_url
    return data;
  },
  
  confirm2FA: async (setupToken, code) => {
    const { data } = await api.post('/auth/2fa/setup/confirm', {
      setup_token: setupToken,
      code,
    });
    // Returns: backup_codes
    return data;
  },
  
  verify2FA: async (code, challengeToken) => {
    const { data } = await api.post('/auth/2fa/verify', {
      code,
      challenge_token: challengeToken,
    });
    // Returns: access_token, user, permissions
    localStorage.setItem('auth_user', JSON.stringify(data.user));
    localStorage.setItem('permissions', JSON.stringify(data.permissions));
    set({
      user: data.user,
      permissions: data.permissions,
      twoFAPending: false,
      twoFAChallengeToken: null,
    });
    return data;
  },
}));
```

### Update API Client to Handle 2FA
```javascript
// src/api/client.js - Modify response interceptor

async (error) => {
  // Handle cached response rejection
  if (error.__cachedResponse) {
    return error.__cachedResponse;
  }
  
  // NEW: Handle 202 (2FA Required) from login
  if (error.response?.status === 202) {
    // Don't retry, just return the 202 response
    // Frontend will handle showing OTP modal
    return Promise.reject(error);
  }
  
  // ... existing 401 handling ...
}
```

### Update Login Page
```javascript
// src/pages/Login.jsx - Handle 2FA response

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setLoading(true);
  try {
    await login(form.email, form.password);
    navigate('/dashboard');
  } catch (err) {
    // NEW: Check for 2FA required (202)
    if (err.response?.status === 202) {
      // Show OTP modal
      set2FAData({
        challengeToken: err.response.data.challenge_token,
        method: err.response.data.method,
      });
      setShowOTPModal(true);
    } else {
      setError(err.response?.data?.detail || 'Invalid credentials');
    }
  } finally {
    setLoading(false);
  }
};
```

### OTP Input Modal Component
```javascript
// src/components/OTPInputModal.jsx (NEW FILE)

import { useState } from 'react';
import { useAuthStore } from '../store/authStore';

export default function OTPInputModal({ 
  challengeToken, 
  method,
  onSuccess,
  onCancel,
}) {
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { verify2FA } = useAuthStore();

  const handleChange = (e) => {
    // Only allow digits, max 6
    const val = e.target.value.replace(/[^0-9]/g, '').slice(0, 6);
    setOtp(val);
    
    // Auto-submit when 6 digits entered
    if (val.length === 6) {
      handleSubmit(new Event('submit'));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await verify2FA(otp, challengeToken);
      onSuccess?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code');
      setOtp('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Enter Your Code</h2>
        <p>Enter the 6-digit code from your authenticator app</p>
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={otp}
            onChange={handleChange}
            placeholder="000000"
            maxLength="6"
            inputMode="numeric"
            autoFocus
            className="otp-input"
          />
          
          {error && <div className="error">{error}</div>}
          
          <button type="submit" disabled={loading || otp.length !== 6}>
            {loading ? "Verifying..." : "Verify"}
          </button>
        </form>
        
        <button onClick={onCancel} className="text-button">
          Use backup code instead
        </button>
      </div>
    </div>
  );
}
```

## 5. CONFIGURATION ADDITIONS

```python
# app/core/config.py - Add 2FA settings

class Settings(BaseSettings):
    # ... existing settings ...
    
    # 2FA Configuration
    TWO_FA_ENABLED: bool = True
    TOTP_ISSUER: str = "Students DS"
    TOTP_WINDOW: int = 1  # Time window tolerance (±N 30-sec steps)
    TWO_FA_RATE_LIMIT: int = 5  # Attempts per window
    TWO_FA_RATE_WINDOW: int = 600  # 10 minutes
    TWO_FA_CHALLENGE_TTL: int = 300  # 5 minutes
```

## 6. DATABASE MIGRATION

```sql
-- Alembic migration file

ALTER TABLE users ADD COLUMN two_fa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN two_fa_method VARCHAR(20);
ALTER TABLE users ADD COLUMN totp_secret VARCHAR(255);
ALTER TABLE users ADD COLUMN totp_backup_codes JSON;
ALTER TABLE users ADD COLUMN last_2fa_verification TIMESTAMP WITH TIME ZONE;

CREATE TABLE two_fa_audit_logs (
  id VARCHAR PRIMARY KEY,
  user_id VARCHAR NOT NULL REFERENCES users(id),
  action VARCHAR(50) NOT NULL,
  method VARCHAR(20),
  ip_address VARCHAR(45),
  success BOOLEAN NOT NULL,
  attempts INTEGER,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_two_fa_audit_user_created 
  ON two_fa_audit_logs(user_id, created_at DESC);
```

