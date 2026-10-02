import html
import importlib
from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Campus Comm",
    page_icon="📢",
    layout="wide",
)


# ============================================================
# Dynamic teammate function loading
# ============================================================

def load_function(module_name, function_name):
    """Return a teammate's function, or None if it isn't available."""
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None

    return getattr(module, function_name, None)


# Person 1 — Snowflake
save_report = load_function("snowflake_client", "save_report")
get_recent_reports = load_function("snowflake_client", "get_recent_reports")
get_dashboard_stats = load_function("snowflake_client", "get_dashboard_stats")
sync_incidents = load_function("snowflake_client", "sync_incidents")
get_incidents = load_function("snowflake_client", "get_incidents")
get_department_incidents = load_function(
    "snowflake_client",
    "get_department_incidents",
)
update_incident_status = load_function(
    "snowflake_client",
    "update_incident_status",
)

# Person 2 — AI
classify_report = load_function("ai", "classify_report")
generate_briefing = load_function("ai", "generate_briefing")
answer_question = load_function("ai", "answer_question")

# Person 2 — Analytics
detect_emerging_issues = load_function(
    "analytics",
    "detect_emerging_issues",
)


# ============================================================
# Configuration
# ============================================================

LOCATIONS = [
    "Hayden Library",
    "Noble Library",
    "Memorial Union",
    "Apache Parking Garage",
    "Student Pavilion",
    "Sun Devil Fitness Complex",
    "Residence Halls",
    "Other",
]

CATEGORIES = [
    "Safety",
    "Technology",
    "Facilities",
    "Transportation",
    "Academic",
    "Student Services",
    "Other",
]

CATEGORY_ICONS = {
    "Safety": "🛡️",
    "Technology": "💻",
    "Facilities": "🏢",
    "Transportation": "🚌",
    "Academic": "📚",
    "Student Services": "🤝",
    "Other": "📌",
}

DEPARTMENTS = [
    "Campus Safety",
    "IT Support",
    "Facilities Management",
    "Parking & Transit",
    "Academic Affairs",
    "Student Services",
    "Campus Operations",
]

CATEGORY_DEPARTMENTS = {
    "Safety": "Campus Safety",
    "Technology": "IT Support",
    "Facilities": "Facilities Management",
    "Transportation": "Parking & Transit",
    "Academic": "Academic Affairs",
    "Student Services": "Student Services",
    "Other": "Campus Operations",
}

SEVERITY_ORDER = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
]

SEVERITY_COLORS = {
    "CRITICAL": "red",
    "HIGH": "orange",
    "MEDIUM": "yellow",
    "LOW": "green",
}

SEVERITY_DOTS = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

STATUS_LABELS = {
    "NEW": "🔴 New",
    "ACKNOWLEDGED": "🟡 Acknowledged",
    "IN_PROGRESS": "🔵 In Progress",
    "RESOLVED": "🟢 Resolved",
}

SUGGESTED_QUESTIONS = [
    "What's happening at Hayden Library?",
    "Are there any safety concerns right now?",
    "What should IT Support prioritize?",
]


# ============================================================
# Styling
# ============================================================

st.markdown(
    """
<style>
.block-container {
    padding-top: 2.5rem;
    max-width: 1280px;
}

/* Header */

.cc-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: .25rem;
}

.cc-logo {
    width: 58px;
    height: 58px;
    border-radius: 16px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.9rem;
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    box-shadow: 0 6px 20px rgba(99, 102, 241, .35);
}

.cc-title {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.02em;
}

.cc-sub {
    font-size: 1.1rem;
    opacity: .7;
    margin-top: .3rem;
}

.cc-live {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    margin-left: auto;
    font-size: .95rem;
    font-weight: 500;
    padding: .4rem .9rem;
    border-radius: 999px;
    border: 1px solid rgba(34, 197, 94, .35);
    background: rgba(34, 197, 94, .10);
    white-space: nowrap;
}

.cc-live i {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #22C55E;
    display: inline-block;
}

/* Tabs */

[data-testid="stTab"] {
    padding: .6rem 1.2rem .6rem 0;
}

[data-testid="stTab"] p,
[data-testid="stTab"] [data-testid="stMarkdownContainer"] {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
}

[data-testid="stPills"] button p,
[data-testid="stButtonGroup"] button p {
    font-size: 1rem !important;
}

/* Metric tiles */

[data-testid="stMetric"] {
    background: var(--cc-card, rgba(128, 128, 128, .06));
    border: 1px solid rgba(128, 128, 128, .2);
    border-radius: 14px;
    padding: 1rem 1.2rem;
}

[data-testid="stMetricLabel"] p {
    font-size: 1rem !important;
    font-weight: 500;
    opacity: .75;
}

/* Critical alert */

.cc-alert {
    display: flex;
    gap: .9rem;
    align-items: center;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin: .4rem 0 1.1rem;
    border: 1px solid rgba(239, 68, 68, .35);
    border-left: 6px solid #EF4444;
    background: rgba(239, 68, 68, .08);
    font-size: 1.08rem;
}

.cc-alert-icon {
    font-size: 1.6rem;
    flex-shrink: 0;
}

.cc-alert-tag {
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .06em;
    color: #EF4444;
    margin-bottom: .1rem;
}

.cc-section-note {
    opacity: .65;
    font-size: 1.02rem;
    margin-top: -.5rem;
    margin-bottom: 1rem;
}

/* Issue cards */

div[class*="st-key-card-CRITICAL"] {
    border-left: 5px solid #EF4444 !important;
}

div[class*="st-key-card-HIGH"] {
    border-left: 5px solid #F97316 !important;
}

div[class*="st-key-card-MEDIUM"] {
    border-left: 5px solid #EAB308 !important;
}

div[class*="st-key-card-LOW"] {
    border-left: 5px solid #22C55E !important;
}

[data-testid="stMarkdownContainer"] span[class*="badge"] {
    font-size: .9rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# General helpers
# ============================================================

def waiting_for(*names):
    missing = [
        name
        for name, fn in names
        if fn is None
    ]

    if missing:
        st.info(
            "Waiting for: "
            + ", ".join(
                f"`{name}`"
                for name in missing
            )
        )
        return True

    return False


def md_safe(text):
    """Prevent $ signs in AI output from rendering as math."""
    return str(text).replace("$", "\\$")


def norm_severity(severity):
    return str(severity or "").strip().upper()


def severity_badge(severity):
    sev = norm_severity(severity)

    color = SEVERITY_COLORS.get(
        sev,
        "gray",
    )

    dot = SEVERITY_DOTS.get(
        sev,
        "⚪",
    )

    return (
        f":{color}-badge["
        f"{dot} {sev or 'UNKNOWN'}]"
    )


def plural(n, word):
    return (
        f"{n} "
        f"{word}"
        f"{'' if str(n) == '1' else 's'}"
    )


def format_time(value):
    try:
        ts = pd.Timestamp(value)

        # Cross-platform formatting: avoids %-d / %-I issues on Windows.
        month = ts.strftime("%b")
        day = ts.day
        hour = ts.strftime("%I").lstrip("0") or "0"
        minute = ts.strftime("%M")
        am_pm = ts.strftime("%p")

        return f"{month} {day}, {hour}:{minute} {am_pm}"

    except Exception:
        return str(value)


def current_time_string():
    now = datetime.now()
    hour = now.strftime("%I").lstrip("0") or "0"
    return f"{hour}:{now.strftime('%M %p')}"


def filter_by_category(df, category):
    if (
        df is None
        or category == "All"
        or "CATEGORY" not in df.columns
    ):
        return df

    return df[
        df["CATEGORY"] == category
    ]


def sort_by_severity(df):
    if (
        df is None
        or df.empty
        or "SEVERITY" not in df.columns
    ):
        return df

    rank = df["SEVERITY"].map(
        lambda s: (
            SEVERITY_ORDER.index(norm_severity(s))
            if norm_severity(s) in SEVERITY_ORDER
            else len(SEVERITY_ORDER)
        )
    )

    if "REPORT_COUNT" in df.columns:
        count = pd.to_numeric(
            df["REPORT_COUNT"],
            errors="coerce",
        ).fillna(0)
    else:
        count = 0

    return (
        df.assign(
            _rank=rank,
            _count=count,
        )
        .sort_values(
            ["_rank", "_count"],
            ascending=[True, False],
        )
        .drop(
            columns=["_rank", "_count"]
        )
    )


def related_reports(issue, reports_df):
    required = {
        "LOCATION",
        "CATEGORY",
    }

    if (
        reports_df is None
        or reports_df.empty
        or not required.issubset(reports_df.columns)
    ):
        return pd.DataFrame()

    related = reports_df[
        (reports_df["LOCATION"] == issue.get("LOCATION"))
        & (reports_df["CATEGORY"] == issue.get("CATEGORY"))
    ]

    subcategory = issue.get("SUBCATEGORY")

    if (
        subcategory
        and "SUBCATEGORY" in related.columns
    ):
        same_sub = related[
            related["SUBCATEGORY"] == subcategory
        ]

        if not same_sub.empty:
            related = same_sub

    if "CREATED_AT" in related.columns:
        related = related.sort_values(
            "CREATED_AT",
            ascending=False,
        )

    return related


# ============================================================
# Cached Snowflake reads
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_reports():
    """
    Load reports from Snowflake.

    Cached so category/filter interactions do not reconnect
    to Snowflake every time Streamlit reruns.
    """
    if get_recent_reports is None:
        return pd.DataFrame()

    result = get_recent_reports(limit=200)

    if result is None:
        return pd.DataFrame()

    return result


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_stats():
    """Load dashboard statistics."""
    if get_dashboard_stats is None:
        return {}

    result = get_dashboard_stats()
    return result or {}


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_department_incidents(department):
    """
    Load incidents for one department.

    Department is part of the cache key.
    """
    if get_department_incidents is None:
        return pd.DataFrame()

    result = get_department_incidents(department)

    if result is None:
        return pd.DataFrame()

    return result


# ============================================================
# Cache invalidation
# ============================================================

def refresh_report_data():
    load_reports.clear()
    load_stats.clear()


def refresh_incident_data():
    load_department_incidents.clear()


def refresh_all_data():
    refresh_report_data()
    refresh_incident_data()

    st.session_state.pop(
        "synced_signature",
        None,
    )


# ============================================================
# Incident synchronization
# ============================================================

def get_current_issues(reports_df):
    """
    Detect current issues locally from the reports DataFrame.
    """
    if (
        reports_df is None
        or detect_emerging_issues is None
    ):
        return None

    return detect_emerging_issues(reports_df)


def issue_signature(issues_df):
    """
    Produce a stable signature representing current issues.
    """
    if (
        issues_df is None
        or issues_df.empty
    ):
        return None

    signature_columns = [
        column
        for column in [
            "TITLE",
            "LOCATION",
            "CATEGORY",
            "SUBCATEGORY",
            "SEVERITY",
            "REPORT_COUNT",
            "SUMMARY",
            "LAST_REPORTED",
        ]
        if column in issues_df.columns
    ]

    if not signature_columns:
        return None

    signature_df = (
        issues_df[signature_columns]
        .copy()
        .astype(str)
        .sort_values(signature_columns)
        .reset_index(drop=True)
    )

    return int(
        pd.util.hash_pandas_object(
            signature_df,
            index=False,
        ).sum()
    )


def synchronize_if_needed(issues_df):
    """
    Synchronize issues into INCIDENTS only when issue data changes.
    """
    if (
        sync_incidents is None
        or issues_df is None
        or issues_df.empty
    ):
        return

    signature = issue_signature(issues_df)

    if signature is None:
        return

    previous_signature = st.session_state.get(
        "synced_signature"
    )

    if signature == previous_signature:
        return

    sync_incidents(issues_df)

    st.session_state[
        "synced_signature"
    ] = signature

    refresh_incident_data()


# ============================================================
# AI Q&A helper
# ============================================================

def ask(question, reports_df):
    if answer_question is None:
        st.info("Waiting for: `answer_question`")
        return

    try:
        with st.spinner("Thinking..."):
            answer = answer_question(
                question,
                reports_df,
            )

        st.session_state["qa"] = (
            question,
            answer,
        )

    except Exception as e:
        st.error(
            f"Could not answer: {e}"
        )


# ============================================================
# Load dashboard data
# ============================================================

reports_df = None
current_issues = None

if get_recent_reports is not None:
    try:
        reports_df = load_reports()

    except Exception as e:
        st.error(
            f"Could not load reports: {e}"
        )


if reports_df is not None:
    try:
        current_issues = get_current_issues(
            reports_df
        )

        current_issues = sort_by_severity(
            current_issues
        )

        synchronize_if_needed(
            current_issues
        )

    except Exception as e:
        st.warning(
            "Reports loaded, but incident routing "
            f"could not be synchronized: {e}"
        )


# ============================================================
# Header
# ============================================================

hero_col, refresh_col = st.columns(
    [14, 1],
    vertical_alignment="center",
)

with hero_col:
    header_html = (
        '<div class="cc-header">'
        '<div class="cc-logo">📢</div>'
        '<div>'
        '<div class="cc-title">Campus Comm</div>'
        '<div class="cc-sub">'
        "Know what's happening on campus, "
        "before it becomes a bigger problem."
        "</div>"
        "</div>"
        '<div class="cc-live">'
        "<i></i>"
        f"Live · {current_time_string()}"
        "</div>"
        "</div>"
    )

    st.markdown(
        header_html,
        unsafe_allow_html=True,
    )


with refresh_col:
    if st.button(
        "🔄",
        help="Refresh data",
    ):
        refresh_all_data()
        st.rerun()


campus_tab, department_tab = st.tabs(
    [
        "📊 Campus Pulse",
        "🏢 Department Operations",
    ]
)


# ============================================================
# CAMPUS PULSE TAB
# ============================================================

with campus_tab:

    # ========================================================
    # Critical alert banner
    # ========================================================

    if (
        current_issues is not None
        and not current_issues.empty
        and "SEVERITY" in current_issues.columns
    ):
        critical = current_issues[
            current_issues["SEVERITY"].map(
                norm_severity
            ) == "CRITICAL"
        ]

        for _, issue in critical.iterrows():

            title = html.escape(
                str(
                    issue.get(
                        "TITLE",
                        "Campus issue",
                    )
                )
            )

            location = html.escape(
                str(
                    issue.get(
                        "LOCATION",
                        "",
                    )
                )
            )

            category = issue.get(
                "CATEGORY"
            )

            department = CATEGORY_DEPARTMENTS.get(
                category,
                "Campus Operations",
            )

            raw_count = issue.get(
                "REPORT_COUNT",
                0,
            )

            try:
                report_count = int(raw_count)
            except (TypeError, ValueError):
                report_count = raw_count

            # IMPORTANT:
            # Build HTML without indentation so Streamlit does not
            # interpret the HTML as a Markdown code block.
            alert_html = (
                '<div class="cc-alert">'
                '<div class="cc-alert-icon">🚨</div>'
                '<div>'
                '<div class="cc-alert-tag">CRITICAL ALERT</div>'
                f"<b>{title}</b> — "
                f"{report_count} reports at {location}. "
                f"Routed to {html.escape(str(department))}."
                "</div>"
                "</div>"
            )

            st.markdown(
                alert_html,
                unsafe_allow_html=True,
            )

    # ========================================================
    # Metrics
    # ========================================================

    if not waiting_for(
        (
            "get_dashboard_stats",
            get_dashboard_stats,
        )
    ):
        try:
            stats = load_stats()

            c1, c2, c3, c4, c5 = st.columns(5)

            c1.metric(
                "📨 Active Reports",
                stats.get("total", "–"),
            )

            c2.metric(
                "📅 Today",
                stats.get("today", "–"),
            )

            c3.metric(
                "🚨 Emerging Issues",
                (
                    0
                    if current_issues is None
                    else len(current_issues)
                ),
            )

            c4.metric(
                "🔴 Critical Reports",
                stats.get("critical", "–"),
            )

            c5.metric(
                "📍 Locations",
                stats.get("locations", "–"),
            )

        except Exception as e:
            st.error(
                f"Could not load stats: {e}"
            )

    st.write("")

    left, right = st.columns(
        [1, 1.2],
        gap="large",
    )

    # ========================================================
    # Report form
    # ========================================================

    with left:

        with st.container(border=True):

            st.subheader(
                "📢 Report a Campus Issue"
            )

            st.caption(
                "Describe the problem and where it is. "
                "Campus Comm classifies and routes it "
                "automatically."
            )

            with st.form(
                "report_form",
                clear_on_submit=True,
                border=False,
            ):

                report_text = st.text_area(
                    "What's going on?",
                    placeholder=(
                        "e.g. I can smell smoke "
                        "inside Hayden Library."
                    ),
                    height=110,
                )

                location = st.selectbox(
                    "📍 Location",
                    LOCATIONS,
                )

                other_location = st.text_input(
                    "If Other, where?",
                    placeholder="Building or area",
                )

                submitted = st.form_submit_button(
                    "Submit Report",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:

                final_location = (
                    other_location.strip()
                    if location == "Other"
                    else location
                )

                if not report_text.strip():
                    st.warning(
                        "Please describe the issue."
                    )

                elif not final_location:
                    st.warning(
                        "Please enter a location."
                    )

                elif not waiting_for(
                    (
                        "classify_report",
                        classify_report,
                    ),
                    (
                        "save_report",
                        save_report,
                    ),
                ):
                    try:

                        with st.spinner(
                            "🤖 Analyzing and routing "
                            "your report..."
                        ):
                            result = classify_report(
                                report_text
                            )

                            save_report(
                                report_text,
                                final_location,
                                result["category"],
                                result["subcategory"],
                                result["severity"],
                                result["summary"],
                            )

                        st.session_state[
                            "last_submission"
                        ] = {
                            **result,
                            "location": final_location,
                            "department": (
                                CATEGORY_DEPARTMENTS.get(
                                    result["category"],
                                    "Campus Operations",
                                )
                            ),
                        }

                        refresh_report_data()
                        refresh_incident_data()

                        st.session_state.pop(
                            "synced_signature",
                            None,
                        )

                        st.rerun()

                    except Exception as e:
                        st.error(
                            "Could not submit "
                            f"report: {e}"
                        )

            if (
                "last_submission"
                in st.session_state
            ):
                result = st.session_state.pop(
                    "last_submission"
                )

                st.success(
                    "✅ Report submitted and routed. "
                    "Thank you!"
                )

                with st.container(border=True):

                    st.markdown(
                        f"{severity_badge(result['severity'])} "
                        f":gray-badge["
                        f"{CATEGORY_ICONS.get(result['category'], '📌')} "
                        f"{result['category']} / "
                        f"{result['subcategory']}]"
                    )

                    st.markdown(
                        md_safe(
                            result["summary"]
                        )
                    )

                    st.caption(
                        f"📍 {result['location']} "
                        f"· 📨 Routed to "
                        f"**{result['department']}**"
                    )

                st.caption(
                    "For immediate emergencies, "
                    "contact emergency services."
                )

    # ========================================================
    # AI briefing + Q&A
    # ========================================================

    with right:

        with st.container(border=True):

            head, btn = st.columns(
                [3, 1.3],
                vertical_alignment="center",
            )

            head.subheader(
                "✨ AI Campus Briefing"
            )

            if (
                not waiting_for(
                    (
                        "generate_briefing",
                        generate_briefing,
                    ),
                    (
                        "get_recent_reports",
                        get_recent_reports,
                    ),
                )
                and reports_df is not None
            ):

                if btn.button(
                    "Generate",
                    key="generate_briefing",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        with st.spinner(
                            "Writing campus briefing..."
                        ):
                            briefing = generate_briefing(
                                reports_df
                            )

                        st.session_state[
                            "briefing"
                        ] = (
                            briefing,
                            current_time_string(),
                        )

                    except Exception as e:
                        st.error(
                            "Could not generate "
                            f"briefing: {e}"
                        )

                if (
                    "briefing"
                    in st.session_state
                ):
                    text, generated_at = (
                        st.session_state[
                            "briefing"
                        ]
                    )

                    st.markdown(
                        md_safe(text)
                    )

                    st.caption(
                        "Generated at "
                        f"{generated_at} by "
                        "Snowflake Cortex AI"
                    )

                else:
                    st.caption(
                        "Get a short AI summary "
                        "of everything happening "
                        "on campus right now."
                    )

        with st.container(border=True):

            st.subheader(
                "💬 Ask Campus Comm"
            )

            if (
                not waiting_for(
                    (
                        "answer_question",
                        answer_question,
                    ),
                    (
                        "get_recent_reports",
                        get_recent_reports,
                    ),
                )
                and reports_df is not None
            ):

                suggestion = st.pills(
                    "Try asking",
                    SUGGESTED_QUESTIONS,
                    key="suggested_question",
                )

                if (
                    suggestion
                    != st.session_state.get(
                        "last_suggestion"
                    )
                ):
                    st.session_state[
                        "last_suggestion"
                    ] = suggestion

                    if suggestion:
                        ask(
                            suggestion,
                            reports_df,
                        )

                with st.form(
                    "ask_form",
                    clear_on_submit=True,
                    border=False,
                ):

                    q_col, a_col = st.columns(
                        [4, 1],
                        vertical_alignment="bottom",
                    )

                    question = q_col.text_input(
                        "Your question",
                        placeholder=(
                            "Ask anything about "
                            "campus reports..."
                        ),
                        label_visibility="collapsed",
                    )

                    asked = a_col.form_submit_button(
                        "Ask",
                        use_container_width=True,
                    )

                if (
                    asked
                    and question.strip()
                ):
                    ask(
                        question.strip(),
                        reports_df,
                    )

                if (
                    "qa"
                    in st.session_state
                ):
                    q, a = st.session_state["qa"]

                    with st.chat_message("user"):
                        st.markdown(
                            md_safe(q)
                        )

                    with st.chat_message(
                        "assistant",
                        avatar="📢",
                    ):
                        st.markdown(
                            md_safe(a)
                        )

    st.divider()

    # ========================================================
    # Category filter
    # ========================================================

    selected_category = (
        st.pills(
            "Filter by category",
            ["All"] + CATEGORIES,
            default="All",
            format_func=lambda c: (
                "🌐 All"
                if c == "All"
                else f"{CATEGORY_ICONS[c]} {c}"
            ),
            label_visibility="collapsed",
        )
        or "All"
    )

    # ========================================================
    # Emerging issues
    # ========================================================

    st.header(
        "🚨 Emerging Issues"
    )

    st.markdown(
        '<div class="cc-section-note">'
        "Related reports from the same place, "
        "grouped automatically."
        "</div>",
        unsafe_allow_html=True,
    )

    if (
        current_issues is not None
        and reports_df is not None
    ):
        try:

            issues = filter_by_category(
                current_issues,
                selected_category,
            )

            if (
                issues is None
                or len(issues) == 0
            ):
                where = (
                    ""
                    if selected_category == "All"
                    else f" in {selected_category}"
                )

                st.success(
                    "✅ No emerging issues"
                    f"{where} right now."
                )

            else:

                cards = st.columns(
                    2,
                    gap="medium",
                )

                for i, (_, issue) in enumerate(
                    issues.iterrows()
                ):

                    severity = norm_severity(
                        issue.get("SEVERITY")
                    )

                    category = issue.get(
                        "CATEGORY",
                        "Other",
                    )

                    subcategory = (
                        issue.get("SUBCATEGORY")
                        or "Other"
                    )

                    department = (
                        CATEGORY_DEPARTMENTS.get(
                            category,
                            "Campus Operations",
                        )
                    )

                    related = related_reports(
                        issue,
                        reports_df,
                    )

                    with cards[
                        i % 2
                    ].container(
                        border=True,
                        key=(
                            f"card-{severity}-"
                            f"campus-{i}"
                        ),
                    ):

                        st.markdown(
                            f"{severity_badge(severity)} "
                            f":blue-badge[📝 "
                            f"{plural(issue.get('REPORT_COUNT', '?'), 'report')}] "
                            f":gray-badge["
                            f"{CATEGORY_ICONS.get(category, '📌')} "
                            f"{category} / "
                            f"{subcategory}]"
                        )

                        st.markdown(
                            "### "
                            + md_safe(
                                issue.get(
                                    "TITLE",
                                    "Emerging issue",
                                )
                            )
                        )

                        st.markdown(
                            f"📍 **"
                            f"{md_safe(issue.get('LOCATION', '–'))}"
                            f"** &nbsp;·&nbsp; "
                            f"🕒 Last report "
                            f"{format_time(issue.get('LAST_REPORTED'))}"
                        )

                        summary = issue.get(
                            "SUMMARY"
                        )

                        if (
                            not summary
                            and not related.empty
                        ):
                            summary = related.iloc[
                                0
                            ].get("SUMMARY")

                        if summary:
                            st.markdown(
                                f"> {md_safe(summary)}"
                            )

                        st.caption(
                            f"📨 Routed to "
                            f"**{department}**"
                        )

                        with st.expander(
                            f"View {len(related)} "
                            f"report"
                            f"{'' if len(related) == 1 else 's'}"
                        ):
                            for _, r in related.iterrows():

                                created_at = (
                                    r.get(
                                        "CREATED_AT",
                                        "",
                                    )
                                )

                                report_body = (
                                    r.get(
                                        "REPORT_TEXT",
                                        "",
                                    )
                                )

                                st.markdown(
                                    f"**{format_time(created_at)}** — "
                                    f"{md_safe(report_body)}"
                                )

        except Exception as e:
            st.error(
                "Could not display "
                f"issues: {e}"
            )

    elif not waiting_for(
        (
            "detect_emerging_issues",
            detect_emerging_issues,
        ),
        (
            "get_recent_reports",
            get_recent_reports,
        ),
    ):
        st.info(
            "No issue data is available yet."
        )

    st.divider()

    # ========================================================
    # Recent reports
    # ========================================================

    st.header(
        "📋 Recent Reports"
    )

    if (
        reports_df is not None
        and get_recent_reports is not None
    ):

        shown = filter_by_category(
            reports_df,
            selected_category,
        )

        if shown is None or len(shown) == 0:

            st.info(
                "No reports in this category yet."
            )

        else:

            table = shown.copy()

            if "SEVERITY" in table.columns:
                table["SEVERITY"] = (
                    table["SEVERITY"].map(
                        lambda s: (
                            f"{SEVERITY_DOTS.get(norm_severity(s), '⚪')} "
                            f"{norm_severity(s)}"
                        )
                    )
                )

            if "CATEGORY" in table.columns:
                table["CATEGORY"] = (
                    table["CATEGORY"].map(
                        lambda c: (
                            f"{CATEGORY_ICONS.get(c, '📌')} "
                            f"{c}"
                        )
                    )
                )

            desired_columns = [
                "CREATED_AT",
                "SEVERITY",
                "CATEGORY",
                "SUBCATEGORY",
                "LOCATION",
                "SUMMARY",
                "REPORT_TEXT",
            ]

            column_order = [
                column
                for column in desired_columns
                if column in table.columns
            ]

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
                column_order=column_order,
                column_config={
                    "CREATED_AT": (
                        st.column_config.DatetimeColumn(
                            "Reported",
                            format="MMM D, h:mm a",
                        )
                    ),
                    "SEVERITY": (
                        st.column_config.TextColumn(
                            "Severity"
                        )
                    ),
                    "CATEGORY": (
                        st.column_config.TextColumn(
                            "Category"
                        )
                    ),
                    "SUBCATEGORY": (
                        st.column_config.TextColumn(
                            "Type"
                        )
                    ),
                    "LOCATION": (
                        st.column_config.TextColumn(
                            "Location"
                        )
                    ),
                    "SUMMARY": (
                        st.column_config.TextColumn(
                            "AI Summary",
                            width="large",
                        )
                    ),
                    "REPORT_TEXT": (
                        st.column_config.TextColumn(
                            "Original Report",
                            width="medium",
                        )
                    ),
                },
            )

            st.caption(
                f"Showing {len(shown)} reports"
            )


# ============================================================
# Department Operations
# ============================================================

def set_status(
    incident_id,
    status,
):
    """
    Update one incident then invalidate only the incident cache.
    """
    if update_incident_status is None:
        st.error(
            "Incident status updates are not available."
        )
        return

    try:
        update_incident_status(
            incident_id,
            status,
        )

        refresh_incident_data()

        st.rerun()

    except Exception as e:
        st.error(
            "Could not update "
            f"incident: {e}"
        )


with department_tab:

    st.header(
        "🏢 Department Operations"
    )

    st.markdown(
        '<div class="cc-section-note">'
        "Issues are routed here automatically "
        "based on their AI-classified category."
        "</div>",
        unsafe_allow_html=True,
    )

    department_ready = not waiting_for(
        (
            "get_department_incidents",
            get_department_incidents,
        ),
        (
            "update_incident_status",
            update_incident_status,
        ),
    )

    # Do not use st.stop() here because it can stop the entire
    # script even when the user is primarily using Campus Pulse.
    if department_ready:

        department = st.selectbox(
            "Department",
            DEPARTMENTS,
            key="department_selector",
        )

        # ====================================================
        # Cached department read
        # ====================================================

        try:
            incidents = load_department_incidents(
                department
            )

        except Exception as e:
            st.error(
                "Could not load department "
                f"incidents: {e}"
            )
            incidents = None

        if incidents is not None:

            if incidents.empty:

                st.info(
                    "No incidents are currently "
                    "routed to this department."
                )

            else:

                if "STATUS" in incidents.columns:
                    status_series = (
                        incidents["STATUS"]
                        .fillna("NEW")
                        .astype(str)
                        .str.upper()
                    )
                else:
                    status_series = pd.Series(
                        ["NEW"] * len(incidents),
                        index=incidents.index,
                    )

                active_mask = (
                    status_series != "RESOLVED"
                )

                if "SEVERITY" in incidents.columns:
                    critical_mask = (
                        incidents["SEVERITY"].map(
                            norm_severity
                        ) == "CRITICAL"
                    ) & active_mask
                else:
                    critical_mask = pd.Series(
                        [False] * len(incidents),
                        index=incidents.index,
                    )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "🔴 New",
                    int(
                        (
                            status_series == "NEW"
                        ).sum()
                    ),
                )

                c2.metric(
                    "🔵 Active",
                    int(active_mask.sum()),
                )

                c3.metric(
                    "🚨 Critical",
                    int(critical_mask.sum()),
                )

                c4.metric(
                    "🟢 Resolved",
                    int(
                        (
                            status_series
                            == "RESOLVED"
                        ).sum()
                    ),
                )

                st.write("")

                show_resolved = st.toggle(
                    "Show resolved incidents",
                    value=False,
                )

                displayed = incidents.copy()

                if not show_resolved:
                    displayed = displayed[
                        status_series != "RESOLVED"
                    ]

                if displayed.empty:
                    st.success(
                        "✅ No active incidents "
                        "for this department."
                    )

                else:
                    cards = st.columns(
                        2,
                        gap="medium",
                    )

                    for i, (
                        _,
                        incident,
                    ) in enumerate(
                        displayed.iterrows()
                    ):

                        incident_id = int(
                            incident["INCIDENT_ID"]
                        )

                        severity = norm_severity(
                            incident.get(
                                "SEVERITY",
                                "",
                            )
                        )

                        raw_status = incident.get(
                            "STATUS",
                            "NEW",
                        )

                        if pd.isna(raw_status):
                            raw_status = "NEW"

                        status = str(
                            raw_status
                        ).upper()

                        category = str(
                            incident.get(
                                "CATEGORY",
                                "Other",
                            )
                        )

                        raw_subcategory = (
                            incident.get(
                                "SUBCATEGORY",
                                "Other",
                            )
                        )

                        if pd.isna(
                            raw_subcategory
                        ):
                            raw_subcategory = "Other"

                        subcategory = str(
                            raw_subcategory
                        )

                        report_count = (
                            incident.get(
                                "REPORT_COUNT",
                                0,
                            )
                        )

                        try:
                            report_count = int(
                                report_count
                            )
                        except (
                            TypeError,
                            ValueError,
                        ):
                            pass

                        with cards[
                            i % 2
                        ].container(
                            border=True,
                            key=(
                                f"card-{severity}-"
                                f"dept-{incident_id}"
                            ),
                        ):

                            st.markdown(
                                f"{severity_badge(severity)} "
                                f":blue-badge[📝 "
                                f"{plural(report_count, 'report')}] "
                                f":violet-badge["
                                f"{STATUS_LABELS.get(status, status)}]"
                            )

                            st.markdown(
                                "### "
                                + md_safe(
                                    incident.get(
                                        "TITLE",
                                        "Campus incident",
                                    )
                                )
                            )

                            st.markdown(
                                f"📍 **"
                                f"{md_safe(incident.get('LOCATION', '–'))}"
                                f"** &nbsp;·&nbsp; "
                                f"{CATEGORY_ICONS.get(category, '📌')} "
                                f"{category} / "
                                f"{subcategory}"
                            )

                            summary = incident.get(
                                "SUMMARY"
                            )

                            if (
                                summary is not None
                                and not pd.isna(summary)
                                and str(summary).strip()
                            ):
                                st.markdown(
                                    f"> {md_safe(summary)}"
                                )

                            # ================================
                            # Department workflow buttons
                            # ================================

                            if status == "NEW":

                                if st.button(
                                    "✓ Acknowledge",
                                    key=f"ack_{incident_id}",
                                    type="primary",
                                ):
                                    set_status(
                                        incident_id,
                                        "ACKNOWLEDGED",
                                    )

                            elif status == "ACKNOWLEDGED":

                                if st.button(
                                    "🚧 Start Work",
                                    key=(
                                        f"progress_"
                                        f"{incident_id}"
                                    ),
                                    type="primary",
                                ):
                                    set_status(
                                        incident_id,
                                        "IN_PROGRESS",
                                    )

                            elif status == "IN_PROGRESS":

                                if st.button(
                                    "✅ Mark Resolved",
                                    key=(
                                        f"resolve_"
                                        f"{incident_id}"
                                    ),
                                    type="primary",
                                ):
                                    set_status(
                                        incident_id,
                                        "RESOLVED",
                                    )

                            elif status == "RESOLVED":

                                resolved_at = (
                                    incident.get(
                                        "RESOLVED_AT"
                                    )
                                )

                                resolved_text = "Resolved"

                                if (
                                    resolved_at is not None
                                    and pd.notna(
                                        resolved_at
                                    )
                                ):
                                    resolved_text += (
                                        " · "
                                        + format_time(
                                            resolved_at
                                        )
                                    )

                                st.success(
                                    resolved_text
                                )