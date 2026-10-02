"""Campus Comm analytics: turn related reports into clean emerging issues."""

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
    "SUMMARY",
    "FIRST_REPORTED",
    "LAST_REPORTED",
]


def load_demo_reports(path=DEMO_DATA_PATH) -> pd.DataFrame:
    """Load local CSV demo reports."""
    return _prepare(pd.read_csv(path))


def detect_emerging_issues(
    reports_df: pd.DataFrame,
    window_hours: int = 24,
    min_reports: int = 1,
    now: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Turn reports into dashboard issues.

    Reports are grouped by:
        location + category + subcategory

    This prevents unrelated problems at the same location from being
    merged together.

    The strongest issue from each category is returned so the dashboard
    stays organized and displays at most one card per category.
    """

    df = _prepare(reports_df)

    if df.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    # Ignore rows without valid timestamps.
    df = df.dropna(subset=["CREATED_AT"])

    if df.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    if now is None:
        now = df["CREATED_AT"].max()

    recent = df[
        df["CREATED_AT"] >= now - pd.Timedelta(hours=window_hours)
    ].copy()

    if recent.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    issues = []

    # IMPORTANT:
    # Include SUBCATEGORY so Fire, Wi-Fi, Equipment, etc.
    # do not accidentally get merged.
    for (location, category, subcategory), group in recent.groupby(
        ["LOCATION", "CATEGORY", "SUBCATEGORY"],
        dropna=False,
    ):
        if len(group) < min_reports:
            continue

        location = _clean_value(location, "Unknown Location")
        category = _clean_value(category, "Other")
        subcategory = _clean_value(subcategory, "Other")

        severity = _highest_severity(group["SEVERITY"])

        # Most recent report is used for the card summary.
        latest = group.sort_values(
            "CREATED_AT",
            ascending=False,
        ).iloc[0]

        summary = _clean_value(
            latest.get("SUMMARY", ""),
            "",
        )

        if not summary:
            summary = _clean_value(
                latest.get("REPORT_TEXT", ""),
                "No summary available.",
            )

        issues.append(
            {
                "TITLE": f"{location} — {subcategory}",
                "LOCATION": location,
                "CATEGORY": category,
                "SUBCATEGORY": subcategory,
                "SEVERITY": severity,
                "REPORT_COUNT": len(group),
                "SUMMARY": summary,
                "FIRST_REPORTED": group["CREATED_AT"].min(),
                "LAST_REPORTED": group["CREATED_AT"].max(),
            }
        )

    if not issues:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    result = pd.DataFrame(
        issues,
        columns=ISSUE_COLUMNS,
    )

    # Convert severity into a sortable numeric rank.
    result["_SEVERITY_RANK"] = (
        result["SEVERITY"]
        .map({
            name: i
            for i, name in enumerate(SEVERITY_ORDER)
        })
        .fillna(0)
    )

    # ---------------------------------------------------------
    # Keep ONE representative issue per category.
    #
    # Priority:
    # 1. Highest severity
    # 2. Most reports
    # 3. Most recent report
    # ---------------------------------------------------------
    result = (
        result
        .sort_values(
            [
                "CATEGORY",
                "_SEVERITY_RANK",
                "REPORT_COUNT",
                "LAST_REPORTED",
            ],
            ascending=[
                True,
                False,
                False,
                False,
            ],
        )
        .drop_duplicates(
            subset=["CATEGORY"],
            keep="first",
        )
    )

    # ---------------------------------------------------------
    # Sort dashboard cards:
    # CRITICAL -> HIGH -> MEDIUM -> LOW
    # Then report count and recency.
    # ---------------------------------------------------------
    result = (
        result
        .sort_values(
            [
                "_SEVERITY_RANK",
                "REPORT_COUNT",
                "LAST_REPORTED",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .drop(columns="_SEVERITY_RANK")
        .reset_index(drop=True)
    )

    return result


def _prepare(reports_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Snowflake or CSV report data."""

    df = reports_df.copy()

    df.columns = [
        str(c).upper()
        for c in df.columns
    ]

    # Make sure required columns always exist.
    required_columns = [
        "CREATED_AT",
        "REPORT_TEXT",
        "LOCATION",
        "CATEGORY",
        "SUBCATEGORY",
        "SEVERITY",
        "SUMMARY",
    ]

    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

    if df.empty:
        return df

    df["CREATED_AT"] = pd.to_datetime(
        df["CREATED_AT"],
        errors="coerce",
    )

    # Normalize text columns.
    for col in [
        "REPORT_TEXT",
        "LOCATION",
        "CATEGORY",
        "SUBCATEGORY",
        "SEVERITY",
        "SUMMARY",
    ]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Normalize severity capitalization.
    df["SEVERITY"] = df["SEVERITY"].str.upper()

    # Safe defaults.
    df.loc[df["LOCATION"] == "", "LOCATION"] = "Unknown Location"
    df.loc[df["CATEGORY"] == "", "CATEGORY"] = "Other"
    df.loc[df["SUBCATEGORY"] == "", "SUBCATEGORY"] = "Other"

    return df


def _clean_value(value, default: str) -> str:
    """Convert missing/blank values into a safe display value."""

    if pd.isna(value):
        return default

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return default

    return value


def _highest_severity(severities: pd.Series) -> str:
    """Return the highest valid severity in a group."""

    known = [
        str(s).strip().upper()
        for s in severities
        if str(s).strip().upper() in SEVERITY_ORDER
    ]

    if not known:
        return "MEDIUM"

    return max(
        known,
        key=SEVERITY_ORDER.index,
    )