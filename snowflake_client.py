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
    summary
):
    """Save one analyzed campus report to Snowflake."""

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


def get_recent_reports(limit=50):
    """Return recent reports as a pandas DataFrame."""

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
        ORDER BY CREATED_AT DESC
        LIMIT %s
        """

        cursor.execute(query, (limit,))
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

        return pd.DataFrame(rows, columns=columns)

    finally:
        cursor.close()
        conn.close()


def get_dashboard_stats():
    """Return statistics needed by the Streamlit dashboard."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT
            COUNT(*) AS TOTAL,
            COUNT_IF(CAST(CREATED_AT AS DATE) = CURRENT_DATE()) AS TODAY,
            COUNT_IF(SEVERITY = 'HIGH') AS HIGH,
            COUNT_IF(SEVERITY = 'CRITICAL') AS CRITICAL,
            COUNT_IF(STATUS = 'ACTIVE') AS ACTIVE
        FROM CAMPUS_REPORTS
        """

        cursor.execute(query)
        row = cursor.fetchone()

        return {
            "total": row[0],
            "today": row[1],
            "high": row[2],
            "critical": row[3],
            "active": row[4],
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