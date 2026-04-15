"""
Configuration management for Imtithal.ai
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_url: str = "http://localhost:8000/api/v1"  # ADDED: Configurable API URL
    
    # Paths (absolute, not relative)
    base_dir: Path = Path(__file__).parent.parent.resolve()  # FIXED: Added .resolve()
    upload_dir: Path = base_dir / "data" / "uploads"
    reports_dir: Path = base_dir / "data" / "reports"
    rules_file: Path = base_dir / "data" / "rules" / "compliance_rules.json"
    database_path: Path = base_dir / "database" / "imtithal.db"
    
    # File upload limits (ADDED)
    max_file_size_mb: int = 10  # Maximum file size in MB
    max_roster_rows: int = 10000  # Maximum roster rows
    
    # Optional: LLM Configuration (disabled by default)
    anthropic_api_key: str | None = None
    enable_llm_enrichment: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
(settings.upload_dir / "rosters").mkdir(exist_ok=True)
(settings.upload_dir / "contracts").mkdir(exist_ok=True)
settings.database_path.parent.mkdir(parents=True, exist_ok=True)