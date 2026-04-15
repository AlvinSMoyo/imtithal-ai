"""
Compliance report builder

Combines all analysis results into structured report
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from app.config import settings
from app.models.company import CompanyProfile
from app.models.compliance import (
    ComplianceReport, RosterSummary, SaudizationCompliance,
    RiskFlag, DocumentFinding
)


def build_report(
    company: CompanyProfile,
    roster_summary: RosterSummary,
    compliance_result: dict,
    contract_findings: List[DocumentFinding]
) -> ComplianceReport:
    """
    Build complete compliance report from analysis results
    
    Args:
        company: Company profile
        roster_summary: Roster analysis
        compliance_result: Nitaqat compliance calculation
        contract_findings: Contract audit findings
    
    Returns:
        ComplianceReport object
    """
    
    saudization = compliance_result["saudization_compliance"]
    risk_flags = compliance_result["risk_flags"]
    
    # Calculate overall risk score (0-100)
    risk_score = calculate_overall_risk_score(
        saudization,
        risk_flags,
        contract_findings
    )
    
    # Determine risk level
    if risk_score < 25:
        risk_level = "low"
    elif risk_score < 50:
        risk_level = "medium"
    elif risk_score < 75:
        risk_level = "high"
    else:
        risk_level = "critical"
    
    # Generate priority actions
    priority_actions = generate_priority_actions(
        saudization,
        risk_flags,
        contract_findings
    )
    
    # Create report ID
    report_id = f"IMTH-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    # Build report
    report = ComplianceReport(
        report_id=report_id,
        scan_timestamp=datetime.utcnow(),
        company_name=company.company_name,
        sector=company.sector,
        roster_summary=roster_summary,
        saudization_compliance=saudization,
        overall_risk_score=round(risk_score, 2),
        risk_level=risk_level,
        risk_flags=risk_flags,
        contract_findings=contract_findings,
        priority_actions=priority_actions
    )
    
    # Save report to disk (don't return path - unused)
    save_report(report)
    
    return report


def calculate_overall_risk_score(
    saudization: SaudizationCompliance,
    risk_flags: List[RiskFlag],
    contract_findings: List[DocumentFinding]
) -> float:
    """
    Calculate weighted overall risk score (0-100)
    
    Scoring logic:
    - Saudization compliance: 60% weight
    - Risk flags severity: 30% weight
    - Contract findings: 10% weight
    """
    
    # Saudization score (60% weight)
    if saudization.status == "compliant":
        saud_score = 0
    elif saudization.status == "at_risk":
        saud_score = 40
    else:  # non_compliant
        saud_score = 80
    
    # Risk flags score (30% weight)
    severity_weights = {"low": 10, "medium": 25, "high": 50, "critical": 100}
    
    if risk_flags:
        flag_scores = [severity_weights.get(flag.severity, 25) for flag in risk_flags]
        avg_flag_score = sum(flag_scores) / len(flag_scores)
    else:
        avg_flag_score = 0
    
    # Contract findings score (10% weight)
    if contract_findings:
        finding_weights = {"low": 10, "medium": 30, "high": 60}
        finding_scores = [finding_weights.get(f.severity, 30) for f in contract_findings]
        avg_finding_score = sum(finding_scores) / len(finding_scores)
    else:
        avg_finding_score = 0
    
    # Weighted total
    overall_score = (
        saud_score * 0.6 +
        avg_flag_score * 0.3 +
        avg_finding_score * 0.1
    )
    
    return overall_score


def generate_priority_actions(
    saudization: SaudizationCompliance,
    risk_flags: List[RiskFlag],
    contract_findings: List[DocumentFinding]
) -> List[str]:
    """Generate prioritized action items"""
    
    actions = []
    
    # Saudization actions
    if saudization.status == "non_compliant":
        actions.append(
            f"🚨 URGENT: Consult with Saudi labor law counsel regarding Saudization compliance. "
            f"Preliminary scan suggests rate may need to increase from {saudization.current_percentage}% "
            f"to approximately {saudization.required_percentage}%."
        )
    elif saudization.status == "at_risk":
        actions.append(
            f"⚠️ Consider increasing Saudization rate from {saudization.current_percentage}% "
            f"to approximately {saudization.required_percentage}% to potentially reach green band. "
            f"Verify official status via Qiwa portal."
        )
    
    # Critical risk flags
    critical_flags = [f for f in risk_flags if f.severity == "critical"]
    for flag in critical_flags:
        actions.append(f"🚨 {flag.title}: {flag.recommendation}")
    
    # High-severity contract issues
    high_findings = [f for f in contract_findings if f.severity == "high"]
    if high_findings:
        actions.append(
            f"📄 Review {len(high_findings)} high-severity contract finding(s) with qualified Saudi labor law counsel"
        )
    
    # Data quality issues
    medium_flags = [f for f in risk_flags if f.severity == "medium" and f.category == "labor_law"]
    if medium_flags:
        actions.append("📊 Correct employee roster data quality issues to ensure accurate analysis")
    
    # If no actions, add general recommendation
    if not actions:
        actions.append(
            "✅ Preliminary scan shows no critical issues detected. "
            "Continue monitoring compliance quarterly. Verify with official Qiwa/Mudad systems."
        )
    
    return actions


def save_report(report: ComplianceReport) -> None:  # FIXED: Removed unused return
    """Save report as JSON file"""
    
    report_filename = f"{report.report_id}.json"
    report_path = settings.reports_dir / report_filename
    
    # FIXED: UTF-8 encoding
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, default=str, ensure_ascii=False)