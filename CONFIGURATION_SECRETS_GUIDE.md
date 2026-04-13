# 🔐 Complete Guide: Where ALL Your Configurations & Secrets Are Stored

## Overview Map

```
Your System:
├── .env (LOCAL FILE - NEVER COMMITTED) ← YOU EDIT THIS
│   └── Contains: All secrets, passwords, API keys
│
├── backend/app/core/config.py (CODE FILE - COMMITTED)
│   └── Reads from .env and validates settings
│
├── google-credentials.json (LOCAL FILE - NEVER COMMITTED) ← YOU ADDED THIS
│   └── Google Drive service account credentials
│
└── Backend Running (Uses all of above)
```

---

## 📋 ALL Configurations & Their Locations

### **1. DATABASE CONFIGURATION**

**What it is:** PostgreSQL connection string

**Where stored:**
- **`.env` file:** `DATABASE_URL=postgresql+asyncpg://user:password@host/database`
- **Config code:** `backend/app/core/config.py` line 6

**Loaded by:**
```python
# app/core/config.py
class Settings(BaseSettings):
    DATABASE_URL: str  # REQUIRED - reads from .env
```

**Used in:**
- `backend/app/core/database.py` - Creates database connection pool
- `alembic.ini` - Migrations use this

**Why not committed:** Contains password, host, database name - SENSITIVE ⚠️

---

### **2. REDIS CONFIGURATION**

**What it is:** Redis connection for caching

**Where stored:**
- **`.env` file:** `REDIS_URL=redis://redis:6379`
- **Config code:** `backend/app/core/config.py` line 15

**Loaded by:**
```python
REDIS_URL: str = "redis://redis:6379"  # Default provided
```

**Used in:**
- `backend/app/core/redis_client.py` - Redis connection
- Rate limiting, session caching, token blacklisting

---

### **3. SECURITY & JWT TOKENS**

**What it is:** Secret key for signing JWT tokens

**Where stored:**
- **`.env` file:** `SECRET_KEY=your-secret-here`
- **Config code:** `backend/app/core/config.py` lines 18-24

**Loaded by:**
```python
SECRET_KEY: str  # REQUIRED - reads from .env
ALGORITHM: str = "HS256"  # Hardcoded
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Configurable
REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Configurable
```

**Used in:**
- `backend/app/core/security.py` - Creates and validates JWT tokens
- Login, authentication, authorization

**⚠️ CRITICAL:** 
- Must be strong random string
- Never use default
- Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

---

### **4. INITIAL ADMIN USER**

**What it is:** First admin account to bootstrap the system

**Where stored:**
- **`.env` file:** 
  - `ADMIN_EMAIL=admin@example.com`
  - `ADMIN_PASSWORD=change-me-in-production`
- **Config code:** `backend/app/core/config.py` (not shown but used in seed)

**Used in:**
- `backend/app/core/seed.py` - Creates admin user on first run
- Only used during database initialization

**⚠️ IMPORTANT:** Change before first production deployment

---

### **5. RATE LIMITING**

**What it is:** How many requests allowed per minute

**Where stored:**
- **`.env` file:**
  - `LOGIN_RATE_LIMIT=5` (per minute)
  - `API_RATE_LIMIT=60` (per minute)
- **Config code:** `backend/app/core/config.py` lines 29-30

**Loaded by:**
```python
LOGIN_RATE_LIMIT: int = 5
API_RATE_LIMIT: int = 60
```

**Used in:**
- `backend/app/middleware/rate_limiting.py` - Rate limit middleware
- Prevents brute force attacks, DDoS protection

---

### **6. FRONTEND CORS (Cross-Origin)**

**What it is:** Which domains can access your backend

**Where stored:**
- **`.env` file:** `FRONTEND_URL=http://localhost:5173`
- **Config code:** `backend/app/core/config.py` line 26

**Loaded by:**
```python
FRONTEND_URL: str = "http://localhost:5173"
```

**Used in:**
- `backend/main.py` - CORS middleware setup
- Only these domains can make requests to backend

**Multiple domains:**
```env
FRONTEND_URL=http://localhost:5173,https://app.example.com,https://admin.example.com
```

---

### **7. EMAIL/SMTP CONFIGURATION**

**What it is:** Gmail credentials for sending emails

**Where stored:**
- **`.env` file:**
  - `SMTP_SERVER=smtp.gmail.com`
  - `SMTP_PORT=465`
  - `SMTP_USERNAME=madrasasms@gmail.com`
  - `SMTP_PASSWORD=jpgw agao jdwp afdd` (your app password)
  - `SMTP_FROM_EMAIL=madrasasms@gmail.com`
  - `SMTP_FROM_NAME=Students Data Store`
- **Config code:** `backend/app/core/config.py` lines 33-38

**Loaded by:**
```python
SMTP_SERVER: str = "smtp.gmail.com"
SMTP_PORT: int = 465
SMTP_USERNAME: str = "madrasasms@gmail.com"
SMTP_PASSWORD: str  # REQUIRED - reads from .env
SMTP_FROM_EMAIL: str = "madrasasms@gmail.com"
SMTP_FROM_NAME: str = "Students Data Store"
```

**Used in:**
- `backend/app/core/email_service.py` - Sends emails
- Password reset, email verification, notifications

**⚠️ IMPORTANT:** 
- This is App Password, not Gmail password
- Keep secret!
- Can be revoked in Google Account settings

---

### **8. EMAIL FEATURES**

**What it is:** Enable/disable email verification

**Where stored:**
- **`.env` file:**
  - `EMAIL_ENABLED=true`
  - `EMAIL_VERIFICATION_REQUIRED=false`
- **Config code:** `backend/app/core/config.py` lines 41-42

**Loaded by:**
```python
EMAIL_ENABLED: bool = True
EMAIL_VERIFICATION_REQUIRED: bool = False
```

**Used in:**
- `backend/app/core/email_service.py` - Check if email enabled
- Authentication flows - check if verification required

---

### **9. GOOGLE DRIVE CONFIGURATION** ⭐ NEW!

**What it is:** Cloud backup storage settings

**Where stored:**
- **`.env` file:**
  - `GOOGLE_DRIVE_ENABLED=true` ✅ YOU CHANGED THIS!
  - `GOOGLE_CREDENTIALS_PATH=google-credentials.json`
  - `GOOGLE_DRIVE_FOLDER_ID=` (optional)
  - `GOOGLE_DRIVE_BACKUP_FOLDER_NAME=Students Data Store Backups`
- **Config code:** `backend/app/core/config.py` lines 48-51
- **Credentials file:** `backend/google-credentials.json` ✅ YOU ADDED THIS!

**Loaded by:**
```python
GOOGLE_DRIVE_ENABLED: bool = False
GOOGLE_CREDENTIALS_PATH: str = "google-credentials.json"
GOOGLE_DRIVE_FOLDER_ID: str = ""
GOOGLE_DRIVE_BACKUP_FOLDER_NAME: str = "Students Data Store Backups"
```

**Used in:**
- `backend/app/core/google_drive_service.py` - Google Drive operations
- `backend/app/core/backup_service.py` - Calls Google Drive service

**⚠️ IMPORTANT:**
- `google-credentials.json` is in `.gitignore` (not committed)
- Contains service account private key - VERY SENSITIVE
- Keep file secure

---

## 🔍 Configuration Flow Diagram

```
┌─────────────────────────────────────────┐
│          Your Local Machine             │
├─────────────────────────────────────────┤
│                                         │
│  .env (LOCAL - NOT COMMITTED)          │
│  ├─ DATABASE_URL                       │
│  ├─ SECRET_KEY                         │
│  ├─ SMTP_PASSWORD                      │
│  ├─ ADMIN_PASSWORD                     │
│  ├─ GOOGLE_DRIVE_ENABLED ← YOU SET     │
│  └─ ... (all configs)                  │
│                                         │
│  google-credentials.json                │
│  └─ Service account private key        │
│                                         │
│           ⬇️  (at runtime)              │
│                                         │
│  backend/app/core/config.py            │
│  ├─ Reads all .env values              │
│  ├─ Validates them                     │
│  ├─ Creates Settings object            │
│  └─ Passed to all services             │
│                                         │
│           ⬇️  (at runtime)              │
│                                         │
│  Backend Services                      │
│  ├─ email_service.py (uses SMTP_*)    │
│  ├─ backup_service.py (uses DB_*)     │
│  ├─ google_drive_service.py (uses GD_*)
│  ├─ security.py (uses SECRET_KEY)     │
│  ├─ redis_client.py (uses REDIS_URL)  │
│  ├─ database.py (uses DATABASE_URL)   │
│  └─ ... (all services)                 │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📁 File Organization

### **Files in Git (Committed - SAFE):**

```
✅ backend/app/core/config.py
   - Defines what configurations exist
   - NO actual secrets/values here
   - Just structure and defaults

✅ backend/app/core/backup_service.py
   - Uses settings.GOOGLE_DRIVE_ENABLED
   - Uses settings.DATABASE_URL
   - Code only, no values

✅ backend/app/core/google_drive_service.py
   - Uses settings.GOOGLE_CREDENTIALS_PATH
   - Uses settings.GOOGLE_DRIVE_ENABLED
   - Code only, no values

✅ backend/.env.example
   - TEMPLATE file showing what variables exist
   - No actual values, just placeholders
   - Safe to commit
```

### **Files NOT in Git (Local Only - SECRET):**

```
❌ backend/.env
   - Your actual configuration values
   - Passwords, API keys, secrets
   - In .gitignore - NEVER committed
   - Only on your machine

❌ backend/google-credentials.json
   - Google service account private key
   - HIGHLY SENSITIVE - treat like password
   - In .gitignore - NEVER committed
   - Only on your machine
```

---

## ✅ What's Currently in Your .env

Your `.env` file contains (I can see it):

```
DATABASE_URL               = postgresql+asyncpg://user:password@host/database
REDIS_URL                  = redis://redis:6379
SECRET_KEY                 = paste-your-secure-random-string-here
ADMIN_EMAIL                = admin@example.com
ADMIN_PASSWORD             = change-me-in-production
LOGIN_RATE_LIMIT           = 5
API_RATE_LIMIT             = 60
FRONTEND_URL               = http://localhost:5173
SMTP_SERVER                = smtp.gmail.com
SMTP_PORT                  = 465
SMTP_USERNAME              = your-email@gmail.com
SMTP_PASSWORD              = your-app-specific-password
SMTP_FROM_EMAIL            = your-email@gmail.com
SMTP_FROM_NAME             = Students Data Store
EMAIL_ENABLED              = true
EMAIL_VERIFICATION_REQUIRED = false
GOOGLE_DRIVE_ENABLED       = true ← YOU SET THIS! ✅
GOOGLE_CREDENTIALS_PATH    = google-credentials.json
GOOGLE_DRIVE_FOLDER_ID     = (empty - will auto-create)
GOOGLE_DRIVE_BACKUP_FOLDER_NAME = Students Data Store Backups
```

---

## ⚠️ What NEEDS to be Updated in Your .env

Based on what I see, update these with REAL values:

### **1. Database (CRITICAL)**
```env
# CURRENT (placeholder):
DATABASE_URL=postgresql+asyncpg://user:password@host/database

# UPDATE TO (example for local):
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/students_db

# OR (for Docker):
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/students_db

# OR (for production Supabase):
DATABASE_URL=postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres
```

### **2. Secret Key (CRITICAL)**
```env
# CURRENT (placeholder):
SECRET_KEY=paste-your-secure-random-string-here

# UPDATE TO (generate new):
# Run this command:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy output and paste:
SECRET_KEY=your-generated-secure-random-string-here
```

### **3. Admin User (IMPORTANT)**
```env
# CURRENT (placeholder):
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-in-production

# UPDATE TO (your credentials):
ADMIN_EMAIL=your-email@gmail.com
ADMIN_PASSWORD=your-secure-password

# Generate secure password:
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### **4. Email/SMTP (if using email)**
```env
# CURRENT (placeholder):
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# UPDATE TO (your Gmail App Password):
SMTP_USERNAME=madrasasms@gmail.com
SMTP_PASSWORD=jpgw agao jdwp afdd

SMTP_FROM_EMAIL=madrasasms@gmail.com
SMTP_FROM_NAME=Students Data Store
```

### **5. Frontend URL (if deploying)**
```env
# CURRENT (local development):
FRONTEND_URL=http://localhost:5173

# UPDATE TO (for production):
FRONTEND_URL=https://app.example.com,https://admin.example.com
```

### **6. Google Drive (already updated by you!)**
```env
# CURRENT (you set this):
GOOGLE_DRIVE_ENABLED=true ✅
GOOGLE_CREDENTIALS_PATH=google-credentials.json ✅
GOOGLE_DRIVE_FOLDER_ID= ✅ (will auto-create)
```

---

## 🔒 Security Best Practices

### **DO:**
✅ Store `.env` in `.gitignore` (already done)
✅ Store `google-credentials.json` in `.gitignore` (already done)
✅ Use strong random secrets (not default values)
✅ Rotate secrets periodically
✅ Keep secrets backed up securely
✅ Use environment variables in production

### **DON'T:**
❌ Commit `.env` to git
❌ Commit `google-credentials.json` to git
❌ Share `.env` via email/Slack
❌ Use simple passwords
❌ Commit actual credentials anywhere
❌ Put credentials in code

---

## 🚀 Configuration Loading at Startup

When your backend starts:

```
1. Read .env file
   └─ Load all key=value pairs from disk

2. Load google-credentials.json
   └─ Parse JSON service account credentials

3. Create Settings object (config.py)
   ├─ Validate all required values exist
   ├─ Apply defaults if not provided
   ├─ Throw error if critical value missing
   └─ Return validated settings

4. Pass settings to services
   ├─ DatabaseBackupService gets DATABASE_URL
   ├─ EmailService gets SMTP_* values
   ├─ GoogleDriveService gets GOOGLE_DRIVE_* values
   ├─ SecurityService gets SECRET_KEY
   └─ All other services get what they need

5. Services use settings
   └─ Create connections, authenticate, etc.

6. Backend ready to serve requests
   └─ All configurations loaded and validated
```

---

## 📍 Your Current Setup

```
Status Overview:

✅ backend/.env                          (EXISTS - you edited)
✅ backend/google-credentials.json       (EXISTS - you added)
✅ backend/.env.example                  (EXISTS - template)
✅ backend/app/core/config.py            (READS from .env)

Configuration Status:
├─ Database:        ⏳ NEEDS REAL VALUE
├─ Secret Key:      ⏳ NEEDS REAL VALUE
├─ Admin User:      ⏳ NEEDS REAL VALUE
├─ Email:           ⏳ NEEDS REAL VALUE (or disable)
├─ Frontend URL:    ✅ OK for local dev
├─ Google Drive:    ✅ ENABLED (you set to true!)
└─ Redis:           ✅ OK for Docker

Next: Update critical values marked ⏳
```

---

## 🎯 Summary

**Where your configs/secrets are:**

| Item | Location | Status | Type |
|------|----------|--------|------|
| Database URL | `.env` | ⏳ Update needed | SECRET |
| Secret Key | `.env` | ⏳ Generate new | SECRET |
| Admin Creds | `.env` | ⏳ Update needed | SECRET |
| Email Password | `.env` | ✅ Already set | SECRET |
| Google Drive Enabled | `.env` | ✅ true | CONFIG |
| Google Credentials | `google-credentials.json` | ✅ Added | SECRET |
| All config structure | `config.py` | ✅ In git | CODE |
| Config template | `.env.example` | ✅ In git | TEMPLATE |

**Safe to commit:** Code, templates, examples
**Never commit:** Actual values, secrets, credentials

---

## Next Steps:

1. ✅ Update `.env` with real database URL
2. ✅ Generate and set real SECRET_KEY
3. ✅ Update admin credentials
4. ✅ Configure email if needed (or disable)
5. ✅ Restart backend
6. ✅ Test everything works

Want me to help with any of these?
