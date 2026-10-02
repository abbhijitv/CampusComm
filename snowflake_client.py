"""Snowflake database helpers for Campus Comm."""

import os
from functools import lru_cache

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

    category = str(category).strip()

    return DEPARTMENT_ROUTES.get(
        category,
        "Campus Operations",
    )


# ============================================================
# Snowflake connection
# ============================================================

@lru_cache(maxsize=1)
def get_connection():
    """Reuse one Snowflake connection so Streamlit reruns stay fast."""

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        client_session_keep_alive=True,
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
        WHERE UPPER(
            COALESCE(STATUS, 'ACTIVE')
        ) = 'ACTIVE'
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


# ============================================================
# Dashboard statistics
# ============================================================

def get_dashboard_stats():
    """Return statistics used by the Streamlit dashboard."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT
            COUNT(*) AS TOTAL,

            COUNT_IF(
                CAST(CREATED_AT AS DATE)
                = CURRENT_DATE()
            ) AS TODAY,

            COUNT_IF(
                UPPER(SEVERITY)
                IN ('HIGH', 'CRITICAL')
            ) AS HIGH_SEVERITY,

            COUNT(
                DISTINCT NULLIF(
                    TRIM(LOCATION),
                    ''
                )
            ) AS LOCATIONS,

            COUNT_IF(
                UPPER(SEVERITY)
                = 'CRITICAL'
            ) AS CRITICAL,

            COUNT_IF(
                UPPER(
                    COALESCE(
                        STATUS,
                        'ACTIVE'
                    )
                ) = 'ACTIVE'
            ) AS ACTIVE

        FROM CAMPUS_REPORTS

        WHERE UPPER(
            COALESCE(
                STATUS,
                'ACTIVE'
            )
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


# ============================================================
# Incident synchronization
# ============================================================

def sync_incidents(issues_df):
    """
    Synchronize detected dashboard issues into INCIDENTS.

    Each unique incident is identified by:

        LOCATION + CATEGORY + SUBCATEGORY

    This allows multiple incidents to exist inside the same category.

    Example:

        Technology:
            Hayden Library — Wi-Fi
            Memorial Union — Security

    Both remain separate incidents and both are routed to IT Support.

    Existing incidents are updated rather than duplicated.

    Resolved incidents are reopened if a newer report arrives after
    the incident was resolved.
    """

    if (
        issues_df is None
        or issues_df.empty
    ):
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for _, issue in issues_df.iterrows():

            title = str(
                issue.get(
                    "TITLE",
                    "Campus Issue",
                )
            ).strip()

            location = str(
                issue.get(
                    "LOCATION",
                    "Unknown Location",
                )
            ).strip()

            category = str(
                issue.get(
                    "CATEGORY",
                    "Other",
                )
            ).strip()

            subcategory = str(
                issue.get(
                    "SUBCATEGORY",
                    "Other",
                )
            ).strip()

            severity = str(
                issue.get(
                    "SEVERITY",
                    "MEDIUM",
                )
            ).strip().upper()

            report_count = int(
                issue.get(
                    "REPORT_COUNT",
                    1,
                )
            )

            summary = str(
                issue.get(
                    "SUMMARY",
                    "",
                )
            ).strip()

            last_reported = issue.get(
                "LAST_REPORTED"
            )

            department = (
                get_department_for_category(
                    category
                )
            )

            # ------------------------------------------------
            # Look for the same existing incident.
            #
            # IMPORTANT:
            # Category alone is NOT enough.
            #
            # LOCATION + CATEGORY + SUBCATEGORY uniquely
            # identifies the issue cluster for this demo.
            # ------------------------------------------------
            cursor.execute(
                """
                SELECT
                    INCIDENT_ID,
                    STATUS,
                    RESOLVED_AT
                FROM INCIDENTS
                WHERE LOCATION = %s
                  AND CATEGORY = %s
                  AND COALESCE(
                      SUBCATEGORY,
                      'Other'
                  ) = %s
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

            # =================================================
            # Existing incident
            # =================================================
            if existing:

                incident_id = existing[0]

                current_status = (
                    existing[1]
                    or "NEW"
                ).upper()

                resolved_at = existing[2]

                new_status = current_status

                # ---------------------------------------------
                # Reopen a resolved incident if a new report
                # arrives after it was resolved.
                # ---------------------------------------------
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

                    if (
                        last_reported_ts
                        > resolved_ts
                    ):
                        new_status = "NEW"

                cursor.execute(
                    """
                    UPDATE INCIDENTS
                    SET
                        UPDATED_AT =
                            CURRENT_TIMESTAMP(),

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

            # =================================================
            # New incident
            # =================================================
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
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'NEW'
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


# ============================================================
# All incidents
# ============================================================

def get_incidents():
    """Return all campus incidents."""

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


# ============================================================
# Department incidents
# ============================================================

def get_department_incidents(
    department,
):
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


# ============================================================
# Department status updates
# ============================================================

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

    new_status = (
        str(new_status)
        .strip()
        .upper()
    )

    if (
        new_status
        not in allowed_statuses
    ):
        raise ValueError(
            f"Invalid incident status: {new_status}"
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # ACKNOWLEDGED
        # ----------------------------------------------------
        if (
            new_status
            == "ACKNOWLEDGED"
        ):

            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'ACKNOWLEDGED',

                    UPDATED_AT =
                        CURRENT_TIMESTAMP(),

                    ACKNOWLEDGED_AT =
                        COALESCE(
                            ACKNOWLEDGED_AT,
                            CURRENT_TIMESTAMP()
                        )

                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

        # ----------------------------------------------------
        # IN PROGRESS
        # ----------------------------------------------------
        elif (
            new_status
            == "IN_PROGRESS"
        ):

            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'IN_PROGRESS',

                    UPDATED_AT =
                        CURRENT_TIMESTAMP(),

                    ACKNOWLEDGED_AT =
                        COALESCE(
                            ACKNOWLEDGED_AT,
                            CURRENT_TIMESTAMP()
                        )

                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

        # ----------------------------------------------------
        # RESOLVED
        # ----------------------------------------------------
        elif (
            new_status
            == "RESOLVED"
        ):

            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'RESOLVED',

                    UPDATED_AT =
                        CURRENT_TIMESTAMP(),

                    ACKNOWLEDGED_AT =
                        COALESCE(
                            ACKNOWLEDGED_AT,
                            CURRENT_TIMESTAMP()
                        ),

                    RESOLVED_AT =
                        CURRENT_TIMESTAMP()

                WHERE INCIDENT_ID = %s
                """,
                (incident_id,),
            )

            # Mark the reports that belong to this incident as resolved too.
            # This keeps Students / Staff, dashboard metrics, and AI context
            # in sync with the department workflow. A later new report is
            # inserted as ACTIVE and can reopen the incident automatically.
            cursor.execute(
                """
                UPDATE CAMPUS_REPORTS
                SET STATUS = 'RESOLVED'
                WHERE UPPER(COALESCE(STATUS, 'ACTIVE')) = 'ACTIVE'
                  AND (LOCATION, CATEGORY, COALESCE(SUBCATEGORY, 'Other')) = (
                      SELECT
                          LOCATION,
                          CATEGORY,
                          COALESCE(SUBCATEGORY, 'Other')
                      FROM INCIDENTS
                      WHERE INCIDENT_ID = %s
                  )
                """,
                (incident_id,),
            )

        # ----------------------------------------------------
        # NEW / RESET
        # ----------------------------------------------------
        else:

            cursor.execute(
                """
                UPDATE INCIDENTS
                SET
                    STATUS = 'NEW',

                    UPDATED_AT =
                        CURRENT_TIMESTAMP(),

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