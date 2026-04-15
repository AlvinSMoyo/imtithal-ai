"""
File upload metadata models
"""

from pydantic import BaseModel
from datetime import datetime
from pathlib import Path


class UploadMetadata(BaseModel):
    """Uploaded file metadata"""
    
    original_filename: str
    saved_path: Path
    file_size: int
    upload_timestamp: datetime = datetime.utcnow()
    file_type: str  # "roster" or "contract"