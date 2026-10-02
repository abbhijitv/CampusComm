"""Campus Comm AI features, powered by Snowflake Cortex."""

import json
import os
from functools import lru_cache

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

from analytics import SEVERITY_ORDER, detect_emerging_issues


load_dotenv()


# Model choices
CLASSIFY_MODEL = "llama3.3-70b"
WRITING_MODEL = "claude-sonnet-4-5"


# Team-agreed categories and suggested subcategories.
SUBCATEGORY_EXAMPLES = {
    "Safety": [
        "Fire",
        "Battery Fire",
        "Medical",
        "Security",
    ],
    "Technology": [
        "Wi-Fi",
        "Network",
        "Classroom Technology",
    ],
    "Facilities": [
        "Electrical",
        "Plumbing",
        "HVAC",
        "Building Damage",
    ],
    "Transportation": [
        "Shuttle",
        "Parking",
        "Bike/Scooter",
    ],
    "Academic": [
        "Academic Integrity",
        "AI/Generative AI",
        "Course Issues",
        "Exams",
    ],
    "Student Services": [
        "Dining",
        "Housing",
        "Advising",
        "Financial Aid",
    ],
    "Other": [
        "Other",
    ],
}


CATEGORIES = list(SUBCATEGORY_EXAMPLES)


# Most recent reports sent to Cortex.
MAX_CONTEXT_REPORTS = 100


def classify_report(text: str) -> dict:
    """
    Classify a free-text campus report.

    Returns:
    {
        "category": "...",
        "subcategory": "...",
        "severity": "...",
        "summary": "..."
    }
    """

    subcategory_guide = "\n".join(
        f"- {category}: {', '.join(subs)}"
        for category, subs in SUBCATEGORY_EXAMPLES.items()
    )

    prompt = f"""
You classify student reports about campus problems.

Report:
\"\"\"{text}\"\"\"

Reply with ONLY a JSON object.
Do not include markdown.
Do not include explanations outside the JSON.

Required format:

{{
  "category": one of {json.dumps(CATEGORIES)},
  "subcategory": "short label",
  "severity": one of {json.dumps(SEVERITY_ORDER)},
  "summary": "one neutral sentence"
}}

Suggested subcategories:

{subcategory_guide}

CATEGORY RULES:

Safety:
Use for anything involving possible immediate danger or injury.
Examples include:
- fire
- smoke
- burning smell
- battery fire
- violence
- medical emergencies
- exposed electrical hazards
- dangerous flooding
- security threats

Technology:
Use for:
- Wi-Fi
- network outages
- classroom technology
- campus software or technology failures

Facilities:
Use for:
- HVAC
- plumbing
- electrical building problems
- elevators
- structural or building damage

Transportation:
Use for:
- parking
- shuttles
- bikes
- scooters
- transportation access

Academic:
Use for:
- courses
- exams
- grading
- academic integrity
- misuse of generative AI
- fabricated AI-generated citations
- cheating concerns

Student Services:
Use for:
- dining
- housing
- advising
- financial aid
- other student support services

Other:
Use only when none of the categories above reasonably apply.

SEVERITY RULES:

LOW:
Minor inconvenience affecting a small number of people.

MEDIUM:
Noticeable disruption affecting some students.

HIGH:
Major disruption that blocks studying, travel, services,
or access for many people.

CRITICAL:
Immediate danger to people, a serious safety emergency,
or a campus-wide critical outage.

SUMMARY RULES:

- Write one neutral sentence.
- Use only information explicitly stated in the report.
- Do not invent a cause.
- Do not invent a location if none was provided in the report text.
"""

    # Safe fallback if Cortex returns something unexpected.
    result = {
        "category": "Other",
        "subcategory": "Other",
        "severity": "MEDIUM",
        "summary": text.strip()[:200],
    }

    try:
        parsed = _parse_json(
            _complete(CLASSIFY_MODEL, prompt)
        )
    except ValueError:
        return result

    if parsed.get("category") in CATEGORIES:
        result["category"] = parsed["category"]

    severity = str(
        parsed.get("severity", "")
    ).strip().upper()

    if severity in SEVERITY_ORDER:
        result["severity"] = severity

    if parsed.get("subcategory"):
        result["subcategory"] = (
            str(parsed["subcategory"])
            .strip()[:50]
        )

    if parsed.get("summary"):
        result["summary"] = (
            str(parsed["summary"])
            .strip()
        )

    return result


def generate_briefing(
    reports_df: pd.DataFrame,
) -> str:
    """
    Write a short campus operations briefing
    from the most recent reports.
    """

    if reports_df.empty:
        return "No campus reports yet."

    issues = detect_emerging_issues(
        reports_df
    )

    if issues.empty:
        issue_lines = "None detected."

    else:
        issue_lines = "\n".join(
            (
                f"- {row.TITLE}: "
                f"{row.REPORT_COUNT} reports, "
                f"severity {row.SEVERITY}"
            )
            for row in issues.itertuples()
        )

    prompt = f"""
You are Campus Comm, an AI assistant helping campus staff
understand current campus conditions.

Emerging issues:
{issue_lines}

{_format_counts(reports_df)}

Recent reports:
{_format_reports(reports_df)}

Write a concise campus operations briefing.

RULES:

- Write 3 to 5 sentences.
- Use plain text.
- Do not use headings or bullet points.
- Lead with the most serious emerging issue.
- Mention other notable patterns.
- Use only facts contained in the reports.
- Use the exact counts provided in the counts table.
- Do not guess causes.
- Do not claim that two reports are connected unless the
  report data reasonably groups them together.
- Do not exaggerate severity.
"""

    return _complete(
        WRITING_MODEL,
        prompt,
    ).strip()


def answer_question(
    question: str,
    reports_df: pd.DataFrame,
) -> str:
    """
    Answer a natural-language question using
    only the stored campus reports.
    """

    if reports_df.empty:
        return (
            "There are no campus reports yet, "
            "so I can't answer that."
        )

    prompt = f"""
You are Campus Comm, an AI assistant that answers questions
about current campus conditions.

You MUST answer using ONLY the campus reports supplied below.

IMPORTANT CAMPUS ABBREVIATIONS:

- SDFC = Sun Devil Fitness Complex
- MU = Memorial Union
- Hayden = Hayden Library
- Noble = Noble Library

QUESTION:
{question}

EXACT REPORT COUNTS:
{_format_counts(reports_df)}

REPORTS:
{_format_reports(reports_df)}

ANSWERING RULES:

1. Answer the user's question immediately.

2. If at least one relevant report exists, clearly summarize
   what the relevant report or reports say.

3. DO NOT start with unnecessary disclaimers such as:
   - "The reports don't contain information beyond..."
   - "There is limited information..."
   - "I cannot determine..."
   - "The available reports only say..."

   when relevant reports actually exist.

4. If there is exactly one relevant report, say:
   "One recent report..." or equivalent.

5. If multiple relevant reports exist, mention the exact number
   using the provided counts table.

6. If multiple reports at the same location describe a similar
   problem, explain that they may represent an emerging issue.

7. Mention the location when relevant.

8. Mention category or severity only when it helps answer the
   question.

9. Do not guess the cause of an issue.

10. Do not invent events, reports, people, dates, or locations.

11. Only say that no information is available when ZERO reports
    are relevant to the user's question.

12. Understand common abbreviations and informal wording.
    For example, a question about "SDFC" refers to reports whose
    location is "Sun Devil Fitness Complex."

13. Keep the answer concise and useful.

14. Maximum length: 100 words.

15. Plain text only. No markdown headings.

Give the answer now.
"""

    return _complete(
        WRITING_MODEL,
        prompt,
    ).strip()


@lru_cache(maxsize=1)
def _get_connection():
    """
    Create and cache the Snowflake connection used
    for Cortex AI calls.
    """

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        client_session_keep_alive=True,
    )


def _complete(
    model: str,
    prompt: str,
) -> str:
    """
    Call Snowflake Cortex COMPLETE.
    """

    conn = _get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)
            """,
            (
                model,
                prompt,
            ),
        )

        row = cur.fetchone()

        if row is None:
            raise RuntimeError(
                "Snowflake Cortex returned no response."
            )

        return row[0]

    finally:
        cur.close()


def _parse_json(
    reply: str,
) -> dict:
    """
    Pull a JSON object from a model reply,
    ignoring accidental surrounding text.
    """

    start = reply.find("{")
    end = reply.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No JSON object in model reply."
        )

    try:
        return json.loads(
            reply[start:end + 1]
        )

    except json.JSONDecodeError as e:
        raise ValueError(
            "Invalid JSON in model reply."
        ) from e


def _recent_reports(
    reports_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize and return the newest reports
    sent to Cortex.
    """

    df = reports_df.copy()

    df.columns = [
        c.upper()
        for c in df.columns
    ]

    if df.empty:
        return df

    df["CREATED_AT"] = pd.to_datetime(
        df["CREATED_AT"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["CREATED_AT"]
    )

    return (
        df
        .sort_values(
            "CREATED_AT",
            ascending=False,
        )
        .head(MAX_CONTEXT_REPORTS)
    )


def _format_counts(
    reports_df: pd.DataFrame,
) -> str:
    """
    Calculate exact counts so the LLM does
    not need to count reports itself.
    """

    df = _recent_reports(
        reports_df
    )

    if df.empty:
        return "No report counts available."

    counts = (
        df.groupby(
            [
                df["CREATED_AT"].dt.date,
                "LOCATION",
                "SUBCATEGORY",
            ]
        )
        .size()
        .sort_index(
            ascending=False
        )
    )

    lines = []

    for (
        day,
        location,
        subcategory,
    ), n in counts.items():

        label = (
            "report"
            if n == 1
            else "reports"
        )

        lines.append(
            f"- {day} | "
            f"{location} | "
            f"{subcategory}: "
            f"{n} {label}"
        )

    return "\n".join(lines)


def _format_reports(
    reports_df: pd.DataFrame,
) -> str:
    """
    Format reports as compact model context.
    """

    df = _recent_reports(
        reports_df
    )

    if df.empty:
        return "No reports."

    lines = []

    for row in df.itertuples():

        created_at = row.CREATED_AT

        location = getattr(
            row,
            "LOCATION",
            "Unknown",
        )

        category = getattr(
            row,
            "CATEGORY",
            "Other",
        )

        subcategory = getattr(
            row,
            "SUBCATEGORY",
            "Other",
        )

        severity = getattr(
            row,
            "SEVERITY",
            "MEDIUM",
        )

        report_text = getattr(
            row,
            "REPORT_TEXT",
            "",
        )

        lines.append(
            f"- [{created_at:%Y-%m-%d %H:%M}] "
            f"{location} | "
            f"{category}/{subcategory} | "
            f"{severity} | "
            f"{report_text}"
        )

    return "\n".join(lines)