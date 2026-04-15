"""
Company profile models
"""

from pydantic import BaseModel, Field
from typing import Optional


class CompanyProfile(BaseModel):
    """Company profile data"""
    
    company_name: str = Field(..., description="Company legal name")
    sector: str = Field(..., description="Industry sector")
    total_employees: int = Field(..., ge=1, description="Total workforce count")
    saudi_employees: int = Field(..., ge=0, description="Number of Saudi nationals")
    non_saudi_employees: int = Field(..., ge=0, description="Number of non-Saudi employees")
    notes: Optional[str] = Field(None, description="Additional company notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Tech Innovations KSA",
                "sector": "Technology",
                "total_employees": 50,
                "saudi_employees": 30,
                "non_saudi_employees": 20,
                "notes": "Growing IT consulting firm"
            }
        }