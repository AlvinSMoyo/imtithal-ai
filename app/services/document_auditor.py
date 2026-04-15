"""
Contract document compliance auditor

Checks employment contracts for required clauses and suspicious terms
"""

import json
import re
from typing import Dict, List

from app.config import settings
from app.models.compliance import DocumentFinding


def load_contract_rules() -> Dict:
    """Load contract audit rules from JSON"""
    try:
        with open(settings.rules_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print("⚠️ WARNING: compliance_rules.json not found for contract rules. Using fallback.")
        return {
            "contract_required_clauses": [
                "probation period",
                "termination notice",
                "salary details",
                "working hours",
                "annual leave",
            ],
            "suspicious_terms": [
                "waive rights",
                "no compensation",
                "unpaid overtime",
                "unlimited working hours",
                "no annual leave",
                "immediate termination without notice",
            ],
        }


def _normalize_text(text: str) -> str:
    """Normalize text for broader phrase matching."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def audit_contracts(contract_texts: List[Dict]) -> List[DocumentFinding]:
    """
    Audit contract documents for compliance issues.
    """
    rules = load_contract_rules()
    findings: List[DocumentFinding] = []

    required_clauses = rules.get("contract_required_clauses", [])
    suspicious_terms = rules.get("suspicious_terms", [])

    toxic_patterns = {
        "unpaid overtime / compensation risk": [
            "no compensation",
            "unpaid overtime",
            "without additional compensation",
            "without additional pay",
            "no paid overtime",
        ],
        "rights waiver / legal override risk": [
            "waive rights",
            "no legal claims",
            "supersedes local labor regulations",
            "supersedes local law",
        ],
        "illegal termination risk": [
            "termination without notice",
            "immediate termination",
            "immediate termination without notice",
        ],
    }

    for contract in contract_texts:
        filename = contract["filename"]
        raw_text = contract["text"]
        text = _normalize_text(raw_text)

        # Required clause checks
        for clause in required_clauses:
            if clause.lower() not in text:
                findings.append(
                    DocumentFinding(
                        document_name=filename,
                        finding_type="missing_clause",
                        description=f"Contract may be missing required clause: '{clause}' (preliminary pattern match)",
                        severity="medium",
                    )
                )

        # Original suspicious term checks
        for term in suspicious_terms:
            if term.lower() in text:
                findings.append(
                    DocumentFinding(
                        document_name=filename,
                        finding_type="suspicious_term",
                        description=f"Contract contains potentially problematic term: '{term}' (requires manual review)",
                        severity="high",
                    )
                )

        # Broader grouped toxic pattern matching
        for category, phrases in toxic_patterns.items():
            for phrase in phrases:
                if phrase in text:
                    findings.append(
                        DocumentFinding(
                            document_name=filename,
                            finding_type="suspicious_term",
                            description=f"Critical Risk: Found reference to '{phrase}' under category '{category}'",
                            severity="high",
                        )
                    )

        # Very short contract warning
        if len(text.strip()) < 500:
            findings.append(
                DocumentFinding(
                    document_name=filename,
                    finding_type="needs_review",
                    description="Contract appears unusually short (< 500 characters). May be incomplete or improperly scanned.",
                    severity="medium",
                )
            )

        # Extraction failure checks
        if text.startswith("[no text extracted") or text.startswith("[pdf extraction error"):
            findings.append(
                DocumentFinding(
                    document_name=filename,
                    finding_type="needs_review",
                    description="Unable to extract text from PDF. Manual review required.",
                    severity="high",
                )
            )

    return findings