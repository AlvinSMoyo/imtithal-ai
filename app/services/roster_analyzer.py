"""
Employee roster CSV parsing and analysis
"""

from pathlib import Path
from typing import Dict

import pandas as pd

from app.config import settings
from app.models.compliance import RosterSummary


REQUIRED_COLUMNS = ["name", "nationality", "job_family", "status"]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CSV headers to reduce failures caused by:
    - BOM markers
    - extra spaces
    - case differences
    - quoted headers
    """
    normalized = []
    for col in df.columns:
        clean = str(col).replace("\ufeff", "").strip().strip('"').strip("'").lower()
        normalized.append(clean)
    df.columns = normalized
    return df


def analyze_roster(roster_path: Path) -> RosterSummary:
    """
    Parse and analyze employee roster CSV

    Expected columns:
    - name
    - nationality
    - job_family
    - status
    """

    validation_issues: list[str] = []

    try:
        # utf-8-sig handles BOM better than plain utf-8 for Excel-style CSVs
        df = pd.read_csv(roster_path, encoding="utf-8-sig")
        df = _normalize_columns(df)

        if len(df) > settings.max_roster_rows:
            validation_issues.append(
                f"Roster exceeds maximum rows ({settings.max_roster_rows}). "
                f"Processing first {settings.max_roster_rows} rows only."
            )
            df = df.head(settings.max_roster_rows)

        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            validation_issues.append(
                f"Missing required columns: {', '.join(missing_cols)}"
            )
            return RosterSummary(
                total_count=0,
                saudi_count=0,
                non_saudi_count=0,
                saudi_percentage=0.0,
                validation_issues=validation_issues,
            )

        # Normalize values too
        for col in REQUIRED_COLUMNS:
            df[col] = df[col].astype(str).str.strip()

        active_df = df[df["status"].str.lower() == "active"].copy()

        inactive_count = len(df) - len(active_df)
        if inactive_count > 0:
            validation_issues.append(
                f"{inactive_count} employees have non-active or missing status (excluded from analysis)"
            )

        total_count = len(active_df)

        if total_count == 0:
            validation_issues.append("No active employees found in roster")
            return RosterSummary(
                total_count=0,
                saudi_count=0,
                non_saudi_count=0,
                saudi_percentage=0.0,
                validation_issues=validation_issues,
            )

        saudi_mask = active_df["nationality"].str.lower().str.contains("saudi", na=False)
        saudi_count = int(saudi_mask.sum())
        non_saudi_count = total_count - saudi_count
        saudi_percentage = round((saudi_count / total_count) * 100, 2)

        if active_df["name"].replace("nan", "").eq("").any():
            missing_name_count = int(active_df["name"].replace("nan", "").eq("").sum())
            validation_issues.append(f"{missing_name_count} employees missing names")

        if active_df["nationality"].replace("nan", "").eq("").any():
            missing_nat_count = int(
                active_df["nationality"].replace("nan", "").eq("").sum()
            )
            validation_issues.append(
                f"{missing_nat_count} employees missing nationality"
            )

        return RosterSummary(
            total_count=total_count,
            saudi_count=saudi_count,
            non_saudi_count=non_saudi_count,
            saudi_percentage=saudi_percentage,
            validation_issues=validation_issues,
        )

    except Exception as e:
        validation_issues.append(f"CSV parsing error: {str(e)}")
        return RosterSummary(
            total_count=0,
            saudi_count=0,
            non_saudi_count=0,
            saudi_percentage=0.0,
            validation_issues=validation_issues,
        )


def get_roster_breakdown(roster_path: Path) -> Dict:
    """
    Get detailed roster breakdown by job family.
    """
    try:
        df = pd.read_csv(roster_path, encoding="utf-8-sig")
        df = _normalize_columns(df)

        if "job_family" not in df.columns:
            return {"error": "job_family column not found"}

        if "status" in df.columns:
            df["status"] = df["status"].astype(str).str.strip()
            active_df = df[df["status"].str.lower() == "active"].copy()
        else:
            active_df = df.copy()

        if "nationality" in active_df.columns:
            active_df["nationality"] = active_df["nationality"].astype(str).str.strip()

        breakdown = (
            active_df.groupby("job_family")
            .agg(
                total=("job_family", "count"),
                saudi_count=(
                    "nationality",
                    lambda x: x.astype(str).str.lower().str.contains("saudi", na=False).sum(),
                ),
            )
            .reset_index()
        )

        breakdown["non_saudi_count"] = breakdown["total"] - breakdown["saudi_count"]
        breakdown["saudi_percentage"] = round(
            (breakdown["saudi_count"] / breakdown["total"]) * 100, 2
        )

        return breakdown.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}