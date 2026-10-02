"""Campus Comm AI features, powered by Snowflake Cortex."""

import json
import os
from functools import lru_cache

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

from analytics import SEVERITY_ORDER, detect_emerging_issues

load_dotenv()

# Model choices checked against this account (Oct 2026). mistral-large2,
# mistral-large, claude-4-sonnet and openai-gpt-4.1 are retired.
CLASSIFY_MODEL = "llama3.3-70b"       # fast + cheap, runs on every report
WRITING_MODEL = "claude-sonnet-4-5"   # better writing for briefing and Q&A

# Team-agreed categories, with suggested (not exhaustive) subcategories.
SUBCATEGORY_EXAMPLES = {
    "Safety": ["Fire", "Battery Fire", "Medical", "Security"],
    "Technology": ["Wi-Fi", "Network", "Classroom Technology"],
    "Facilities": ["Electrical", "Plumbing", "HVAC", "Building Damage"],
    "Transportation": ["Shuttle", "Parking", "Bike/Scooter"],
    "Academic": ["Academic Integrity", "AI/Generative AI", "Course Issues", "Exams"],
    "Student Services": ["Dining", "Housing", "Advising", "Financial Aid"],
    "Other": ["Other"],
}
CATEGORIES = list(SUBCATEGORY_EXAMPLES)

# Most recent reports sent to the model as context for briefing and Q&A.
MAX_CONTEXT_REPORTS = 100


def classify_report(text: str) -> dict:
    """Classify a free-text report.

    Returns {"category", "subcategory", "severity", "summary"}. If the model's
    reply can't be parsed, falls back to safe defaults instead of failing.
    """
    subcategory_guide = "\n".join(
        f"- {category}: {', '.join(subs)}" for category, subs in SUBCATEGORY_EXAMPLES.items()
    )
    prompt = f"""You classify student reports about campus problems.

Report: \"\"\"{text}\"\"\"

Reply with ONLY a JSON object, no other text:
{{
  "category": one of {json.dumps(CATEGORIES)},
  "subcategory": a short label of 1-3 words,
  "severity": one of {json.dumps(SEVERITY_ORDER)},
  "summary": one neutral sentence describing the problem and where it is,
             using only details stated in the report
}}

Suggested subcategories per category (prefer these; use another short label
only if none fit):
{subcategory_guide}

Use category "Safety" for anything that could hurt someone (gas smell, fire,
smoke, exposed wires, flooding, violence, unsafe crossings), even inside a building.
Use "Academic" for courses, exams, grading and academic integrity, including
misuse of AI tools such as fabricated AI-generated citations.

Severity guide: LOW = minor inconvenience; MEDIUM = disrupts some people;
HIGH = blocks studying, travel or access for many people; CRITICAL = immediate
danger to people or a campus-wide outage."""

    result = {
        "category": "Other",
        "subcategory": "Other",
        "severity": "MEDIUM",
        "summary": text.strip()[:200],
    }
    try:
        parsed = _parse_json(_complete(CLASSIFY_MODEL, prompt))
    except ValueError:
        return result

    if parsed.get("category") in CATEGORIES:
        result["category"] = parsed["category"]
    severity = str(parsed.get("severity", "")).strip().upper()
    if severity in SEVERITY_ORDER:
        result["severity"] = severity
    if parsed.get("subcategory"):
        result["subcategory"] = str(parsed["subcategory"]).strip()[:50]
    if parsed.get("summary"):
        result["summary"] = str(parsed["summary"]).strip()
    return result


def generate_briefing(reports_df: pd.DataFrame) -> str:
    """Write a short campus operations briefing from recent reports."""
    if reports_df.empty:
        return "No campus reports yet."

    issues = detect_emerging_issues(reports_df)
    if issues.empty:
        issue_lines = "None detected."
    else:
        issue_lines = "\n".join(
            f"- {row.TITLE}: {row.REPORT_COUNT} reports, severity {row.SEVERITY}"
            for row in issues.itertuples()
        )

    prompt = f"""You are writing a short operations briefing for campus staff.

Emerging issues (several related reports at one location):
{issue_lines}

{_format_counts(reports_df)}

Recent reports:
{_format_reports(reports_df)}

Write 3-5 sentences of plain text (no headings, no bullet points). Lead with the
most serious emerging issue, mention other notable patterns, and note which
areas are quiet. Only use facts from the reports above, take numbers from the
counts table, and do not guess at causes or connections between issues."""

    return _complete(WRITING_MODEL, prompt).strip()


def answer_question(question: str, reports_df: pd.DataFrame) -> str:
    """Answer a natural-language question using only the stored reports."""
    if reports_df.empty:
        return "There are no campus reports yet, so I can't answer that."

    prompt = f"""You answer questions about campus issues using ONLY the student
reports below. If the reports don't contain the answer, say so plainly.
Mention how many reports support your answer and when they came in, taking
numbers from the counts table rather than counting yourself. Do not guess at
causes. Keep the answer under 120 words, plain text.

{_format_counts(reports_df)}

Reports:
{_format_reports(reports_df)}

Question: {question}"""

    return _complete(WRITING_MODEL, prompt).strip()


@lru_cache(maxsize=1)
def _get_connection():
    # TODO: switch to Person 1's connection helper in snowflake_client.py once it exists.
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        client_session_keep_alive=True,
    )


def _complete(model: str, prompt: str) -> str:
    cur = _get_connection().cursor()
    try:
        cur.execute("SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)", (model, prompt))
        return cur.fetchone()[0]
    finally:
        cur.close()


def _parse_json(reply: str) -> dict:
    """Pull the JSON object out of a model reply, ignoring any extra text."""
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model reply")
    try:
        return json.loads(reply[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError("invalid JSON in model reply") from e


def _recent_reports(reports_df: pd.DataFrame) -> pd.DataFrame:
    """The reports sent to the model: newest first, capped at MAX_CONTEXT_REPORTS."""
    df = reports_df.copy()
    df.columns = [c.upper() for c in df.columns]
    df["CREATED_AT"] = pd.to_datetime(df["CREATED_AT"])
    return df.sort_values("CREATED_AT", ascending=False).head(MAX_CONTEXT_REPORTS)


def _format_counts(reports_df: pd.DataFrame) -> str:
    """Exact report counts per day, location and subcategory (models miscount)."""
    df = _recent_reports(reports_df)
    counts = (
        df.groupby([df["CREATED_AT"].dt.date, "LOCATION", "SUBCATEGORY"])
        .size()
        .sort_index(ascending=False)
    )
    lines = [
        f"- {day} | {location} | {subcategory}: {n} report{'s' if n > 1 else ''}"
        for (day, location, subcategory), n in counts.items()
    ]
    return "Report counts (exact):\n" + "\n".join(lines)


def _format_reports(reports_df: pd.DataFrame) -> str:
    """One line per report, newest first, for use as model context."""
    df = _recent_reports(reports_df)
    return "\n".join(
        f"- [{row.CREATED_AT:%Y-%m-%d %H:%M}] {row.LOCATION} | "
        f"{row.CATEGORY}/{row.SUBCATEGORY} | {row.SEVERITY} | {row.REPORT_TEXT}"
        for row in df.itertuples()
    )
