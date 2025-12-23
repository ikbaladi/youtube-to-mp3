import os
import time
from pathlib import Path
from app.config import settings
import logging
import unicodedata

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename and handle Unicode"""
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove multiple spaces and trim
    filename = ' '.join(filename.split())
    
    # Limit length
    return filename[:200].strip()


def cleanup_old_files():
    """Remove files older than FILE_RETENTION_HOURS"""
    try:
        download_dir = settings.DOWNLOAD_DIR
        current_time = time.time()
        retention_seconds = settings.FILE_RETENTION_HOURS * 3600
        
        for file_path in download_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > retention_seconds:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path.name}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"