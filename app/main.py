"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import compliance

# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="Imtithal.ai API",
    description="Compliance Copilot for Saudi SMEs - Backend API",
    version="0.1.0"
)

# CORS middleware (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(compliance.router, prefix="/api/v1", tags=["compliance"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Imtithal.ai Compliance API",
        "version": "0.1.0",
        "message": "Governance-first AI for Saudi SME compliance"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "ok",
        "database": str(settings.database_path),
        "upload_dir": str(settings.upload_dir),
        "reports_dir": str(settings.reports_dir),
        "llm_enabled": settings.enable_llm_enrichment
    }