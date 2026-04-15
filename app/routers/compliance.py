"""
Compliance scanning endpoints
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from app.database import get_db, ComplianceScan
from app.models.company import CompanyProfile
from app.models.compliance import ComplianceReport
from app.services.storage_service import save_upload, validate_file_size
from app.services.roster_analyzer import analyze_roster
from app.services.pdf_parser import extract_pdf_text
from app.services.nitaqat_engine import calculate_compliance_score
from app.services.document_auditor import audit_contracts
from app.services.report_builder import build_report

router = APIRouter()


@router.post("/scan", response_model=ComplianceReport)
async def run_compliance_scan(
    # Company profile
    company_name: str = Form(...),
    sector: str = Form(...),
    total_employees: int = Form(...),
    saudi_employees: int = Form(...),
    non_saudi_employees: int = Form(...),
    notes: str = Form(None),
    
    # File uploads
    roster_file: UploadFile = File(...),
    contract_files: List[UploadFile] = File(...),
    
    # Database session
    db: Session = Depends(get_db)
):
    """
    Run compliance scan on uploaded company data
    
    Steps:
    1. Validate inputs
    2. Save uploaded files
    3. Parse employee roster (CSV)
    4. Extract contract text (PDFs)
    5. Run compliance analysis
    6. Generate report
    7. Optionally save scan to database
    """
    
    try:
        # ADDED: Validate employee count math
        if saudi_employees + non_saudi_employees != total_employees:
            raise HTTPException(
                status_code=400,
                detail=f"Employee counts don't match: {saudi_employees} Saudi + "
                       f"{non_saudi_employees} non-Saudi ≠ {total_employees} total"
            )
        
        # ADDED: Validate counts are non-negative
        if saudi_employees < 0 or non_saudi_employees < 0 or total_employees < 1:
            raise HTTPException(
                status_code=400,
                detail="Employee counts must be non-negative and total must be at least 1"
            )
        
        # 1. Create company profile
        company = CompanyProfile(
            company_name=company_name,
            sector=sector,
            total_employees=total_employees,
            saudi_employees=saudi_employees,
            non_saudi_employees=non_saudi_employees,
            notes=notes
        )
        
        # ADDED: Validate file sizes
        validate_file_size(roster_file)
        for contract_file in contract_files:
            validate_file_size(contract_file)
        
        # 2. Save roster file
        roster_path = await save_upload(roster_file, "rosters")
        
        # 3. Parse roster
        roster_summary = analyze_roster(roster_path)
        
        # 4. Save and parse contract PDFs
        contract_texts = []
        contract_paths = []
        
        for contract_file in contract_files:
            contract_path = await save_upload(contract_file, "contracts")
            contract_paths.append(str(contract_path))
            
            text = extract_pdf_text(contract_path)
            contract_texts.append({
                "filename": contract_file.filename,
                "text": text
            })
        
        # 5. Run Nitaqat compliance check
        compliance_result = calculate_compliance_score(
            company_profile=company,
            roster_summary=roster_summary
        )
        
        # 6. Audit contract documents
        contract_findings = audit_contracts(contract_texts)
        
        # 7. Build final report
        report = build_report(
            company=company,
            roster_summary=roster_summary,
            compliance_result=compliance_result,
            contract_findings=contract_findings
        )
        
        # 8. FIXED: Optionally save scan to database (don't fail scan if DB fails)
        try:
            scan_record = ComplianceScan(
                company_id=None,  # No user auth in MVP
                company_name=company_name,
                scan_timestamp=datetime.utcnow(),
                roster_file=str(roster_path),
                contract_files=json.dumps(contract_paths),
                overall_risk_score=report.overall_risk_score,
                saudization_status=report.saudization_compliance.status,
                risk_flags_count=len(report.risk_flags),
                report_file=report.report_id
            )
            
            db.add(scan_record)
            db.commit()
        except Exception as db_error:
            # FIXED: Rollback and log, but continue returning report
            db.rollback()
            print(f"⚠️ Database save failed (scan still succeeded): {db_error}")
        
        return report
        
    except HTTPException:
        # Re-raise validation errors
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Compliance scan failed: {str(e)}"
        )


@router.get("/scans/recent")
async def get_recent_scans(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent compliance scans"""
    
    try:
        scans = db.query(ComplianceScan)\
            .order_by(ComplianceScan.scan_timestamp.desc())\
            .limit(limit)\
            .all()
        
        return [
            {
                "id": scan.id,
                "company_name": scan.company_name,
                "timestamp": scan.scan_timestamp.isoformat(),
                "risk_score": scan.overall_risk_score,
                "status": scan.saudization_status,
                "risk_flags": scan.risk_flags_count
            }
            for scan in scans
        ]
    except Exception as e:
        # FIXED: Don't crash UI if database unavailable
        print(f"⚠️ Database query failed: {e}")
        return []