"""Database backup and recovery service."""
import logging
import subprocess
import os
import gzip
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.database_backup import DatabaseBackup, BackupRestore, BackupSchedule
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseBackupService:
    """Service for managing database backups and restores."""
    
    def __init__(self):
        self.backup_dir = Path("/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(
        self,
        db: Session,
        user: User,
        description: str = None,
        backup_type: str = "full",
        compress: bool = True,
        is_automated: bool = False,
        upload_to_drive: bool = False,
    ) -> tuple[bool, str, DatabaseBackup]:
        """
        Create a new database backup using pg_dump.
        
        Args:
            db: Database session
            user: User initiating backup
            description: Optional description
            backup_type: "full" or "incremental"
            compress: Whether to compress the backup
            is_automated: Whether created by automated task
        
        Returns:
            tuple[bool, str, DatabaseBackup]: (success, message, backup_object)
        """
        try:
            # Generate backup filename
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            if compress:
                backup_file = self.backup_dir / f"{backup_name}.sql.gz"
            
            logger.info(f"Starting backup: {backup_name}")
            
            # Create backup record
            backup = DatabaseBackup(
                name=backup_name,
                description=description,
                status="in_progress",
                created_by_id=user.id if user else None,
                is_automated=is_automated,
                backup_type=backup_type,
                is_compressed=compress,
                compression_format="gzip" if compress else None,
                started_at=datetime.now(timezone.utc),
            )
            db.add(backup)
            db.commit()
            
            # Run pg_dump
            try:
                # Parse database URL to get connection parameters
                db_url = settings.DATABASE_URL
                
                # Extract connection details from DATABASE_URL
                # Format: postgresql://user:password@host:port/database
                from urllib.parse import urlparse
                
                parsed = urlparse(db_url)
                db_user = parsed.username
                db_password = parsed.password
                db_host = parsed.hostname or "localhost"
                db_port = parsed.port or 5432
                db_name = parsed.path.lstrip("/")
                
                # Prepare environment with database password
                env = os.environ.copy()
                if db_password:
                    env["PGPASSWORD"] = db_password
                
                # Run pg_dump command
                dump_command = [
                    "pg_dump",
                    "-h", db_host,
                    "-p", str(db_port),
                    "-U", db_user,
                    "-d", db_name,
                    "-v",  # Verbose
                ]
                
                # Write to file
                with open(backup_file, "w") as f:
                    result = subprocess.run(
                        dump_command,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        timeout=3600,  # 1 hour timeout
                    )
                
                if result.returncode != 0:
                    error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                    raise Exception(f"pg_dump failed: {error_msg}")
                
                # Compress if needed
                if compress and backup_file.suffix != ".gz":
                    compressed_file = str(backup_file) + ".gz"
                    with open(backup_file, "rb") as f_in:
                        with gzip.open(compressed_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()
                    backup_file = Path(compressed_file)
                
                # Get file size
                file_size = backup_file.stat().st_size
                
                # Update backup record
                backup.status = "completed"
                backup.file_path = str(backup_file)
                backup.file_size = file_size
                backup.completed_at = datetime.now(timezone.utc)
                backup.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                
                db.commit()
                
                logger.info(f"Backup completed: {backup_name} ({file_size} bytes)")
                
                # Upload to Google Drive if requested
                if upload_to_drive:
                    try:
                        from app.core.google_drive_service import GoogleDriveService
                        drive_service = GoogleDriveService()
                        
                        if drive_service.is_enabled:
                            logger.info(f"Uploading backup to Google Drive: {backup_name}")
                            success, message, drive_file_id = drive_service.upload_backup(
                                file_path=str(backup_file),
                                file_name=backup_file.name,
                                description=description or f"Automated backup from Students Data Store"
                            )
                            
                            if success:
                                backup.google_drive_file_id = drive_file_id
                                backup.uploaded_to_drive = True
                                backup.uploaded_to_drive_at = datetime.now(timezone.utc)
                                db.commit()
                                logger.info(f"Backup uploaded to Google Drive: {drive_file_id}")
                            else:
                                logger.warning(f"Failed to upload to Google Drive: {message}")
                    
                    except Exception as e:
                        logger.error(f"Error uploading to Google Drive: {e}")
                        # Don't fail the backup if Google Drive upload fails
                
                return True, f"Backup created successfully: {backup_name}", backup
                
            except subprocess.TimeoutExpired:
                backup.status = "failed"
                backup.error_message = "Backup timeout after 1 hour"
                db.commit()
                logger.error(f"Backup failed: Timeout")
                return False, "Backup timeout after 1 hour", backup
                
            except Exception as e:
                backup.status = "failed"
                backup.error_message = str(e)
                db.commit()
                logger.error(f"Backup failed: {e}")
                return False, f"Backup failed: {str(e)}", backup
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, f"Error: {str(e)}", None
    
    def restore_backup(
        self,
        db: Session,
        backup_id: str,
        user: User,
        restore_mode: str = "full_restore",
    ) -> tuple[bool, str]:
        """
        Restore database from a backup.
        
        Args:
            db: Database session
            backup_id: ID of backup to restore
            user: User initiating restore
            restore_mode: "full_restore" or "point_in_time"
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            # Get backup record
            result = db.execute(
                select(DatabaseBackup).where(DatabaseBackup.id == backup_id)
            )
            backup = result.scalar_one_or_none()
            
            if not backup or backup.status != "completed":
                return False, "Backup not found or not ready for restore"
            
            if not backup.file_path or not Path(backup.file_path).exists():
                return False, "Backup file not found"
            
            logger.info(f"Starting restore from backup: {backup.name}")
            
            # Create restore record
            restore = BackupRestore(
                backup_id=backup_id,
                status="in_progress",
                restore_mode=restore_mode,
                started_by_id=user.id,
                started_at=datetime.now(timezone.utc),
            )
            db.add(restore)
            db.commit()
            
            try:
                # Parse database URL
                from urllib.parse import urlparse
                
                db_url = settings.DATABASE_URL
                parsed = urlparse(db_url)
                
                db_user = parsed.username
                db_password = parsed.password
                db_host = parsed.hostname or "localhost"
                db_port = parsed.port or 5432
                db_name = parsed.path.lstrip("/")
                
                # Prepare environment
                env = os.environ.copy()
                if db_password:
                    env["PGPASSWORD"] = db_password
                
                # Read backup file
                backup_file = Path(backup.file_path)
                
                if backup_file.suffix == ".gz":
                    # Decompress
                    with gzip.open(backup_file, "rb") as f_in:
                        sql_content = f_in.read().decode()
                else:
                    # Read as-is
                    with open(backup_file, "r") as f:
                        sql_content = f.read()
                
                # Restore using psql
                restore_command = [
                    "psql",
                    "-h", db_host,
                    "-p", str(db_port),
                    "-U", db_user,
                    "-d", db_name,
                ]
                
                result = subprocess.run(
                    restore_command,
                    input=sql_content,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=7200,  # 2 hour timeout
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    raise Exception(f"psql restore failed: {error_msg}")
                
                # Update restore record
                restore.status = "completed"
                restore.completed_at = datetime.now(timezone.utc)
                db.commit()
                
                logger.info(f"Restore completed from backup: {backup.name}")
                return True, f"Database restored successfully from {backup.name}"
                
            except subprocess.TimeoutExpired:
                restore.status = "failed"
                restore.error_message = "Restore timeout after 2 hours"
                db.commit()
                logger.error("Restore failed: Timeout")
                return False, "Restore timeout after 2 hours"
                
            except Exception as e:
                restore.status = "failed"
                restore.error_message = str(e)
                db.commit()
                logger.error(f"Restore failed: {e}")
                return False, f"Restore failed: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, f"Error: {str(e)}"
    
    def delete_backup(self, db: Session, backup_id: str) -> tuple[bool, str]:
        """
        Delete a backup and its files.
        
        Args:
            db: Database session
            backup_id: ID of backup to delete
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            result = db.execute(
                select(DatabaseBackup).where(DatabaseBackup.id == backup_id)
            )
            backup = result.scalar_one_or_none()
            
            if not backup:
                return False, "Backup not found"
            
            # Delete file if exists
            if backup.file_path:
                try:
                    Path(backup.file_path).unlink()
                except FileNotFoundError:
                    pass
            
            # Delete database record
            db.delete(backup)
            db.commit()
            
            logger.info(f"Backup deleted: {backup.name}")
            return True, f"Backup deleted: {backup.name}"
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False, f"Error: {str(e)}"
    
    def get_backup_summary(self, db: Session) -> dict:
        """
        Get summary statistics about backups.
        
        Returns:
            dict: Backup statistics
        """
        try:
            result = db.execute(select(DatabaseBackup))
            backups = result.scalars().all()
            
            total_backups = len(backups)
            completed_backups = len([b for b in backups if b.status == "completed"])
            failed_backups = len([b for b in backups if b.status == "failed"])
            
            total_size = sum(b.file_size or 0 for b in backups if b.status == "completed")
            
            recent_backup = max(
                [b for b in backups if b.status == "completed"],
                key=lambda b: b.completed_at,
                default=None
            )
            
            return {
                "total_backups": total_backups,
                "completed_backups": completed_backups,
                "failed_backups": failed_backups,
                "total_size": total_size,
                "total_size_gb": total_size / (1024 ** 3),
                "recent_backup": {
                    "name": recent_backup.name,
                    "completed_at": recent_backup.completed_at.isoformat(),
                    "size": recent_backup.file_size,
                } if recent_backup else None,
            }
        
        except Exception as e:
            logger.error(f"Error getting backup summary: {e}")
            return {}
    
    def cleanup_expired_backups(self, db: Session) -> int:
        """
        Delete expired backups based on retention policy.
        
        Returns:
            int: Number of backups deleted
        """
        try:
            result = db.execute(
                select(DatabaseBackup).where(
                    DatabaseBackup.expires_at < datetime.now(timezone.utc)
                )
            )
            expired_backups = result.scalars().all()
            
            deleted_count = 0
            for backup in expired_backups:
                if backup.file_path and Path(backup.file_path).exists():
                    try:
                        Path(backup.file_path).unlink()
                    except:
                        pass
                
                db.delete(backup)
                deleted_count += 1
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} expired backups")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            return 0
