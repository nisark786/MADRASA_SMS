# AUTHENTICATION SYSTEM - QUICK REFERENCE SUMMARY

## Architecture Overview

FRONTEND (React + Zustand)
  ├─ Login.jsx: email + password form
  ├─ useAuthStore: login(), logout(), hasPermission()
  └─ axios interceptors: CSRF token + auto-refresh on 401

        ↓ withCredentials: true ↓

BACKEND (FastAPI)
  ├─ POST /auth/login: credential validation + token generation
  ├─ POST /auth/refresh: new access token from refresh token
  ├─ POST /auth/logout: cache invalidation + cookie clearing
  └─ GET /auth/me: current user + permissions

STORAGE
  ├─ httpOnly Cookies: access_token, refresh_token, csrf_token
  ├─ localStorage: auth_user, permissions (JSON)
  └─ Redis: user:obj:{id}, perms:{id}, csrf:{token}, rate_limit:{key}

## Security Layers (7 Total)

1. AUTHENTICATION
   - bcrypt password hashing (auto-deprecated schemes)
   - Constant-time comparison (timing attack prevention)
   - Rate limiting: 5/min per email, 10/min per IP (Redis)

2. TOKEN MANAGEMENT
   - JWT with HS256 (HMAC-SHA256)
   - Token types: access (15min) and refresh (7 days)
   - Type verification prevents token confusion attacks

3. TRANSPORT SECURITY
   - httpOnly cookies (XSS protection)
   - Secure flag (HTTPS only)
   - SameSite=Strict (CSRF protection)
   - CORS whitelisting

4. CSRF PROTECTION
   - Double-submit cookie pattern
   - Cryptographically secure tokens (32 bytes)
   - Redis-backed validation (15min TTL)
   - Single-use tokens (deleted after validation)

5. SESSION MANAGEMENT
   - User object cache (15min TTL)
   - Permission cache (token lifetime)
   - Cache invalidation on logout

6. CONTENT SECURITY
   - CSP headers (restrictive policy)
   - X-Frame-Options: DENY
   - HSTS: 1 year (enforce HTTPS)

7. AUDIT & LOGGING
   - Login attempts with IP address
   - Last login tracking
   - Structured JSON logging
   - Background audit tasks

## Login Process (Simplified)

User Input (email + password)
    ↓
Rate Limit Check (Redis) - 5/min per email
    ↓
Credential Validation (bcrypt)
    ↓
JWT Token Generation (HS256)
    ↓
Permission Resolution (DB or Redis cache)
    ↓
User Object Caching (Redis, 15min)
    ↓
Background Tasks (audit log, last_login)
    ↓
Response with:
  - access_token (httpOnly cookie)
  - refresh_token (httpOnly cookie)
  - csrf_token (httpOnly cookie)
  - user data (JSON)
  - permissions (JSON)
  - rate limit headers
    ↓
Redirect to dashboard

## Key Files

Backend:
  - auth.py (279 lines) - login, refresh, logout, me endpoints
  - security.py (44 lines) - JWT encoding/decoding, password hashing
  - csrf.py (91 lines) - CSRF token generation/validation
  - rate_limit.py (121 lines) - Redis-based rate limiting
  - dependencies/auth.py (131 lines) - JWT extraction, user verification

Frontend:
  - client.js (98 lines) - axios instance + interceptors
  - authStore.js (47 lines) - Zustand state management
  - Login.jsx (114 lines) - login form + error handling

## Current Security Measures (Implemented)

✓ Constant-time password verification
✓ JWT tokens with type field
✓ Rate limiting (brute force protection)
✓ httpOnly cookies (XSS protection)
✓ SameSite=Strict (CSRF protection)
✓ CSRF tokens (double-submit pattern)
✓ Content Security Policy
✓ X-Frame-Options: DENY
✓ HSTS headers
✓ Audit logging with IP tracking
✓ Account status checking
✓ No user enumeration (generic errors)

## For 2FA Implementation

WHAT CHANGES:
1. Database
   - Add 2FA fields to User model
   - Create TwoFAAuditLog table

2. Backend Services
   - TOTP generation/verification (pyotp)
   - Backup code generation (cryptographically secure)
   - Challenge token management (Redis)
   - QR code generation (qrcode)

3. Backend Endpoints
   - POST /auth/2fa/setup - initiate setup
   - POST /auth/2fa/setup/confirm - verify OTP during setup
   - POST /auth/2fa/verify - verify OTP during login (main endpoint)
   - POST /auth/2fa/disable - disable 2FA
   - GET /auth/2fa/status - check 2FA status

4. Backend Logic
   - Modify login: if 2FA enabled, return 202 with challenge token
   - New rate limiting: 5 attempts per 10 minutes for 2FA

5. Frontend Components
   - OTPInputModal.jsx - 6-digit OTP input
   - Setup2FAWizard.jsx - step-by-step setup
   - Manage2FAPage.jsx - disable/regenerate codes

6. Frontend Logic
   - Handle 202 response from login
   - Update auth store with 2FA methods
   - Show OTP modal after login
   - Implement setup/disable flows

## 2FA Authentication Flow

User Login (existing)
    ↓
Check: 2FA enabled?
    ├─ NO → return tokens (existing flow)
    └─ YES ↓
        Generate 2FA challenge token (5min TTL)
        Return 202 "Accepted" with:
          - challenge_token
          - method ('totp' or 'sms')
            ↓
        Frontend shows OTP modal
            ↓
User submits OTP
    ↓
POST /auth/2fa/verify
    ├─ Validate challenge token
    ├─ Rate limit check (5/10min)
    ├─ Verify OTP (TOTP with ±1 window)
    ├─ OR verify backup code (hashed)
    ├─ If valid: generate tokens
    └─ If invalid: return 401, increment attempts

ADVANTAGES:
✓ Minimal changes to existing auth flow
✓ Backward compatible (non-2FA users unaffected)
✓ Redis infrastructure ready for challenge tokens
✓ Rate limiting already in place
✓ Audit logging infrastructure exists

LIBRARIES TO ADD:
Backend: pyotp, qrcode[pil]
Frontend: qrcode.react

ESTIMATED TIME: 8-12 days (design + implementation + testing)

