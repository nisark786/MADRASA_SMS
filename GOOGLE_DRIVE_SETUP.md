# Google Drive Integration for Database Backups

## Step 1: Create Google Cloud Project & Get Credentials

### 1.1 Create a Project
1. Go to https://console.cloud.google.com/
2. Click on "Select a Project" (top left)
3. Click "NEW PROJECT"
4. Enter name: "Students Data Store Backups"
5. Click "CREATE"
6. Wait for project to be created, then select it

### 1.2 Enable Google Drive API
1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on it
4. Click "ENABLE"

### 1.3 Create Service Account
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in:
   - Service account name: "students-backup-service"
   - Service account ID: (auto-filled)
   - Description: "Automated backup service for Students Data Store"
4. Click "CREATE AND CONTINUE"
5. Skip the optional steps, click "DONE"

### 1.4 Create & Download Key
1. In "Credentials" page, find your service account under "Service Accounts"
2. Click on the service account name
3. Go to "KEYS" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON" format
6. Click "CREATE"
7. A JSON file will download automatically
8. **Save this file as: `google-credentials.json` in backend root directory**

### 1.5 Get Your Google Drive Folder ID (Optional but Recommended)
1. Create a folder in your Google Drive called "Students Backups"
2. Open that folder
3. Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
4. Copy the FOLDER_ID
5. Add to your `.env` file as: `GOOGLE_DRIVE_FOLDER_ID=FOLDER_ID_HERE`

## Step 2: Installation

Add to `requirements.txt`:
```
google-auth-oauthlib==1.0.0
google-auth-httplib2==0.2.0
google-api-python-client==2.95.0
```

## Step 3: Environment Configuration

Add to `.env`:
```env
# Google Drive Configuration
GOOGLE_DRIVE_ENABLED=true
GOOGLE_CREDENTIALS_PATH=google-credentials.json
GOOGLE_DRIVE_FOLDER_ID=YOUR_FOLDER_ID_HERE
GOOGLE_DRIVE_BACKUP_FOLDER_NAME=Students Backups
```

## Step 4: Usage

### Manual Backup with Google Drive
```
Admin Dashboard
  ↓
Click "Create Backup"
  ↓
Select "Upload to Google Drive" checkbox
  ↓
Backup created and automatically uploaded
  ↓
File appears in Google Drive folder
  ↓
Can download from Drive anytime
```

### Benefits
✅ **Free storage** - Google gives 15 GB free
✅ **Automatic upload** - Backups sync to Drive automatically
✅ **Access anywhere** - Download from Google Drive web interface
✅ **Versioning** - Google Drive keeps file history
✅ **Redundancy** - Local disk + Google Drive = 2 copies
✅ **Sharing** - Can share backups with team members
✅ **No bandwidth costs** - Google's infrastructure
✅ **Auto-sync** - Sync to multiple cloud providers later

## Step 5: Architecture

```
Database Backup Flow with Google Drive:

1. Create Backup:
   Local Disk: /backups/backup_20260413_020000.sql.gz
        ↓
   Upload to Google Drive
        ↓
   Google Drive: "Students Backups/backup_20260413_020000.sql.gz"
        ↓
   Database records both locations
        ↓
   User sees upload status in UI

2. Restore from Backup:
   Option A: Restore from local disk (fast)
   Option B: Download from Google Drive first, then restore
   
3. Automated Cleanup:
   Old local backups deleted (after 30 days)
   BUT Google Drive versions kept (configurable retention)
```

## File Structure

```
Google Drive:
📁 Students Backups (created automatically)
├── backup_20260413_020000.sql.gz (220 MB)
├── backup_20260412_020000.sql.gz (215 MB)
├── backup_20260411_020000.sql.gz (210 MB)
├── README.txt (backup manifest)
└── manifest.json (backup metadata)

Local Disk:
/backups/
├── backup_20260413_020000.sql.gz (active)
├── backup_20260412_020000.sql.gz (active)
└── backup_20260411_020000.sql.gz (expires in 5 days)
```
