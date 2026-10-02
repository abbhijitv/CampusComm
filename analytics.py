"""Campus Comm analytics: turn related reports into clean emerging issues."""

from pathlib import Path
from typing import Optional

import pandas as pd


# ============================================================
# Constants
# ============================================================

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


# ============================================================
# Demo data
# ============================================================

def load_demo_reports(path=DEMO_DATA_PATH) -> pd.DataFrame:
    """Load local CSV demo reports."""
    return _prepare(pd.read_csv(path))


# ============================================================
# Emerging issue detection
# ============================================================

def detect_emerging_issues(
    reports_df: pd.DataFrame,
    window_hours: int = 24,
    min_reports: int = 1,
    now: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Turn individual campus reports into grouped dashboard issues.

    Reports are grouped by:

        LOCATION + CATEGORY + SUBCATEGORY

    This means related reports become one incident while unrelated
    problems remain separate.

    Example:

        5 Safety / Fire reports at Hayden Library
            -> one Hayden Library — Fire issue with 5 reports

        1 Technology / Wi-Fi report at Hayden Library
            -> separate Hayden Library — Wi-Fi issue

    Every valid recent report is represented in an issue as long as
    min_reports is 1.
    """

    df = _prepare(reports_df)

    if df.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    # Ignore reports that do not have a valid timestamp.
    df = df.dropna(subset=["CREATED_AT"])

    if df.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    # Use newest report as the reference point unless a specific
    # "now" timestamp is supplied.
    if now is None:
        now = df["CREATED_AT"].max()
    else:
        now = pd.Timestamp(now)

    # Only consider reports inside the selected time window.
    recent = df[
        df["CREATED_AT"]
        >= now - pd.Timedelta(hours=window_hours)
    ].copy()

    if recent.empty:
        return pd.DataFrame(columns=ISSUE_COLUMNS)

    issues = []

    # --------------------------------------------------------
    # Group related reports.
    #
    # IMPORTANT:
    # We group by location + category + subcategory.
    #
    # We DO NOT reduce this to one issue per category.
    # Otherwise legitimate reports can disappear from the
    # dashboard.
    # --------------------------------------------------------
    grouped = recent.groupby(
        [
            "LOCATION",
            "CATEGORY",
            "SUBCATEGORY",
        ],
        dropna=False,
    )

    for (
        location,
        category,
        subcategory,
    ), group in grouped:

        if len(group) < min_reports:
            continue

        location = _clean_value(
            location,
            "Unknown Location",
        )

        category = _clean_value(
            category,
            "Other",
        )

        subcategory = _clean_value(
            subcategory,
            "Other",
        )

        # Use the highest severity from all reports in this issue.
        severity = _highest_severity(
            group["SEVERITY"]
        )

        # Sort newest first so we can use the most recent
        # report's summary on the card.
        sorted_group = group.sort_values(
            "CREATED_AT",
            ascending=False,
        )

        latest = sorted_group.iloc[0]

        summary = _clean_value(
            latest.get("SUMMARY", ""),
            "",
        )

        # Fall back to report text if summary is missing.
        if not summary:
            summary = _clean_value(
                latest.get("REPORT_TEXT", ""),
                "No summary available.",
            )

        issues.append(
            {
                "TITLE": (
                    f"{location} — {subcategory}"
                ),
                "LOCATION": location,
                "CATEGORY": category,
                "SUBCATEGORY": subcategory,
                "SEVERITY": severity,
                "REPORT_COUNT": len(group),
                "SUMMARY": summary,
                "FIRST_REPORTED": (
                    group["CREATED_AT"].min()
                ),
                "LAST_REPORTED": (
                    group["CREATED_AT"].max()
                ),
            }
        )

    if not issues:
        return pd.DataFrame(
            columns=ISSUE_COLUMNS
        )

    result = pd.DataFrame(
        issues,
        columns=ISSUE_COLUMNS,
    )

    # --------------------------------------------------------
    # Severity ranking
    #
    # LOW      = 0
    # MEDIUM   = 1
    # HIGH     = 2
    # CRITICAL = 3
    # --------------------------------------------------------
    severity_rank = {
        severity: index
        for index, severity
        in enumerate(SEVERITY_ORDER)
    }

    result["_SEVERITY_RANK"] = (
        result["SEVERITY"]
        .map(severity_rank)
        .fillna(0)
    )

    # --------------------------------------------------------
    # Sort dashboard issues.
    #
    # Priority:
    # 1. Highest severity
    # 2. Largest number of reports
    # 3. Most recently reported
    #
    # IMPORTANT:
    # There is intentionally NO drop_duplicates(CATEGORY)
    # here. Every unique issue remains represented.
    # --------------------------------------------------------
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
        .drop(
            columns="_SEVERITY_RANK"
        )
        .reset_index(drop=True)
    )

    return result


# ============================================================
# Data preparation
# ============================================================

def _prepare(
    reports_df: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Snowflake or CSV report data."""

    if reports_df is None:
        return pd.DataFrame()

    df = reports_df.copy()

    # Normalize column names.
    df.columns = [
        str(column).upper()
        for column in df.columns
    ]

    # Make sure every column required by the analytics
    # pipeline exists.
    required_columns = [
        "CREATED_AT",
        "REPORT_TEXT",
        "LOCATION",
        "CATEGORY",
        "SUBCATEGORY",
        "SEVERITY",
        "SUMMARY",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    if df.empty:
        return df

    # Normalize timestamps.
    df["CREATED_AT"] = pd.to_datetime(
        df["CREATED_AT"],
        errors="coerce",
    )

    # Normalize text columns.
    text_columns = [
        "REPORT_TEXT",
        "LOCATION",
        "CATEGORY",
        "SUBCATEGORY",
        "SEVERITY",
        "SUMMARY",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # Normalize severity capitalization.
    df["SEVERITY"] = (
        df["SEVERITY"]
        .str.upper()
    )

    # Safe defaults for grouping.
    df.loc[
        df["LOCATION"] == "",
        "LOCATION",
    ] = "Unknown Location"

    df.loc[
        df["CATEGORY"] == "",
        "CATEGORY",
    ] = "Other"

    df.loc[
        df["SUBCATEGORY"] == "",
        "SUBCATEGORY",
    ] = "Other"

    return df


# ============================================================
# Utility helpers
# ============================================================

def _clean_value(
    value,
    default: str,
) -> str:
    """Convert missing/blank values into a safe display value."""

    if pd.isna(value):
        return default

    value = str(value).strip()

    if (
        not value
        or value.lower() == "nan"
    ):
        return default

    return value


def _highest_severity(
    severities: pd.Series,
) -> str:
    """Return the highest valid severity in a report group."""

    known = [
        str(severity).strip().upper()
        for severity in severities
        if (
            str(severity).strip().upper()
            in SEVERITY_ORDER
        )
    ]

    if not known:
        return "MEDIUM"

    return max(
        known,
        key=SEVERITY_ORDER.index,
    )