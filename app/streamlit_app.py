"""
Streamlit UI for Imtithal.ai Compliance Scanner
"""

import streamlit as st
import requests
from pathlib import Path
import json
import pandas as pd
import os

# Page config
st.set_page_config(
    page_title="Imtithal.ai - Compliance Copilot",
    page_icon="⚖️",
    layout="wide"
)

# FIXED: Configurable API URL from environment
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


def main():
    """Main Streamlit application"""
    
    # Header
    st.title("⚖️ Imtithal.ai")
    st.markdown("**Compliance Copilot for Saudi SMEs** | امتثال - مساعد الامتثال للشركات السعودية")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.info(
            """
            **Imtithal.ai** helps Saudi SMEs:
            
            ✅ Scan workforce for Saudization compliance  
            ✅ Audit employment contracts  
            ✅ Get explainable risk assessments  
            ✅ Receive actionable recommendations
            
            ---
            
            **MVP Version:** 0.1.0  
            **Status:** Demo/Funding Prototype
            """
        )
        
        st.markdown("---")
        
        # Recent scans
        st.subheader("📊 Recent Scans")
        try:
            response = requests.get(f"{API_URL}/scans/recent?limit=5", timeout=5)
            if response.status_code == 200:
                scans = response.json()
                if scans:
                    for scan in scans:
                        risk_emoji = "🟢" if scan["risk_score"] < 25 else "🟡" if scan["risk_score"] < 50 else "🔴"
                        st.text(f"{risk_emoji} {scan['company_name']}")
                        st.caption(f"Risk: {scan['risk_score']:.0f} | {scan['timestamp'][:10]}")
                else:
                    st.text("No scans yet")
            else:
                st.warning("Unable to load recent scans")
        except:
            st.warning("API not available")
    
    # ADDED: Session state for resetting file uploaders
    if 'scan_counter' not in st.session_state:
        st.session_state.scan_counter = 0
    
    # Main content
    st.header("🔍 Run Compliance Scan")
    
    # Company Profile Section
    st.subheader("1️⃣ Company Profile")
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input("Company Name *", placeholder="Tech Innovations KSA")
        sector = st.selectbox(
            "Industry Sector *",
            ["Technology", "Retail", "Healthcare", "Construction", "Finance", "Manufacturing", "Other"]
        )
    
    with col2:
        total_employees = st.number_input("Total Employees *", min_value=1, value=50, step=1)
        saudi_employees = st.number_input("Saudi Employees *", min_value=0, value=30, step=1)
    
    non_saudi_employees = total_employees - saudi_employees
    
    # ADDED: Validation warning for count mismatch
    if saudi_employees + non_saudi_employees != total_employees:
        st.error(f"⚠️ Employee counts don't match: {saudi_employees} + {non_saudi_employees} ≠ {total_employees}")
    else:
        st.info(f"📊 Current Saudization: **{(saudi_employees/total_employees*100):.1f}%** ({saudi_employees} Saudi / {total_employees} total)")
    
    notes = st.text_area("Additional Notes (optional)", placeholder="Growing IT consulting firm...")
    
    st.markdown("---")
    
    # File Uploads Section
    st.subheader("2️⃣ Upload Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Employee Roster (CSV) ***")
        st.caption("Required columns: name, nationality, job_family, status")
        # FIXED: Add key for reset
        roster_file = st.file_uploader(
            "Upload CSV",
            type=["csv"],
            help="CSV file with employee data",
            key=f"roster_{st.session_state.scan_counter}"
        )
        
        if roster_file:
            st.success(f"✅ {roster_file.name}")
    
    with col2:
        st.markdown("**Employment Contracts (PDF) ***")
        st.caption("Upload one or more contract documents")
        # FIXED: Add key for reset
        contract_files = st.file_uploader(
            "Upload PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            help="Employment contract PDFs",
            key=f"contracts_{st.session_state.scan_counter}"
        )
        
        if contract_files:
            st.success(f"✅ {len(contract_files)} file(s) uploaded")
    
    st.markdown("---")
    
    # Submit button
    st.subheader("3️⃣ Run Scan")
    
    if st.button("🚀 Analyze Compliance", type="primary", use_container_width=True):
        
        # Validation
        if not company_name:
            st.error("❌ Company name is required")
            return
        
        if not roster_file:
            st.error("❌ Employee roster CSV is required")
            return
        
        if not contract_files:
            st.error("❌ At least one contract PDF is required")
            return
        
        # ADDED: Validate employee counts
        if saudi_employees + non_saudi_employees != total_employees:
            st.error("❌ Employee counts must add up correctly")
            return
        
        # Show loading
        with st.spinner("🔄 Analyzing compliance... This may take 30-60 seconds"):
            
            try:
                # FIXED: Prepare multipart form data correctly for multiple PDFs
                files = [
                    ("roster_file", (roster_file.name, roster_file.getvalue(), "text/csv"))
                ]
                
                # Add all contract files with same key (FastAPI List[UploadFile] support)
                for contract_file in contract_files:
                    files.append(
                        ("contract_files", (contract_file.name, contract_file.getvalue(), "application/pdf"))
                    )
                
                data = {
                    "company_name": company_name,
                    "sector": sector,
                    "total_employees": total_employees,
                    "saudi_employees": saudi_employees,
                    "non_saudi_employees": non_saudi_employees,
                    "notes": notes if notes else ""
                }
                
                # Call API
                response = requests.post(
                    f"{API_URL}/scan",
                    data=data,
                    files=files,
                    timeout=120  # ADDED: Longer timeout for file processing
                )
                
                if response.status_code == 200:
                    report = response.json()
                    
                    # ADDED: Increment scan counter to reset file uploaders
                    st.session_state.scan_counter += 1
                    
                    # Display results
                    display_results(report)
                    
                elif response.status_code == 413:
                    st.error("❌ One or more files are too large. Maximum file size: 10MB")
                elif response.status_code == 400:
                    st.error(f"❌ Validation error: {response.json().get('detail', 'Invalid input')}")
                else:
                    st.error(f"❌ Scan failed: {response.text}")
            
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. Files may be too large or server is busy.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure FastAPI backend is running at " + API_URL)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Make sure the FastAPI backend is running")


def display_results(report: dict):
    """Display compliance scan results"""
    
    st.success("✅ Compliance scan complete!")
    
    st.markdown("---")
    
    # Overall Risk Score
    st.header("📊 Compliance Summary")
    
    risk_score = report["overall_risk_score"]
    risk_level = report["risk_level"]
    
    # Risk score gauge
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.metric(
            "Overall Risk Score",
            f"{risk_score:.1f}/100",
            delta=None,
            help="Lower is better (0 = perfect compliance)"
        )
        
        # Color-coded risk level
        risk_colors = {
            "low": "🟢 Low Risk",
            "medium": "🟡 Medium Risk",
            "high": "🟠 High Risk",
            "critical": "🔴 Critical Risk"
        }
        st.markdown(f"### {risk_colors.get(risk_level, risk_level)}")
    
    with col2:
        st.write("")  # Spacer
    
    with col3:
        # Saudization status
        saud = report["saudization_compliance"]
        
        color_emojis = {
            "green": "🟢",
            "yellow": "🟡",
            "red": "🔴"
        }
        
        st.metric(
            "Saudization Rate",
            f"{saud['current_percentage']:.1f}%",
            delta=f"{saud['gap']:.1f}% vs target",
            help=f"Target: {saud['required_percentage']}%"
        )
        
        st.markdown(f"### {color_emojis.get(saud['color_band'], '⚪')} {saud['color_band'].upper()} Band")
    
    st.markdown("---")
    
    # Saudization Details
    st.subheader("👥 Saudization Compliance")
    
    st.info(saud["explanation"])
    
    # Roster summary
    roster = report["roster_summary"]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Employees", roster["total_count"])
    col2.metric("Saudi", roster["saudi_count"])
    col3.metric("Non-Saudi", roster["non_saudi_count"])
    col4.metric("Saudi %", f"{roster['saudi_percentage']:.1f}%")
    
    # Validation issues
    if roster.get("validation_issues"):
        st.warning("⚠️ **Data Quality Issues:**")
        for issue in roster["validation_issues"]:
            st.text(f"  • {issue}")
    
    st.markdown("---")
    
    # Risk Flags
    st.subheader("⚠️ Risk Flags")
    
    risk_flags = report.get("risk_flags", [])
    
    if risk_flags:
        for flag in risk_flags:
            severity_colors = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "critical": "🔴"
            }
            
            with st.expander(f"{severity_colors.get(flag['severity'], '⚪')} {flag['title']} [{flag['severity'].upper()}]"):
                st.markdown(f"**Category:** {flag['category']}")
                st.markdown(f"**Description:** {flag['description']}")
                st.markdown(f"**Affected Data:** {flag['affected_data']}")
                st.success(f"**Recommendation:** {flag['recommendation']}")
    else:
        st.success("✅ No risk flags detected")
    
    st.markdown("---")
    
    # Contract Findings
    st.subheader("📄 Contract Audit Findings")
    
    contract_findings = report.get("contract_findings", [])
    
    if contract_findings:
        for finding in contract_findings:
            severity_colors = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🔴"
            }
            
            st.markdown(
                f"{severity_colors.get(finding['severity'], '⚪')} "
                f"**{finding['document_name']}** - {finding['description']} "
                f"[{finding['severity'].upper()}]"
            )
    else:
        st.success("✅ No contract issues detected")
    
    st.markdown("---")
    
    # Priority Actions
    st.subheader("🎯 Recommended Actions")
    
    actions = report.get("priority_actions", [])
    
    for i, action in enumerate(actions, 1):
        st.markdown(f"{i}. {action}")
    
    st.markdown("---")
    
    # Download Report
    st.subheader("💾 Download Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # FIXED: Use ensure_ascii=False for Arabic support
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON Report",
            data=report_json,
            file_name=f"{report['report_id']}.json",
            mime="application/json"
        )
    
    with col2:
        st.info(f"**Report ID:** {report['report_id']}")
        st.caption(f"Generated: {report['scan_timestamp']}")
    
    # Disclaimer
    st.warning(report.get("disclaimer", "Manual legal review recommended."))


if __name__ == "__main__":
    main()