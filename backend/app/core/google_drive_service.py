"""Google Drive integration service for backup management."""
import logging
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timezone
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from app.core.config import settings

logger = logging.getLogger(__name__)

# Scopes required for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveService:
    """Service for managing backups on Google Drive."""
    
    def __init__(self):
        """Initialize Google Drive service."""
        self.service = None
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self.folder_name = settings.GOOGLE_DRIVE_BACKUP_FOLDER_NAME
        self.is_enabled = settings.GOOGLE_DRIVE_ENABLED
        
        if self.is_enabled:
            self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive API service."""
        try:
            creds_path = settings.GOOGLE_CREDENTIALS_PATH
            
            if not os.path.exists(creds_path):
                logger.warning(f"Google credentials file not found at {creds_path}")
                self.is_enabled = False
                return
            
            # Load credentials from service account JSON file
            credentials = Credentials.from_service_account_file(
                creds_path,
                scopes=SCOPES
            )
            
            # Build the Drive service
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Ensure backup folder exists
            self._ensure_backup_folder()
            
            logger.info("Google Drive service initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            self.is_enabled = False
    
    def _ensure_backup_folder(self):
        """Ensure the backup folder exists in Google Drive."""
        try:
            if self.folder_id:
                # Try to access existing folder
                try:
                    self.service.files().get(fileId=self.folder_id).execute()
                    logger.info(f"Using existing Google Drive folder: {self.folder_id}")
                    return
                except HttpError as e:
                    if e.resp.status == 404:
                        logger.warning(f"Folder {self.folder_id} not found, will create new one")
                        self.folder_id = None
                    else:
                        raise
            
            # Create folder if it doesn't exist
            file_metadata = {
                'name': self.folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            self.folder_id = folder.get('id')
            logger.info(f"Created new Google Drive folder: {self.folder_id}")
        
        except Exception as e:
            logger.error(f"Failed to ensure backup folder: {e}")
            raise
    
    def upload_backup(
        self,
        file_path: str,
        file_name: str,
        description: str = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a backup file to Google Drive.
        
        Args:
            file_path: Local path to backup file
            file_name: Name for file on Google Drive
            description: Optional file description
        
        Returns:
            tuple[bool, str, str]: (success, message, drive_file_id)
        """
        if not self.is_enabled or not self.service:
            return False, "Google Drive service not enabled", None
        
        try:
            # Check if file exists locally
            if not os.path.exists(file_path):
                return False, f"Backup file not found: {file_path}", None
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            logger.info(f"Uploading backup to Google Drive: {file_name} ({file_size} bytes)")
            
            # Prepare file metadata
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id],
                'description': description or f"Database backup created at {datetime.now(timezone.utc).isoformat()}",
            }
            
            # Upload file
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, size'
            ).execute()
            
            drive_file_id = file.get('id')
            web_link = file.get('webViewLink')
            uploaded_size = file.get('size', 0)
            
            logger.info(
                f"Successfully uploaded to Google Drive. "
                f"File ID: {drive_file_id}, Size: {uploaded_size}, Link: {web_link}"
            )
            
            return True, f"Uploaded to Google Drive: {web_link}", drive_file_id
        
        except HttpError as e:
            error_msg = f"Google Drive API error: {e.content.decode()}"
            logger.error(error_msg)
            return False, error_msg, None
        
        except Exception as e:
            error_msg = f"Failed to upload backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def download_backup(
        self,
        drive_file_id: str,
        local_path: str,
    ) -> Tuple[bool, str]:
        """
        Download a backup file from Google Drive.
        
        Args:
            drive_file_id: Google Drive file ID
            local_path: Local path to save file
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        if not self.is_enabled or not self.service:
            return False, "Google Drive service not enabled"
        
        try:
            logger.info(f"Downloading backup from Google Drive: {drive_file_id}")
            
            # Get file info
            file = self.service.files().get(
                fileId=drive_file_id,
                fields='name, size'
            ).execute()
            
            file_name = file.get('name', 'backup')
            file_size = file.get('size', 0)
            
            # Download file
            request = self.service.files().get_media(fileId=drive_file_id)
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                try:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.debug(f"Download progress: {progress}%")
                except HttpError as e:
                    logger.error(f"Error downloading file: {e}")
                    return False, f"Download error: {e}"
            
            # Save to local path
            fh.seek(0)
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Successfully downloaded backup: {local_path} ({file_size} bytes)")
            return True, f"Downloaded from Google Drive: {file_name}"
        
        except HttpError as e:
            error_msg = f"Google Drive API error: {e.content.decode()}"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Failed to download backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_backups(self) -> Tuple[bool, str, List[Dict]]:
        """
        List all backup files in Google Drive backup folder.
        
        Returns:
            tuple[bool, str, List[Dict]]: (success, message, files_list)
        """
        if not self.is_enabled or not self.service:
            return False, "Google Drive service not enabled", []
        
        try:
            logger.info("Listing backups from Google Drive")
            
            # Query for all files in backup folder
            query = f"'{self.folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, size, mimeType, createdTime, modifiedTime, webViewLink)',
                orderBy='modifiedTime desc',
                pageSize=100,
            ).execute()
            
            files = results.get('files', [])
            
            logger.info(f"Found {len(files)} backup files on Google Drive")
            
            return True, f"Found {len(files)} backups", files
        
        except HttpError as e:
            error_msg = f"Google Drive API error: {e.content.decode()}"
            logger.error(error_msg)
            return False, error_msg, []
        
        except Exception as e:
            error_msg = f"Failed to list backups: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
    
    def delete_backup(self, drive_file_id: str) -> Tuple[bool, str]:
        """
        Delete a backup file from Google Drive.
        
        Args:
            drive_file_id: Google Drive file ID
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        if not self.is_enabled or not self.service:
            return False, "Google Drive service not enabled"
        
        try:
            logger.info(f"Deleting backup from Google Drive: {drive_file_id}")
            
            # Get file name before deleting
            file = self.service.files().get(
                fileId=drive_file_id,
                fields='name'
            ).execute()
            file_name = file.get('name', 'unknown')
            
            # Delete file
            self.service.files().delete(fileId=drive_file_id).execute()
            
            logger.info(f"Successfully deleted backup from Google Drive: {file_name}")
            return True, f"Deleted from Google Drive: {file_name}"
        
        except HttpError as e:
            error_msg = f"Google Drive API error: {e.content.decode()}"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Failed to delete backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_storage_info(self) -> Dict:
        """
        Get Google Drive storage information.
        
        Returns:
            dict: Storage quota information
        """
        if not self.is_enabled or not self.service:
            return {
                "enabled": False,
                "message": "Google Drive service not enabled"
            }
        
        try:
            about = self.service.about().get(fields='storageQuota').execute()
            storage_quota = about.get('storageQuota', {})
            
            limit = storage_quota.get('limit', 0)
            usage = storage_quota.get('usage', 0)
            usage_in_drive = storage_quota.get('usageInDrive', 0)
            
            return {
                "enabled": True,
                "limit_bytes": limit,
                "limit_gb": limit / (1024 ** 3),
                "usage_bytes": usage,
                "usage_gb": usage / (1024 ** 3),
                "usage_in_drive_bytes": usage_in_drive,
                "usage_in_drive_gb": usage_in_drive / (1024 ** 3),
                "available_bytes": limit - usage,
                "available_gb": (limit - usage) / (1024 ** 3),
            }
        
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {
                "enabled": False,
                "error": str(e)
            }
