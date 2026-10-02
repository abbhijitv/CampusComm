"""Snowflake database helpers for Campus Comm."""

import os

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv


load_dotenv()


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


def save_report(
    report_text,
    location,
    category,
    subcategory,
    severity,
    summary,
):
    """
    Save one AI-classified campus report to Snowflake.

    Returns True when the insert succeeds.
    """

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

        return True

    finally:
        cursor.close()
        conn.close()


def get_recent_reports(limit=100):
    """
    Return recent reports as a pandas DataFrame.

    The default is 100 so the AI and dashboard have enough recent
    context while still keeping queries small.
    """

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


if __name__ == "__main__":
    try:
        conn = get_connection()

        print("✅ Connected to Snowflake successfully!")

        conn.close()

    except Exception as e:
        print("❌ Snowflake connection failed:")
        print(e)