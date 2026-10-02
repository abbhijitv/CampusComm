-- Campus Comm analytics queries
-- Run in CAMPUS_COMM_DB.PUBLIC. Thresholds match analytics.py:
-- 3+ reports, same location + category, within the last 24 hours.

USE DATABASE CAMPUS_COMM_DB;
USE SCHEMA PUBLIC;


-- 1. Emerging issues
-- Uses the real clock. To test with demo data, replace CURRENT_TIMESTAMP()
-- with (SELECT MAX(CREATED_AT) FROM CAMPUS_REPORTS).
WITH recent AS (
    SELECT *
    FROM CAMPUS_REPORTS
    WHERE CREATED_AT >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
)
SELECT
    LOCATION || ' ' || MODE(SUBCATEGORY) || ' Problems' AS TITLE,
    LOCATION,
    CATEGORY,
    MODE(SUBCATEGORY) AS SUBCATEGORY,
    CASE MAX(CASE SEVERITY
                 WHEN 'LOW' THEN 1 WHEN 'MEDIUM' THEN 2
                 WHEN 'HIGH' THEN 3 WHEN 'CRITICAL' THEN 4 END)
        WHEN 1 THEN 'LOW' WHEN 2 THEN 'MEDIUM'
        WHEN 3 THEN 'HIGH' WHEN 4 THEN 'CRITICAL'
    END AS SEVERITY,
    COUNT(*) AS REPORT_COUNT,
    MIN(CREATED_AT) AS FIRST_REPORTED,
    MAX(CREATED_AT) AS LAST_REPORTED
FROM recent
GROUP BY LOCATION, CATEGORY
HAVING COUNT(*) >= 3
ORDER BY REPORT_COUNT DESC, LAST_REPORTED DESC;


-- 2. Dashboard headline numbers
SELECT
    COUNT(*) AS TOTAL_REPORTS,
    COUNT_IF(CREATED_AT >= DATEADD(hour, -24, CURRENT_TIMESTAMP())) AS LAST_24H,
    COUNT_IF(STATUS = 'Open') AS OPEN_REPORTS,
    COUNT_IF(SEVERITY IN ('HIGH', 'CRITICAL') AND STATUS = 'Open') AS OPEN_HIGH_SEVERITY
FROM CAMPUS_REPORTS;


-- 3. Reports by category (last 7 days)
SELECT CATEGORY, COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
WHERE CREATED_AT >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY CATEGORY
ORDER BY REPORT_COUNT DESC;


-- 4. Busiest locations (last 7 days)
SELECT LOCATION, COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
WHERE CREATED_AT >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY LOCATION
ORDER BY REPORT_COUNT DESC
LIMIT 10;


-- 5. Reports per hour (last 24 hours), for a trend chart
SELECT DATE_TRUNC('hour', CREATED_AT) AS HOUR, COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
WHERE CREATED_AT >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
GROUP BY HOUR
ORDER BY HOUR;


-- 6. Classify a report directly in SQL (same idea as ai.classify_report)
SELECT AI_CLASSIFY(
    'Wi-Fi keeps disconnecting on the second floor of Hayden.',
    ['Safety', 'Technology', 'Facilities', 'Transportation',
     'Academic', 'Student Services', 'Other']
):labels[0]::STRING AS CATEGORY;
