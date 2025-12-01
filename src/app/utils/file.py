"""
File utility functions for handling uploads and file operations.
"""
import logging
from typing import Optional
from pathlib import Path
from src.app.core.config import settings

logger = logging.getLogger(__name__)


def ensure_upload_dir() -> Path:
    """
    Ensure upload directory exists.
    
    Returns:
        Path to upload directory
    """
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def save_uploaded_file(
    file_data: bytes, 
    filename: str, 
    subdirectory: Optional[str] = None
) -> Path:
    """
    Save uploaded file to disk.
    
    Args:
        file_data: Binary file data
        filename: Original filename
        subdirectory: Optional subdirectory within uploads
        
    Returns:
        Path to saved file
    """
    upload_dir = ensure_upload_dir()
    
    if subdirectory:
        upload_dir = upload_dir / subdirectory
        upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / filename
    
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    logger.info(f"File saved: {file_path}")
    return file_path


def get_file_mime_type(filename: str) -> str:
    """
    Get MIME type from filename extension.
    
    Args:
        filename: Filename with extension
        
    Returns:
        MIME type string
    """
    extension = Path(filename).suffix.lower()
    
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.webp': 'image/webp'
    }
    
    return mime_types.get(extension, 'application/octet-stream')


def is_image_file(filename: str) -> bool:
    """
    Check if file is an image based on extension.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if file is an image
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    extension = Path(filename).suffix.lower()
    return extension in image_extensions


def is_pdf_file(filename: str) -> bool:
    """
    Check if file is a PDF based on extension.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if file is a PDF
    """
    return Path(filename).suffix.lower() == '.pdf'





