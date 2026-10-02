"""Snowflake database helpers for Campus Comm."""

import os

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv


load_dotenv()


# ============================================================
# Department routing
# ============================================================

DEPARTMENT_ROUTES = {
    "Safety": "Campus Safety",
    "Technology": "IT Support",
    "Facilities": "Facilities Management",
    "Transportation": "Parking & Transit",
    "Academic": "Academic Affairs",
    "Student Services": "Student Services",
    "Other": "Campus Operations",
}


def get_department_for_category(category):
    """Return the department responsible for a report category."""
    return DEPARTMENT_ROUTES.get(
        str(category).strip(),
        "Campus Operations",
    )


# ============================================================
# Snowflake connection
# ============================================================

def get_connection():
    """Create a connection to the Campus Comm Snowflake database."""

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


# ============================================================
# Reports
# ============================================================

def save_report(
    report_text,
    location,
    category,
    subcategory,
    severity,
    summary,
):
    """Save one AI-classified campus report to Snowflake."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO CAMPUS_REPORTS (
            REPORT_TEXT,
            LOCATION,
            CATEGORY,
            SUBCATEGORY,
            SEVERITY,
            SUMMARY
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                report_text,
                location,
                category,
                subcategory,
                severity,
                summary,
            ),
        )

        conn.commit()
        return True

    finally:
        cursor.close()
        conn.close()


def get_recent_reports(limit=100):
    """Return recent active reports as a pandas DataFrame."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT
            REPORT_ID,
            CREATED_AT,
            REPORT_TEXT,
            LOCATION,
            CATEGORY,
            SUBCATEGORY,
            SEVERITY,
            SUMMARY,
            STATUS
        FROM CAMPUS_REPORTS
        WHERE UPPER(COALESCE(STATUS, 'ACTIVE')) = 'ACTIVE'
        ORDER BY CREATED_AT DESC
        LIMIT %s
        """

        cursor.execute(
            query,
            (limit,),
        )

        rows = cursor.fetchall()

        columns = [
            "REPORT_ID",
            "CREATED_AT",
            "REPORT_TEXT",
            "LOCATION",
            "CATEGORY",
            "SUBCATEGORY",
            "SEVERITY",
            "SUMMARY",
            "STATUS",
        ]

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    finally:
        cursor.close()
        conn.close()


def get_dashboard_stats():
    """Return statistics used by the Streamlit dashboard."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT
            COUNT(*) AS TOTAL,

            COUNT_IF(
                CAST(CREATED_AT AS DATE) = CURRENT_DATE()
            ) AS TODAY,

            COUNT_IF(
                UPPER(SEVERITY) IN ('HIGH', 'CRITICAL')
            ) AS HIGH_SEVERITY,

            COUNT(
                DISTINCT NULLIF(TRIM(LOCATION), '')
            ) AS LOCATIONS,

            COUNT_IF(
                UPPER(SEVERITY) = 'CRITICAL'
            ) AS CRITICAL,

            COUNT_IF(
                UPPER(COALESCE(STATUS, 'ACTIVE')) = 'ACTIVE'
            ) AS ACTIVE

        FROM CAMPUS_REPORTS

        WHERE UPPER(
            COALESCE(STATUS, 'ACTIVE')
        ) = 'ACTIVE'
        """

        cursor.execute(query)

        row = cursor.fetchone()

        return {
            "total": row[0] or 0,
            "today": row[1] or 0,
            "high_severity": row[2] or 0,
            "locations": row[3] or 0,
            "critical": row[4] or 0,
            "active": row[5] or 0,
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================
# Incidents
# ============================================================

def sync_incidents(issues_df):
    """
    Synchronize detected dashboard issues into INCIDENTS.

    An incident is uniquely identified for the demo by:
        LOCATION + CATEGORY + SUBCATEGORY

    Existing incidents are updated with the newest severity,
    report count, title, and summary.

    New issue clusters create new incidents.

    Resolved incidents stay resolved unless a newer report arrives
    after they were resolved, in which case the incident is reopened.
    """

    if issues_df is None or issues_df.empty:
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for _, issue in issues_df.iterrows():

            title = str(
                issue.get("TITLE", "Campus Issue")
            ).strip()

            location = str(
                issue.get("LOCATION", "Unknown Location")
            ).strip()

            category = str(
                issue.get("CATEGORY", "Other")
            ).strip()

            subcategory = str(
                issue.get("SUBCATEGORY", "Other")
            ).strip()

            severity = str(
                issue.get("SEVERITY", "MEDIUM")
            ).strip().upper()

            report_count = int(
                issue.get("REPORT_COUNT", 1)
            )

            summary = str(
                issue.get("SUMMARY", "")
            ).strip()

            last_reported = issue.get(
                "LAST_REPORTED"
            )

            department = get_department_for_category(
                category
            )

            # Find an existing incident for the same cluster.
            cursor.execute(
                """
                SELECT
                    INCIDENT_ID,
                    STATUS,
                    RESOLVED_AT
                FROM INCIDENTS
                WHERE LOCATION = %s
                  AND CATEGORY = %s
                  AND COALESCE(SUBCATEGORY, 'Other') = %s
                ORDER BY CREATED_AT DESC
                LIMIT 1
                """,
                (
                    location,
                    category,
                    subcategory,
                ),
            )

            existing = cursor.fetchone()

            if existing:
                incident_id = existing[0]
                current_status = (
                    existing[1] or "NEW"
                ).upper()
                resolved_at = existing[2]

                new_status = current_status

                # If a new report arrived after resolution,
                # reopen the incident.
                if (
                    current_status == "RESOLVED"
                    and resolved_at is not None
                    and last_reported is not None
                ):
                    last_reported_ts = pd.Timestamp(
                        last_reported
                    )
                    resolved_ts = pd.Timestamp(
                        resolved_at
                    )

                    if last_reported_ts > resolved_ts:
                        new_status = "NEW"

                cursor.execute(
                    """
                    UPDATE INCIDENTS
                    SET
                        UPDATED_AT = CURRENT_TIMESTAMP(),
                        TITLE = %s,
                        SEVERITY = %s,
                        REPORT_COUNT = %s,
                        SUMMARY = %s,
                        ASSIGNED_DEPARTMENT = %s,
                        STATUS = %s,
                        RESOLVED_AT =
                            CASE
                                WHEN %s = 'NEW'
                                THEN NULL
                                ELSE RESOLVED_AT
                            END
                    WHERE INCIDENT_ID = %s
                    """,
                    (
                        title,
                        severity,
                        report_count,
                        summary,
                        department,
                        new_status,
                        new_status,
                        incident_id,
                    ),
                )

            else:
                cursor.execute(
                    """
                    INSERT INTO INCIDENTS (
                        TITLE,
                        LOCATION,
                        CATEGORY,
                        SUBCATEGORY,
                        SEVERITY,
                        REPORT_COUNT,
                        SUMMARY,
                        ASSIGNED_DEPARTMENT,
                        STATUS
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, 'NEW'
                    )
                    """,
                    (
                        title,
                        location,
                        category,
                        subcategory,
                        severity,
                        report_count,
                        summary,
                        department,
                    ),
                )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


def get_incidents():
    """Return all incidents."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT
            INCIDENT_ID,
            CREATED_AT,
            UPDATED_AT,
            TITLE,
            LOCATION,
            CATEGORY,
            SUBCATEGORY,
            SEVERITY,
            REPORT_COUNT,
            SUMMARY,
            ASSIGNED_DEPARTMENT,
            STATUS,
            ACKNOWLEDGED_AT,
            RESOLVED_AT
        FROM INCIDENTS
        ORDER BY
            CASE UPPER(SEVERITY)
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END,
            UPDATED_AT DESC
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        columns = [
            "INCIDENT_ID",
            "CREATED_AT",
            "UPDATED_AT",
            "TITLE",
            "LOCATION",
            "CATEGORY",
            "SUBCATEGORY",
            "SEVERITY",
            "REPORT_COUNT",
            "SUMMARY",
            "ASSIGNED_DEPARTMENT",
            "STATUS",
            "ACKNOWLEDGED_AT",
            "RESOLVED_AT",
        ]

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    finally:
        cursor.close()
        conn.close()


def get_department_incidents(department):
    """Return incidents routed to one department."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT
            INCIDENT_ID,
            CREATED_AT,
            UPDATED_AT,
            TITLE,
            LOCATION,
            CATEGORY,
            SUBCATEGORY,
            SEVERITY,
            REPORT_COUNT,
            SUMMARY,
            ASSIGNED_DEPARTMENT,
            STATUS,
            ACKNOWLEDGED_AT,
            RESOLVED_AT
        FROM INCIDENTS
        WHERE ASSIGNED_DEPARTMENT = %s
        ORDER BY
            CASE UPPER(SEVERITY)
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END,
            UPDATED_AT DESC
        """

        cursor.execute(
            query,
            (department,),
        )

        rows = cursor.fetchall()

        columns = [
            "INCIDENT_ID",
            "CREATED_AT",
            "UPDATED_AT",
            "TITLE",
            "LOCATION",
            "CATEGORY",
            "SUBCATEGORY",
            "SEVERITY",
            "REPORT_COUNT",
            "SUMMARY",
            "ASSIGNED_DEPARTMENT",
            "STATUS",
            "ACKNOWLEDGED_AT",
            "RESOLVED_AT",
        ]

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    finally:
        cursor.close()
        conn.close()


def update_incident_status(
    incident_id,
    new_status,
):
    """Update an incident's department-response status."""

    allowed_statuses = {
        "NEW",
        "ACKNOWLEDGED",
        "IN_PROGRESS",
        "RESOLVED",
    }

    new_status = str(
        new_status
    ).strip().upper()

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid incident status: {new_status}"
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if new_status == "ACKNOWLEDGED":
            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'ACKNOWLEDGED',
                    UPDATED_AT = CURRENT_TIMESTAMP(),
                    ACKNOWLEDGED_AT =
                        COALESCE(
                            ACKNOWLEDGED_AT,
                            CURRENT_TIMESTAMP()
                        )
                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

        elif new_status == "IN_PROGRESS":
            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'IN_PROGRESS',
                    UPDATED_AT = CURRENT_TIMESTAMP(),
                    ACKNOWLEDGED_AT =
                        COALESCE(
                            ACKNOWLEDGED_AT,
                            CURRENT_TIMESTAMP()
                        )
                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

        elif new_status == "RESOLVED":
            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'RESOLVED',
                    UPDATED_AT = CURRENT_TIMESTAMP(),
                    ACKNOWLEDGED_AT =
                        COALESCE(
                            ACKNOWLEDGED_AT,
                            CURRENT_TIMESTAMP()
                        ),
                    RESOLVED_AT = CURRENT_TIMESTAMP()
                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

        else:
            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'NEW',
                    UPDATED_AT = CURRENT_TIMESTAMP(),
                    ACKNOWLEDGED_AT = NULL,
                    RESOLVED_AT = NULL
                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

        conn.commit()
        return True

    finally:
        cursor.close()
        conn.close()


# ============================================================
# Connection test
# ============================================================

if __name__ == "__main__":
    try:
        conn = get_connection()

        print(
            "✅ Connected to Snowflake successfully!"
        )

        conn.close()

    except Exception as e:
        print(
            "❌ Snowflake connection failed:"
        )
        print(e)