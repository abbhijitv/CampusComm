"""Campus Comm analytics: detect emerging issues from groups of related reports."""

from pathlib import Path
from typing import Optional

import pandas as pd

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
DEMO_DATA_PATH = Path(__file__).parent / "data" / "campus_reports.csv"

ISSUE_COLUMNS = [
    "TITLE",
    "LOCATION",
    "CATEGORY",
    "SUBCATEGORY",
    "SEVERITY",
    "REPORT_COUNT",
    "FIRST_REPORTED",
    "LAST_REPORTED",
]


def load_demo_reports(path=DEMO_DATA_PATH) -> pd.DataFrame:
    """Load the synthetic demo reports (same columns as CAMPUS_REPORTS)."""
    return _prepare(pd.read_csv(path))


def detect_emerging_issues(
    reports_df: pd.DataFrame,
    window_hours: int = 24,
    min_reports: int = 3,
    now: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Group recent reports by location + category and flag busy groups.

    A group becomes an emerging issue when it has at least `min_reports`
    reports within the last `window_hours`. The window ends at `now`, which
    defaults to the most recent report so the demo data keeps working on any
    date. Pass `now=pd.Timestamp.now()` to anchor it to the real clock.

    Returns one row per issue with ISSUE_COLUMNS, most reports first.
    """
    df = _prepare(reports_df)
    if df.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    if now is None:
        now = df["CREATED_AT"].max()
    recent = df[df["CREATED_AT"] >= now - pd.Timedelta(hours=window_hours)]

    issues = []
    for (location, category), group in recent.groupby(["LOCATION", "CATEGORY"]):
        if len(group) < min_reports:
            continue
        subcategory = group["SUBCATEGORY"].mode().iloc[0]
        issues.append({
            "TITLE": f"{location} {subcategory} Problems",
            "LOCATION": location,
            "CATEGORY": category,
            "SUBCATEGORY": subcategory,
            "SEVERITY": _highest_severity(group["SEVERITY"]),
            "REPORT_COUNT": len(group),
            "FIRST_REPORTED": group["CREATED_AT"].min(),
            "LAST_REPORTED": group["CREATED_AT"].max(),
        })

    if not issues:
        return pd.DataFrame(columns=ISSUE_COLUMNS)
    return (
        pd.DataFrame(issues, columns=ISSUE_COLUMNS)
        .sort_values(["REPORT_COUNT", "LAST_REPORTED"], ascending=False)
        .reset_index(drop=True)
    )


def _prepare(reports_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names (Snowflake returns UPPERCASE) and timestamp type."""
    df = reports_df.copy()
    df.columns = [c.upper() for c in df.columns]
    df["CREATED_AT"] = pd.to_datetime(df["CREATED_AT"])
    return df


def _highest_severity(severities: pd.Series) -> str:
    known = [str(s).upper() for s in severities if str(s).upper() in SEVERITY_ORDER]
    if not known:
        return "MEDIUM"
    return max(known, key=SEVERITY_ORDER.index)
