# Students Data Store - Authentication System Analysis & 2FA Implementation Guide

## Executive Summary

The Students Data Store project implements a **modern, security-first authentication system** with:
- JWT token-based authentication (access + refresh tokens)
- httpOnly secure cookies for XSS protection
- CSRF protection with double-submit cookie pattern
- Rate limiting on login attempts
- Redis-based caching for zero-DB authentication on warm paths

## 1. CURRENT AUTHENTICATION FLOW

### 1.1 Login Process (POST /api/v1/auth/login)

REQUEST: email, password

SECURITY CHECKS:
1. Rate Limiting (5 per email, 10 per IP per 60s) - Redis token bucket
2. Credential Validation - bcrypt constant-time comparison
3. Account Status Check - is_active flag
4. Token Generation - HS256 JWT (15min access, 7day refresh)
5. Permission Resolution - DB or Redis cache
6. User Caching - Redis (15min TTL)
7. Audit Logging - background task (last_login + IP tracking)

RESPONSE:
- access_token (httpOnly cookie)
- refresh_token (httpOnly cookie)
- csrf_token (httpOnly cookie)
- user data (JSON)
- permissions list
- rate limit headers

### 1.2 Frontend Flow

1. User enters email/password in Login.jsx
2. useAuthStore.login() → POST /auth/login
3. Response: tokens in httpOnly cookies, user data in localStorage
4. Redirect to /dashboard
5. Subsequent requests: axios sends cookies automatically (withCredentials: true)
6. CSRF token attached to state-changing requests (POST, PUT, DELETE, PATCH)

### 1.3 Token Refresh (POST /api/v1/auth/refresh)

1. Frontend detects 401 response
2. axios interceptor calls /auth/refresh
3. Uses refresh_token from httpOnly cookie
4. Returns new access_token in httpOnly cookie
5. Retries original request

### 1.4 Logout (POST /api/v1/auth/logout)

1. Requires authentication (verified by JWT)
2. Invalidates Redis caches (user object, permissions)
3. Clears httpOnly cookies
4. Frontend: localStorage cleared, redirects to /login

## 2. AUTH.PY FILE CONTENTS

### Endpoints:
- POST /auth/login (70 lines of logic)
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me (concurrent fetch of permissions + roles)

### Key Functions:
- login(body, request, background_tasks, db) - main login handler
- _post_login_tasks(user_id, ip_address) - background logging
- refresh(request) - token refresh
- logout(current_user) - session termination
- me(current_user, db) - user profile fetch

### Models:
- LoginRequest: email (EmailStr), password (str)
- TokenResponse: access_token, token_type, user, permissions, csrf_token
- RefreshRequest: refresh_token

## 3. FRONTEND AUTHENTICATION

### API Client (client.js):
- axios with withCredentials: true (auto-sends cookies)
- Request interceptor: attaches CSRF token to state-changing requests
- Response interceptor: caches GET responses (30s), auto-refreshes on 401, stores CSRF token
- GET request caching: deduplication within 30s window

### Auth Store (authStore.js):
- Zustand state management
- localStorage for: auth_user, permissions
- httpOnly cookies for: access_token, refresh_token, csrf_token (auto-managed)
- Methods: login(), logout(), hasPermission(), hasAnyPermission()

### Login Page (Login.jsx):
- Simple form with email + password
- Error display
- Loading state
- Redirect to dashboard on success

## 4. SECURITY MEASURES IN PLACE

### Authentication:
✅ Constant-time password verification (bcrypt)
✅ JWT with type field (access vs refresh)
✅ Rate limiting (brute force)
✅ Account status checking
✅ No user enumeration (generic errors)

### Transport:
✅ httpOnly cookies (XSS protection)
✅ Secure flag (HTTPS in production)
✅ SameSite=Strict (CSRF protection)
✅ CORS whitelisting
✅ HSTS headers (1 year)

### Session:
✅ CSRF tokens (double-submit cookie)
✅ Single-use CSRF tokens
✅ Redis CSRF storage (15min TTL)
✅ Cache invalidation on logout

### Content:
✅ Content Security Policy (CSP)
✅ X-Frame-Options: DENY
✅ X-Content-Type-Options: nosniff
✅ X-XSS-Protection

### Audit:
✅ Login audit logs with IP address
✅ Structured JSON logging
✅ Background task processing

## 5. WHAT NEEDS TO CHANGE FOR 2FA

### Backend Changes:

1. User Model - Add fields:
   - two_fa_enabled: bool
   - two_fa_method: str ('totp' or 'sms')
   - totp_secret: str (encrypted)
   - totp_backup_codes: list (hashed)
   - last_2fa_verification: datetime

2. New Models:
   - TwoFAAuditLog (track 2FA attempts)

3. New Services (app/core/):
   - totp.py: generate_secret(), verify_otp(), generate_backup_codes()
   - qr_code.py: generate_qr_url()
   - 2fa_challenge_tokens in Redis

4. New Endpoints:
   - POST /auth/2fa/setup - initiate setup (requires password)
   - POST /auth/2fa/setup/confirm - verify OTP during setup
   - POST /auth/2fa/verify - verify OTP during login
   - POST /auth/2fa/disable - disable 2FA (requires password + OTP)
   - GET /auth/2fa/status - check if enabled

5. Modify Existing:
   - POST /auth/login - if 2FA enabled, return 202 with challenge token
   - /auth/me - include two_fa_enabled flag

6. Add Dependencies:
   - pyotp (TOTP generation/verification)
   - qrcode[pil] (QR code generation)

7. Database Migration:
   - Add new columns to users table
   - Create two_fa_audit_logs table

### Frontend Changes:

1. Update Auth Store:
   - Add twoFAPending, twoFAChallengeToken, twoFAMethod state
   - Add verify2FA() method
   - Add setup2FA(), confirm2FA(), disable2FA() methods

2. New Components:
   - OTPInputModal.jsx - 6-digit OTP input
   - BackupCodeModal.jsx - backup code input
   - Setup2FAWizard.jsx - step-by-step setup

3. New Pages:
   - Setup2FAPage.jsx - initial setup with QR code
   - Manage2FAPage.jsx - disable/regenerate codes

4. Update Login Flow:
   - Handle 202 response from /auth/login
   - Show OTP modal instead of redirecting
   - After OTP verification, show redirect

5. Add Dependencies:
   - qrcode.react (QR code display)

## 6. NEW AUTHENTICATION FLOW WITH 2FA

User submits email + password
  ↓
[existing: rate_limit + credential check]
  ↓
[Check: user.two_fa_enabled?]
  ├─ NO → [return tokens, redirect to dashboard]
  └─ YES → [2FA flow]
           ↓
       [Generate 2FA challenge token (5min TTL)]
       [Generate OTP if TOTP method]
       [Return 202 "Accepted" with:]
       - challenge_token
       - method ('totp' or 'sms')
       ↓
       [Frontend shows OTP modal]
       ↓
User submits OTP code
  ↓
[POST /auth/2fa/verify with code + challenge_token]
  ↓
[Rate limit check (5 per 10min)]
[Validate challenge token exists]
[Verify OTP with TOTP library (time window ±1)]
[OR verify backup code (hashed comparison)]
  ↓
[If valid: generate access + refresh tokens]
[If invalid: return 401, increment attempt counter]
  ↓
[Return standard token response]

## 7. NEW ENDPOINTS NEEDED

POST /auth/2fa/setup
- Input: password
- Output: setup_token, secret, qr_code_url
- Rate limit: 1 per minute

POST /auth/2fa/setup/confirm
- Input: setup_token, code (OTP)
- Output: backup_codes (array)
- Rate limit: 5 per 10 minutes

POST /auth/2fa/verify
- Input: code, challenge_token
- Output: access_token, refresh_token, user, permissions, csrf_token
- Rate limit: 5 per 10 minutes

POST /auth/2fa/disable
- Input: password, code (current OTP)
- Output: {success: true}
- Requires: auth + password + valid OTP

POST /auth/2fa/backup-codes/regenerate
- Input: password, code (current OTP)
- Output: backup_codes (array)
- Requires: auth + 2FA enabled + password + valid OTP

GET /auth/2fa/status
- Output: {enabled: bool, method: str, last_verification: datetime}
- Requires: auth

## 8. IMPLEMENTATION ROADMAP

Phase 1: Backend Infrastructure (1-2 days)
- Create TOTP service (pyotp)
- Create QR code generator
- Add Redis state management for 2FA challenges
- Add rate limiting for 2FA attempts

Phase 2: Backend Endpoints (2-3 days)
- Modify login to handle 2FA
- Create 2FA setup endpoints
- Create 2FA verification endpoint
- Create 2FA management endpoints

Phase 3: Frontend Implementation (2-3 days)
- Update auth store with 2FA methods
- Create OTP modal component
- Create Setup2FA wizard
- Update login page to handle 202 response

Phase 4: Security Testing (2-3 days)
- Unit tests for TOTP
- Integration tests for full flow
- Rate limiting tests
- Backup code tests

Phase 5: Deployment (1 day)
- Database migration
- Environment variables
- Documentation

Total: 8-12 days

## 9. SECURITY CONSIDERATIONS FOR 2FA

✅ TOTP secret encrypted at rest
✅ Backup codes hashed with bcrypt
✅ Challenge tokens: 5min TTL, Redis-backed
✅ 2FA rate limiting: 5 per 10 minutes
✅ Time skew tolerance: ±1 window (30s each direction)
✅ All 2FA operations audited with IP address
✅ Disable 2FA requires password + current OTP (double verification)
✅ Setup requires password confirmation
✅ QR codes generated server-side
✅ Backup codes shown only once
✅ Full audit trail in two_fa_audit_logs table

## 10. COMPARISON: Before vs After 2FA

| Aspect | Before | After |
|--------|--------|-------|
| Auth steps | 1 (password) | 2 (password + OTP) |
| Phishing vulnerability | High | Very Low |
| Compromised device | Full compromise | Limited (no OTP) |
| Recovery options | Password reset | Password reset + backup codes |
| User friction | Low | Medium |
| Audit trail | Basic | Detailed |

## Conclusion

The auth system is well-designed for 2FA addition. Current features like Redis,
async patterns, and httpOnly cookies provide excellent infrastructure. 2FA is
additive and can be optional initially for gradual rollout.

