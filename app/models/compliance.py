"""
Compliance analysis result models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RiskFlag(BaseModel):
    """Individual compliance risk flag"""
    
    severity: str = Field(..., description="low | medium | high | critical")
    category: str = Field(..., description="saudization | contract | labor_law")
    title: str = Field(..., description="Short risk title")
    description: str = Field(..., description="Detailed explanation")
    affected_data: str = Field(..., description="What triggered this flag")
    recommendation: str = Field(..., description="How to remediate")


class SaudizationCompliance(BaseModel):
    """Saudization/Nitaqat compliance details"""
    
    status: str = Field(..., description="compliant | at_risk | non_compliant")
    current_percentage: float = Field(..., description="Current Saudi %")
    required_percentage: float = Field(..., description="Required Saudi % for sector")
    gap: float = Field(..., description="Difference (negative = shortfall)")
    color_band: str = Field(..., description="Nitaqat color: green | yellow | red")
    explanation: str = Field(..., description="Compliance status narrative")


class RosterSummary(BaseModel):
    """Employee roster analysis summary"""
    
    total_count: int
    saudi_count: int
    non_saudi_count: int
    saudi_percentage: float
    validation_issues: List[str] = Field(default_factory=list)


class DocumentFinding(BaseModel):
    """Contract document audit finding"""
    
    document_name: str
    finding_type: str = Field(..., description="missing_clause | suspicious_term | needs_review")
    description: str
    severity: str = Field(..., description="low | medium | high")


class ComplianceReport(BaseModel):
    """Complete compliance scan report"""
    
    report_id: str = Field(..., description="Unique report identifier")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)  # FIXED: Removed parentheses
    
    # Company info
    company_name: str
    sector: str
    
    # Roster summary
    roster_summary: RosterSummary
    
    # Compliance results
    saudization_compliance: SaudizationCompliance
    overall_risk_score: float = Field(..., ge=0, le=100, description="0=perfect, 100=critical")
    risk_level: str = Field(..., description="low | medium | high | critical")
    risk_flags: List[RiskFlag]
    
    # Contract findings
    contract_findings: List[DocumentFinding]
    
    # Recommendations
    priority_actions: List[str]
    
    # Audit trail
    scan_methodology: str = Field(
        default="Deterministic rule-based compliance engine v0.1 (MVP)"
    )
    disclaimer: str = Field(
        default="⚠️ This is a preliminary compliance scan using example rules for demonstration purposes. "
                "Manual legal review by qualified Saudi labor law counsel is required. "
                "These results are not authoritative legal guidance."
    )