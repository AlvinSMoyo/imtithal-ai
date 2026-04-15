"""
File upload and storage service
"""

from pathlib import Path
from fastapi import UploadFile, HTTPException
import shutil
from datetime import datetime

from app.config import settings


def validate_file_size(file: UploadFile) -> None:
    """
    Validate uploaded file size
    
    Args:
        file: UploadFile from FastAPI
    
    Raises:
        HTTPException: If file exceeds size limit
    """
    # ADDED: Check file size before processing
    file.file.seek(0, 2)  # Seek to end
    file_size_bytes = file.file.tell()
    file.file.seek(0)  # Reset to start
    
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' is too large ({file_size_mb:.1f}MB). "
                   f"Maximum allowed: {settings.max_file_size_mb}MB"
        )


async def save_upload(file: UploadFile, category: str) -> Path:
    """
    Save uploaded file to local storage
    
    Args:
        file: UploadFile from FastAPI
        category: "rosters" or "contracts"
    
    Returns:
        Path to saved file
    """
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = file.filename.replace(" ", "_")
    filename = f"{timestamp}_{safe_filename}"
    
    # Determine save path
    save_dir = settings.upload_dir / category
    save_dir.mkdir(parents=True, exist_ok=True)
    
    save_path = save_dir / filename
    
    # Save file (streams, doesn't load into memory)
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return save_path


def get_upload_info(file_path: Path) -> dict:
    """Get metadata about an uploaded file"""
    
    if not file_path.exists():
        return None
    
    return {
        "path": str(file_path),
        "filename": file_path.name,
        "size_bytes": file_path.stat().st_size,
        "size_kb": round(file_path.stat().st_size / 1024, 2),
        "exists": True
    }