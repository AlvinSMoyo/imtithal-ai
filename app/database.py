"""
Database initialization and models
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.config import settings

# Database setup
DATABASE_URL = f"sqlite:///{settings.database_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class Company(Base):
    """Company profile table"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sector = Column(String)
    total_employees = Column(Integer)
    saudi_employees = Column(Integer)
    non_saudi_employees = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceScan(Base):
    """Compliance scan history"""
    __tablename__ = "compliance_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer)
    company_name = Column(String)
    scan_timestamp = Column(DateTime, default=datetime.utcnow)
    roster_file = Column(String)
    contract_files = Column(Text)  # JSON string
    
    # Results
    overall_risk_score = Column(Float)
    saudization_status = Column(String)
    risk_flags_count = Column(Integer)
    
    # Report path
    report_file = Column(String)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()