-- ============================================================
-- CAMPUS COMM
-- Snowflake Database Setup + Hackathon Demo Data
-- ============================================================


-- ============================================================
-- 1. DATABASE / SCHEMA
-- ============================================================

CREATE DATABASE IF NOT EXISTS CAMPUS_COMM_DB;

CREATE SCHEMA IF NOT EXISTS CAMPUS_COMM_DB.PUBLIC;

USE DATABASE CAMPUS_COMM_DB;
USE SCHEMA PUBLIC;


-- ============================================================
-- 2. CAMPUS REPORTS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS CAMPUS_REPORTS (
    REPORT_ID INTEGER AUTOINCREMENT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    REPORT_TEXT STRING NOT NULL,
    LOCATION STRING,
    CATEGORY STRING,
    SUBCATEGORY STRING,
    SEVERITY STRING,
    SUMMARY STRING,
    STATUS STRING DEFAULT 'ACTIVE'
);


-- ============================================================
-- 3. INCIDENTS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS INCIDENTS (
    INCIDENT_ID INTEGER AUTOINCREMENT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ,
    TITLE STRING,
    LOCATION STRING,
    CATEGORY STRING,
    SUBCATEGORY STRING,
    SEVERITY STRING,
    REPORT_COUNT INTEGER,
    SUMMARY STRING,
    STATUS STRING DEFAULT 'ACTIVE',
    ASSIGNED_DEPARTMENT STRING,
    ACKNOWLEDGED_AT TIMESTAMP_NTZ,
    RESOLVED_AT TIMESTAMP_NTZ
);

-- ============================================================
-- 4. RESET DEMO REPORTS
-- ============================================================
-- IMPORTANT:
-- This removes existing REPORT ROWS but keeps the table.
--
-- Run this when resetting the hackathon demo.
-- Do NOT run it during the live presentation unless you
-- intentionally want to reset all submitted reports.
-- ============================================================

TRUNCATE TABLE CAMPUS_REPORTS;


-- ============================================================
-- 5. SAFETY
-- Hayden Library Fire / Electric Scooter Scenario
--
-- Multiple related reports intentionally demonstrate how
-- Campus Comm identifies an emerging issue from separate
-- student observations.
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES

(
    'I smell something burning inside Hayden Library.',
    'Hayden Library',
    'Safety',
    'Fire',
    'HIGH',
    'A burning smell has been reported inside Hayden Library.'
),

(
    'There is smoke inside Hayden and people are starting to leave.',
    'Hayden Library',
    'Safety',
    'Fire',
    'HIGH',
    'Smoke and possible evacuation activity have been reported at Hayden Library.'
),

(
    'The fire alarm is going off at Hayden Library.',
    'Hayden Library',
    'Safety',
    'Fire',
    'HIGH',
    'The fire alarm has been activated at Hayden Library.'
),

(
    'I saw smoke near what looks like an electric scooter inside Hayden.',
    'Hayden Library',
    'Safety',
    'Fire',
    'CRITICAL',
    'Smoke has been reported near an electric scooter inside Hayden Library.'
),

(
    'Hayden is being evacuated and there are emergency responders outside.',
    'Hayden Library',
    'Safety',
    'Fire',
    'CRITICAL',
    'Hayden Library is being evacuated with emergency responders present.'
);


-- ============================================================
-- 6. TECHNOLOGY
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES (
    'The Wi-Fi keeps disconnecting on the second floor of Hayden Library.',
    'Hayden Library',
    'Technology',
    'Wi-Fi',
    'MEDIUM',
    'Students are experiencing Wi-Fi connectivity problems at Hayden Library.'
);


-- ============================================================
-- 7. FACILITIES
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES (
    'Several gym machines are not working properly.',
    'Sun Devil Fitness Complex',
    'Facilities',
    'Equipment',
    'MEDIUM',
    'Several gym machines are reportedly unavailable at the Sun Devil Fitness Complex.'
);


-- ============================================================
-- 8. TRANSPORTATION
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES (
    'The campus shuttle is running very late and students have been waiting.',
    'Tempe Campus',
    'Transportation',
    'Shuttle',
    'MEDIUM',
    'Students are reporting delays with the campus shuttle.'
);


-- ============================================================
-- 9. ACADEMIC
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES (
    'Students are reporting AI-generated citations in assignments that do not actually exist.',
    'Tempe Campus',
    'Academic',
    'Academic Integrity',
    'MEDIUM',
    'Reports describe potentially fabricated AI-generated citations in coursework.'
);


-- ============================================================
-- 10. STUDENT SERVICES
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES (
    'The dining hall has an unusually long wait and one of the food stations is closed.',
    'Memorial Union',
    'Student Services',
    'Dining',
    'LOW',
    'Students are reporting longer dining wait times at Memorial Union.'
);


-- ============================================================
-- 11. OTHER
-- ============================================================

INSERT INTO CAMPUS_REPORTS (
    REPORT_TEXT,
    LOCATION,
    CATEGORY,
    SUBCATEGORY,
    SEVERITY,
    SUMMARY
)
VALUES (
    'There are several unattended personal items near the student center.',
    'Memorial Union',
    'Other',
    'Lost Property',
    'LOW',
    'Several unattended personal items have been reported near Memorial Union.'
);


-- ============================================================
-- 12. VERIFY REPORTS
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
-- 13. VERIFY CATEGORY COUNTS
-- ============================================================

SELECT
    CATEGORY,
    COUNT(*) AS REPORT_COUNT
FROM CAMPUS_REPORTS
GROUP BY CATEGORY
ORDER BY REPORT_COUNT DESC, CATEGORY;


-- ============================================================
-- 14. VERIFY DASHBOARD STATISTICS
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
-- EXPECTED DEMO DATA
-- ============================================================
--
-- Safety            = 5
-- Technology        = 1
-- Facilities        = 1
-- Transportation    = 1
-- Academic          = 1
-- Student Services  = 1
-- Other             = 1
--
-- TOTAL             = 11
--
-- The five Safety reports are intentionally related:
--
--   burning smell
--        ↓
--   smoke
--        ↓
--   fire alarm
--        ↓
--   possible electric scooter involvement
--        ↓
--   evacuation / emergency response
--
-- Campus Comm should combine these into:
--
--   Hayden Library — Fire
--   CRITICAL
--   5 reports
--
-- ============================================================