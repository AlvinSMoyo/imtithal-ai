"""
Helper utility functions
"""

from datetime import datetime
from typing import Any
import json


def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def safe_json_dump(data: Any) -> str:
    """Safely serialize data to JSON string"""
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return f"{{\"error\": \"JSON serialization failed: {str(e)}\"}}"


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."