"""
Nitaqat/Saudization compliance calculation engine

⚠️ IMPORTANT DISCLAIMER:
The rules and thresholds in this file are MOCK EXAMPLES for MVP demonstration only.
They are NOT authoritative legal values.

Before production use:
1. Verify all thresholds with Saudi labor law counsel
2. Integrate with official Qiwa/Mudad APIs
3. Update rules based on current Nitaqat regulations
4. Add sector-specific calculation logic
"""

import json
from pathlib import Path
from typing import Dict, List

from app.config import settings
from app.models.company import CompanyProfile
from app.models.compliance import RosterSummary, SaudizationCompliance, RiskFlag


def load_compliance_rules() -> Dict:
    """
    Load compliance rules from JSON file
    
    Returns:
        Dictionary of rules and thresholds
    """
    
    try:
        # FIXED: UTF-8 encoding for Arabic support
        with open(settings.rules_file, "r", encoding="utf-8") as f:
            rules = json.load(f)
        return rules
    except FileNotFoundError:
        # ADDED: Log warning about using fallback rules
        print("⚠️ WARNING: compliance_rules.json not found. Using fallback mock rules.")
        # Fallback: return minimal mock rules
        return {
            "nitaqat_thresholds": {
                "default": {
                    "green": 50,
                    "yellow": 30,
                    "red": 0
                }
            },
            "contract_required_clauses": [
                "probation period",
                "termination notice",
                "salary details"
            ]
        }


def calculate_compliance_score(
    company_profile: CompanyProfile,
    roster_summary: RosterSummary
) -> Dict:
    """
    Calculate Nitaqat compliance status and risk score
    
    Args:
        company_profile: Company information
        roster_summary: Analyzed roster data
    
    Returns:
        Dictionary with compliance status and risk flags
    """
    
    rules = load_compliance_rules()
    risk_flags = []
    
    # Get sector-specific thresholds (or default)
    sector_key = company_profile.sector.lower()
    thresholds = rules.get("nitaqat_thresholds", {}).get(
        sector_key,
        rules.get("nitaqat_thresholds", {}).get("default", {
            "green": 50,
            "yellow": 30,
            "red": 0
        })
    )
    
    current_percentage = roster_summary.saudi_percentage
    required_percentage = thresholds.get("green", 50)
    gap = current_percentage - required_percentage
    
    # Determine color band and status
    if current_percentage >= thresholds.get("green", 50):
        color_band = "green"
        status = "compliant"
        # FIXED: Soften authoritative language
        explanation = (
            f"Preliminary scan suggests Saudization rate ({current_percentage:.1f}%) "
            f"appears to meet the green band threshold ({required_percentage}%). "
            f"Manual verification recommended."
        )
    elif current_percentage >= thresholds.get("yellow", 30):
        color_band = "yellow"
        status = "at_risk"
        # FIXED: Soften language
        explanation = (
            f"Preliminary scan indicates Saudization rate ({current_percentage:.1f}%) "
            f"may be in the yellow band. Approximately {required_percentage - current_percentage:.1f}% "
            f"more Saudi employees may be needed to reach green band. Manual verification recommended."
        )
        
        # Add risk flag
        risk_flags.append(RiskFlag(
            severity="medium",
            category="saudization",
            title="Saudization Rate May Be Below Green Band",
            description=f"Current rate: {current_percentage:.1f}%, Possible green band requirement: {required_percentage}%",
            affected_data=f"{roster_summary.saudi_count}/{roster_summary.total_count} employees are Saudi (per roster)",
            recommendation=f"Consider hiring approximately {calculate_required_hires(roster_summary, required_percentage)} additional Saudi employees. Verify with Qiwa portal for official status."
        ))
    else:
        color_band = "red"
        status = "non_compliant"
        # FIXED: Soften language
        explanation = (
            f"⚠️ Preliminary scan suggests Saudization rate ({current_percentage:.1f}%) "
            f"may be critically low (possible red band). Immediate legal review recommended."
        )
        
        # Add critical risk flag
        risk_flags.append(RiskFlag(
            severity="critical",
            category="saudization",
            title="Possible Critical Saudization Non-Compliance",
            description=f"Current rate: {current_percentage:.1f}%, Minimum threshold may be: {thresholds.get('yellow', 30)}%",
            affected_data=f"Only {roster_summary.saudi_count}/{roster_summary.total_count} employees are Saudi (per roster)",
            recommendation=f"URGENT: Consult with Saudi labor law counsel immediately. Approximately {calculate_required_hires(roster_summary, required_percentage)} Saudi hires may be needed. Verify official status via Qiwa portal."
        ))
    
    # Check for roster validation issues
    if roster_summary.validation_issues:
        risk_flags.append(RiskFlag(
            severity="medium",
            category="labor_law",
            title="Data Quality Issues Detected in Roster",
            description="Employee roster has validation issues that may affect compliance calculations",
            affected_data="; ".join(roster_summary.validation_issues),
            recommendation="Review and correct roster data to ensure accurate compliance reporting."
        ))
    
    # Check if reported counts match roster
    if company_profile.total_employees != roster_summary.total_count:
        risk_flags.append(RiskFlag(
            severity="low",
            category="labor_law",
            title="Employee Count Mismatch Between Profile and Roster",
            description=f"Company profile shows {company_profile.total_employees} employees, but roster contains {roster_summary.total_count} active employees",
            affected_data=f"Discrepancy: {abs(company_profile.total_employees - roster_summary.total_count)} employees",
            recommendation="Update company profile or roster to ensure counts match official records in Qiwa/Mudad systems."
        ))
    
    return {
        "saudization_compliance": SaudizationCompliance(
            status=status,
            current_percentage=current_percentage,
            required_percentage=required_percentage,
            gap=round(gap, 2),
            color_band=color_band,
            explanation=explanation
        ),
        "risk_flags": risk_flags
    }


def calculate_required_hires(roster_summary: RosterSummary, target_percentage: float) -> int:
    """
    Calculate number of Saudi employees needed to reach target percentage
    
    Formula:
    target_percentage = (current_saudi + x) / (total + x) * 100
    Solve for x (where x = additional Saudi hires)
    """
    
    current_saudi = roster_summary.saudi_count
    total = roster_summary.total_count
    target = target_percentage / 100
    
    # x = (target * total - current_saudi) / (1 - target)
    required = (target * total - current_saudi) / (1 - target)
    
    return max(0, int(required) + 1)  # Round up