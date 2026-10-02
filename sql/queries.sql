-- ============================================================
-- CAMPUS COMM
-- queries.sql
--
-- Read-only queries for testing, dashboard development,
-- analytics, and demo verification.
--
-- Database creation and demo data belong in setup.sql.
-- ============================================================


USE DATABASE CAMPUS_COMM_DB;
USE SCHEMA PUBLIC;


-- ============================================================
-- 1. ALL RECENT REPORTS
-- Used by / similar to the Recent Reports section of the app
-- ============================================================

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
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 2. DASHBOARD STATISTICS
--
-- Verifies:
-- Total Reports
-- Reports Today
-- High Severity
-- Critical Reports
-- Locations
-- Active Reports
-- ============================================================

SELECT
    COUNT(*) AS TOTAL_REPORTS,

    COUNT_IF(
        CAST(CREATED_AT AS DATE) = CURRENT_DATE()
    ) AS REPORTS_TODAY,

    COUNT_IF(
        UPPER(SEVERITY) IN ('HIGH', 'CRITICAL')
    ) AS HIGH_SEVERITY,

    COUNT_IF(
        UPPER(SEVERITY) = 'CRITICAL'
    ) AS CRITICAL_REPORTS,

    COUNT(
        DISTINCT NULLIF(TRIM(LOCATION), '')
    ) AS LOCATIONS,

    COUNT_IF(
        UPPER(COALESCE(STATUS, 'ACTIVE')) = 'ACTIVE'
    ) AS ACTIVE_REPORTS

FROM CAMPUS_REPORTS;


-- ============================================================
-- 3. REPORT COUNT BY CATEGORY
-- ============================================================

SELECT
    CATEGORY,
    COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
GROUP BY CATEGORY
ORDER BY REPORT_COUNT DESC, CATEGORY;


-- ============================================================
-- 4. ALL 7 CATEGORIES INCLUDING ZERO-REPORT CATEGORIES
--
-- This is useful for verifying that the application supports:
--
-- Safety
-- Technology
-- Facilities
-- Transportation
-- Academic
-- Student Services
-- Other
-- ============================================================

WITH EXPECTED_CATEGORIES AS (
    SELECT COLUMN1 AS CATEGORY
    FROM VALUES
        ('Safety'),
        ('Technology'),
        ('Facilities'),
        ('Transportation'),
        ('Academic'),
        ('Student Services'),
        ('Other')
),

REPORT_COUNTS AS (
    SELECT
        CATEGORY,
        COUNT(*) AS REPORT_COUNT
    FROM CAMPUS_REPORTS
    GROUP BY CATEGORY
)

SELECT
    E.CATEGORY,
    COALESCE(R.REPORT_COUNT, 0) AS REPORT_COUNT
FROM EXPECTED_CATEGORIES E
LEFT JOIN REPORT_COUNTS R
    ON E.CATEGORY = R.CATEGORY
ORDER BY
    CASE E.CATEGORY
        WHEN 'Safety' THEN 1
        WHEN 'Technology' THEN 2
        WHEN 'Facilities' THEN 3
        WHEN 'Transportation' THEN 4
        WHEN 'Academic' THEN 5
        WHEN 'Student Services' THEN 6
        WHEN 'Other' THEN 7
        ELSE 8
    END;


-- ============================================================
-- 5. SAFETY REPORTS
-- ============================================================

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
WHERE CATEGORY = 'Safety'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 6. TECHNOLOGY REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE CATEGORY = 'Technology'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 7. FACILITIES REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE CATEGORY = 'Facilities'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 8. TRANSPORTATION REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE CATEGORY = 'Transportation'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 9. ACADEMIC REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE CATEGORY = 'Academic'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 10. STUDENT SERVICES REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE CATEGORY = 'Student Services'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 11. OTHER REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE CATEGORY = 'Other'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 12. HAYDEN LIBRARY REPORTS
--
-- Hayden can contain reports from multiple categories.
-- For example:
-- Safety -> Fire
-- Technology -> Wi-Fi
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE LOCATION = 'Hayden Library'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 13. HIGH + CRITICAL REPORTS
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE UPPER(SEVERITY) IN ('HIGH', 'CRITICAL')
ORDER BY
    CASE UPPER(SEVERITY)
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        ELSE 3
    END,
    CREATED_AT DESC;


-- ============================================================
-- 14. CRITICAL REPORTS ONLY
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE UPPER(SEVERITY) = 'CRITICAL'
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 15. REPORT COUNT BY LOCATION
-- ============================================================

SELECT
    LOCATION,
    COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
WHERE LOCATION IS NOT NULL
  AND TRIM(LOCATION) <> ''
GROUP BY LOCATION
ORDER BY REPORT_COUNT DESC, LOCATION;


-- ============================================================
-- 16. REPORT COUNT BY SEVERITY
-- ============================================================

SELECT
    SEVERITY,
    COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
GROUP BY SEVERITY
ORDER BY
    CASE UPPER(SEVERITY)
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END;


-- ============================================================
-- 17. REPORT COUNT BY CATEGORY + SUBCATEGORY
-- ============================================================

SELECT
    CATEGORY,
    SUBCATEGORY,
    COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
GROUP BY
    CATEGORY,
    SUBCATEGORY
ORDER BY
    REPORT_COUNT DESC,
    CATEGORY,
    SUBCATEGORY;


-- ============================================================
-- 18. POTENTIAL EMERGING ISSUES
--
-- Groups reports by:
-- Location + Category + Subcategory
--
-- Requires at least 2 reports in the same cluster.
--
-- NOTE:
-- analytics.py remains responsible for the application's
-- actual emerging-issue detection.
-- ============================================================

SELECT
    LOCATION,
    CATEGORY,
    SUBCATEGORY,

    COUNT(*) AS REPORT_COUNT,

    COUNT_IF(
        UPPER(SEVERITY) = 'CRITICAL'
    ) AS CRITICAL_REPORTS,

    COUNT_IF(
        UPPER(SEVERITY) = 'HIGH'
    ) AS HIGH_REPORTS,

    MAX(CREATED_AT) AS LATEST_REPORT

FROM CAMPUS_REPORTS

WHERE UPPER(COALESCE(STATUS, 'ACTIVE')) = 'ACTIVE'

GROUP BY
    LOCATION,
    CATEGORY,
    SUBCATEGORY

HAVING COUNT(*) >= 2

ORDER BY
    REPORT_COUNT DESC,
    LATEST_REPORT DESC;


-- ============================================================
-- 19. HAYDEN FIRE DEMO REPORTS
--
-- This should show the multiple related reports used in the
-- main Campus Comm presentation scenario.
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS
WHERE LOCATION = 'Hayden Library'
  AND CATEGORY = 'Safety'
  AND SUBCATEGORY = 'Fire'
ORDER BY CREATED_AT ASC;


-- ============================================================
-- 20. HAYDEN FIRE SUMMARY
-- ============================================================

SELECT
    LOCATION,
    CATEGORY,
    SUBCATEGORY,

    COUNT(*) AS REPORT_COUNT,

    COUNT_IF(
        UPPER(SEVERITY) = 'CRITICAL'
    ) AS CRITICAL_REPORTS,

    COUNT_IF(
        UPPER(SEVERITY) = 'HIGH'
    ) AS HIGH_REPORTS,

    MIN(CREATED_AT) AS FIRST_REPORT,
    MAX(CREATED_AT) AS LATEST_REPORT

FROM CAMPUS_REPORTS

WHERE LOCATION = 'Hayden Library'
  AND CATEGORY = 'Safety'
  AND SUBCATEGORY = 'Fire'

GROUP BY
    LOCATION,
    CATEGORY,
    SUBCATEGORY;


-- ============================================================
-- 21. TODAY'S REPORTS
-- ============================================================

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
WHERE CAST(CREATED_AT AS DATE) = CURRENT_DATE()
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 22. ACTIVE REPORTS
-- ============================================================

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
ORDER BY CREATED_AT DESC;


-- ============================================================
-- 23. MOST RECENT REPORT FROM EACH CATEGORY
--
-- This is especially useful for your presentation because
-- every category can display one representative report.
-- ============================================================

SELECT
    REPORT_ID,
    CREATED_AT,
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
FROM CAMPUS_REPORTS

QUALIFY ROW_NUMBER() OVER (
    PARTITION BY CATEGORY
    ORDER BY CREATED_AT DESC, REPORT_ID DESC
) = 1

ORDER BY
    CASE CATEGORY
        WHEN 'Safety' THEN 1
        WHEN 'Technology' THEN 2
        WHEN 'Facilities' THEN 3
        WHEN 'Transportation' THEN 4
        WHEN 'Academic' THEN 5
        WHEN 'Student Services' THEN 6
        WHEN 'Other' THEN 7
        ELSE 8
    END;


-- ============================================================
-- 24. DATABASE HEALTH CHECK
--
-- Quick check before your presentation.
-- ============================================================

SELECT
    COUNT(*) AS TOTAL_REPORTS,

    COUNT(DISTINCT CATEGORY) AS CATEGORY_COUNT,

    COUNT(
        DISTINCT NULLIF(TRIM(LOCATION), '')
    ) AS LOCATION_COUNT,

    COUNT_IF(
        UPPER(SEVERITY) = 'CRITICAL'
    ) AS CRITICAL_REPORTS,

    COUNT_IF(
        UPPER(SEVERITY) = 'HIGH'
    ) AS HIGH_REPORTS,

    MAX(CREATED_AT) AS LATEST_REPORT

FROM CAMPUS_REPORTS;


-- ============================================================
-- 25. DEMO READINESS CHECK
--
-- Checks whether all 7 required categories have at least
-- one report.
--
-- Expected result with the clean setup.sql:
--
-- MISSING_CATEGORIES
-- 0
-- ============================================================

WITH EXPECTED_CATEGORIES AS (
    SELECT COLUMN1 AS CATEGORY
    FROM VALUES
        ('Safety'),
        ('Technology'),
        ('Facilities'),
        ('Transportation'),
        ('Academic'),
        ('Student Services'),
        ('Other')
),

EXISTING_CATEGORIES AS (
    SELECT DISTINCT CATEGORY
    FROM CAMPUS_REPORTS
)

SELECT
    COUNT_IF(X.CATEGORY IS NULL) AS MISSING_CATEGORIES
FROM EXPECTED_CATEGORIES E
LEFT JOIN EXISTING_CATEGORIES X
    ON E.CATEGORY = X.CATEGORY;


-- ============================================================
-- 26. FINAL DEMO OVERVIEW
--
-- A compact overview of the data currently in Campus Comm.
-- ============================================================

SELECT
    CATEGORY,
    COUNT(*) AS REPORT_COUNT,
    COUNT(DISTINCT LOCATION) AS LOCATIONS,
    COUNT_IF(UPPER(SEVERITY) = 'CRITICAL') AS CRITICAL,
    COUNT_IF(UPPER(SEVERITY) = 'HIGH') AS HIGH,
    COUNT_IF(UPPER(SEVERITY) = 'MEDIUM') AS MEDIUM,
    COUNT_IF(UPPER(SEVERITY) = 'LOW') AS LOW
FROM CAMPUS_REPORTS
GROUP BY CATEGORY
ORDER BY
    CASE CATEGORY
        WHEN 'Safety' THEN 1
        WHEN 'Technology' THEN 2
        WHEN 'Facilities' THEN 3
        WHEN 'Transportation' THEN 4
        WHEN 'Academic' THEN 5
        WHEN 'Student Services' THEN 6
        WHEN 'Other' THEN 7
        ELSE 8
    END;