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
get_department_incidents = load_function("snowflake_client", "get_department_incidents")
update_incident_status = load_function("snowflake_client", "update_incident_status")

# Person 2 — AI
classify_report = load_function("ai", "classify_report")
generate_briefing = load_function("ai", "generate_briefing")
answer_question = load_function("ai", "answer_question")

# Person 2 — Analytics
detect_emerging_issues = load_function("analytics", "detect_emerging_issues")


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

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

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
    .block-container { padding-top: 2.5rem; max-width: 1280px; }

    /* Header */
    .cc-header { display: flex; align-items: center; gap: 1rem; margin-bottom: .25rem; }
    .cc-logo {
        width: 58px; height: 58px; border-radius: 16px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center; font-size: 1.9rem;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        box-shadow: 0 6px 20px rgba(99,102,241,.35);
    }
    .cc-title { font-size: 2.5rem; font-weight: 800; line-height: 1.05; letter-spacing: -0.02em; }
    .cc-sub { font-size: 1.1rem; opacity: .7; margin-top: .3rem; }
    .cc-live {
        display: inline-flex; align-items: center; gap: .45rem; margin-left: auto;
        font-size: .95rem; font-weight: 500; padding: .4rem .9rem; border-radius: 999px;
        border: 1px solid rgba(34,197,94,.35); background: rgba(34,197,94,.10); white-space: nowrap;
    }
    .cc-live i { width: 9px; height: 9px; border-radius: 50%; background: #22C55E; display: inline-block; }

    /* Tabs */
    [data-testid="stTab"] { padding: .6rem 1.2rem .6rem 0; }
    [data-testid="stTab"] p, [data-testid="stTab"] [data-testid="stMarkdownContainer"] { font-size: 1.15rem !important; font-weight: 600 !important; }
    [data-testid="stPills"] button p, [data-testid="stButtonGroup"] button p { font-size: 1rem !important; }

    /* Metric tiles */
    [data-testid="stMetric"] {
        background: var(--cc-card, rgba(128,128,128,.06));
        border: 1px solid rgba(128,128,128,.2);
        border-radius: 14px;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricLabel"] p { font-size: 1rem !important; font-weight: 500; opacity: .75; }

    /* Critical alert */
    .cc-alert {
        display: flex; gap: .9rem; align-items: center;
        border-radius: 14px; padding: 1rem 1.25rem; margin: .4rem 0 1.1rem;
        border: 1px solid rgba(239,68,68,.35); border-left: 6px solid #EF4444;
        background: rgba(239,68,68,.08); font-size: 1.08rem;
    }
    .cc-alert .cc-alert-icon { font-size: 1.6rem; }
    .cc-alert .cc-alert-tag {
        font-size: .8rem; font-weight: 700; letter-spacing: .06em; color: #EF4444;
    }

    .cc-section-note { opacity: .65; font-size: 1.02rem; margin-top: -.5rem; margin-bottom: 1rem; }

    /* Issue cards: thin colored edge by severity */
    div[class*="st-key-card-CRITICAL"] { border-left: 5px solid #EF4444 !important; }
    div[class*="st-key-card-HIGH"]     { border-left: 5px solid #F97316 !important; }
    div[class*="st-key-card-MEDIUM"]   { border-left: 5px solid #EAB308 !important; }
    div[class*="st-key-card-LOW"]      { border-left: 5px solid #22C55E !important; }

    /* Badges a bit larger */
    [data-testid="stMarkdownContainer"] span[class*="badge"] { font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Helpers
# ============================================================

def waiting_for(*names):
    missing = [name for name, fn in names if fn is None]
    if missing:
        st.info("Waiting for: " + ", ".join(f"`{m}`" for m in missing))
        return True
    return False


def md_safe(text):
    """Stop AI text with $ signs from rendering as math."""
    return str(text).replace("$", "\\$")


def norm_severity(severity):
    return str(severity or "").strip().upper()


def severity_badge(severity):
    sev = norm_severity(severity)
    color = SEVERITY_COLORS.get(sev, "gray")
    return f":{color}-badge[{SEVERITY_DOTS.get(sev, '⚪')} {sev or 'UNKNOWN'}]"


def plural(n, word):
    return f"{n} {word}{'' if str(n) == '1' else 's'}"


def format_time(value):
    try:
        return pd.Timestamp(value).strftime("%b %-d, %-I:%M %p")
    except Exception:
        return str(value)


def filter_by_category(df, category):
    if df is None or category == "All" or "CATEGORY" not in df.columns:
        return df
    return df[df["CATEGORY"] == category]


def sort_by_severity(df):
    if df is None or df.empty or "SEVERITY" not in df.columns:
        return df
    rank = df["SEVERITY"].map(
        lambda s: SEVERITY_ORDER.index(norm_severity(s))
        if norm_severity(s) in SEVERITY_ORDER
        else len(SEVERITY_ORDER)
    )
    count = df["REPORT_COUNT"] if "REPORT_COUNT" in df.columns else 0
    return (
        df.assign(_rank=rank, _count=count)
        .sort_values(["_rank", "_count"], ascending=[True, False])
        .drop(columns=["_rank", "_count"])
    )


def related_reports(issue, reports_df):
    related = reports_df[
        (reports_df["LOCATION"] == issue.get("LOCATION"))
        & (reports_df["CATEGORY"] == issue.get("CATEGORY"))
    ]
    subcategory = issue.get("SUBCATEGORY")
    if subcategory and "SUBCATEGORY" in related.columns:
        same_sub = related[related["SUBCATEGORY"] == subcategory]
        if not same_sub.empty:
            related = same_sub
    return related.sort_values("CREATED_AT", ascending=False)


@st.cache_data(ttl=30, show_spinner=False)
def load_reports():
    return get_recent_reports(limit=200)


@st.cache_data(ttl=30, show_spinner=False)
def load_stats():
    return get_dashboard_stats()


def refresh_data():
    load_reports.clear()
    load_stats.clear()


def sync_current_issues(reports_df):
    """Detect current issues and sync them into INCIDENTS when they change."""
    if reports_df is None or detect_emerging_issues is None:
        return None

    issues = detect_emerging_issues(reports_df)

    if sync_incidents is not None and issues is not None and not issues.empty:
        signature = int(pd.util.hash_pandas_object(issues, index=False).sum())
        if st.session_state.get("synced_signature") != signature:
            sync_incidents(issues)
            st.session_state["synced_signature"] = signature

    return issues


def ask(question, reports_df):
    try:
        with st.spinner("Thinking..."):
            st.session_state["qa"] = (question, answer_question(question, reports_df))
    except Exception as e:
        st.error(f"Could not answer: {e}")


# ============================================================
# Load data
# ============================================================

reports_df = None
current_issues = None

if get_recent_reports is not None:
    try:
        reports_df = load_reports()
    except Exception as e:
        st.error(f"Could not load reports: {e}")

if reports_df is not None:
    try:
        current_issues = sort_by_severity(sync_current_issues(reports_df))
    except Exception as e:
        st.warning(f"Reports loaded, but incident routing could not be synchronized: {e}")


# ============================================================
# Header
# ============================================================

hero_col, refresh_col = st.columns([14, 1], vertical_alignment="center")

with hero_col:
    st.markdown(
        f"""
        <div class="cc-header">
          <div class="cc-logo">📢</div>
          <div>
            <div class="cc-title">Campus Comm</div>
            <div class="cc-sub">Know what's happening on campus, before it becomes a bigger problem.</div>
          </div>
          <div class="cc-live"><i></i> Live · {datetime.now().strftime("%-I:%M %p")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with refresh_col:
    if st.button("🔄", help="Refresh data"):
        refresh_data()
        st.rerun()


campus_tab, department_tab = st.tabs(["📊 Campus Pulse", "🏢 Department Operations"])


# ============================================================
# CAMPUS PULSE TAB
# ============================================================

with campus_tab:

    # ---------- Critical alert banner ----------
    if current_issues is not None and not current_issues.empty:
        critical = current_issues[current_issues["SEVERITY"].map(norm_severity) == "CRITICAL"]
        for _, issue in critical.iterrows():
            st.markdown(
                f"""<div class="cc-alert"><div class="cc-alert-icon">🚨</div><div>
                <div class="cc-alert-tag">CRITICAL ALERT</div>
                <b>{html.escape(str(issue.get('TITLE', 'Campus issue')))}</b> —
                {int(issue.get('REPORT_COUNT', 0))} reports at {html.escape(str(issue.get('LOCATION', '')))}.
                Routed to {html.escape(CATEGORY_DEPARTMENTS.get(issue.get('CATEGORY'), 'Campus Operations'))}.
                </div></div>""",
                unsafe_allow_html=True,
            )

    # ---------- Metrics ----------
    if not waiting_for(("get_dashboard_stats", get_dashboard_stats)):
        try:
            stats = load_stats()
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📨 Active Reports", stats.get("total", "–"))
            c2.metric("📅 Today", stats.get("today", "–"))
            c3.metric("🚨 Emerging Issues", 0 if current_issues is None else len(current_issues))
            c4.metric("🔴 Critical Reports", stats.get("critical", "–"))
            c5.metric("📍 Locations", stats.get("locations", "–"))
        except Exception as e:
            st.error(f"Could not load stats: {e}")

    st.write("")

    left, right = st.columns([1, 1.2], gap="large")

    # ---------- Report form ----------
    with left:
        with st.container(border=True):
            st.subheader("📢 Report a Campus Issue")
            st.caption("Describe the problem and where it is. Campus Comm classifies and routes it automatically.")

            with st.form("report_form", clear_on_submit=True, border=False):
                report_text = st.text_area(
                    "What's going on?",
                    placeholder="e.g. I can smell smoke inside Hayden Library.",
                    height=110,
                )
                location = st.selectbox("📍 Location", LOCATIONS)
                other_location = st.text_input("If Other, where?", placeholder="Building or area")
                submitted = st.form_submit_button("Submit Report", type="primary", width="stretch")

            if submitted:
                final_location = other_location.strip() if location == "Other" else location

                if not report_text.strip():
                    st.warning("Please describe the issue.")
                elif not final_location:
                    st.warning("Please enter a location.")
                elif not waiting_for(("classify_report", classify_report), ("save_report", save_report)):
                    try:
                        with st.spinner("🤖 Analyzing and routing your report..."):
                            result = classify_report(report_text)
                            save_report(
                                report_text,
                                final_location,
                                result["category"],
                                result["subcategory"],
                                result["severity"],
                                result["summary"],
                            )
                        st.session_state["last_submission"] = {
                            **result,
                            "location": final_location,
                            "department": CATEGORY_DEPARTMENTS.get(result["category"], "Campus Operations"),
                        }
                        # Reload so the new report shows up in issues and tables right away
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not submit report: {e}")

            if "last_submission" in st.session_state:
                result = st.session_state.pop("last_submission")
                st.success("✅ Report submitted and routed. Thank you!")
                with st.container(border=True):
                    st.markdown(
                        f"{severity_badge(result['severity'])} "
                        f":gray-badge[{CATEGORY_ICONS.get(result['category'], '📌')} "
                        f"{result['category']} / {result['subcategory']}]"
                    )
                    st.markdown(md_safe(result["summary"]))
                    st.caption(f"📍 {result['location']} · 📨 Routed to **{result['department']}**")
                st.caption("For immediate emergencies, contact emergency services.")

    # ---------- AI briefing + Q&A ----------
    with right:
        with st.container(border=True):
            head, btn = st.columns([3, 1.3], vertical_alignment="center")
            head.subheader("✨ AI Campus Briefing")

            if not waiting_for(
                ("generate_briefing", generate_briefing),
                ("get_recent_reports", get_recent_reports),
            ) and reports_df is not None:
                if btn.button("Generate", key="generate_briefing", type="primary", width="stretch"):
                    try:
                        with st.spinner("Writing campus briefing..."):
                            st.session_state["briefing"] = (
                                generate_briefing(reports_df),
                                datetime.now().strftime("%-I:%M %p"),
                            )
                    except Exception as e:
                        st.error(f"Could not generate briefing: {e}")

                if "briefing" in st.session_state:
                    text, generated_at = st.session_state["briefing"]
                    st.markdown(md_safe(text))
                    st.caption(f"Generated at {generated_at} by Snowflake Cortex AI")
                else:
                    st.caption("Get a short AI summary of everything happening on campus right now.")

        with st.container(border=True):
            st.subheader("💬 Ask Campus Comm")

            if not waiting_for(
                ("answer_question", answer_question),
                ("get_recent_reports", get_recent_reports),
            ) and reports_df is not None:
                suggestion = st.pills(
                    "Try asking",
                    SUGGESTED_QUESTIONS,
                    key="suggested_question",
                )
                if suggestion != st.session_state.get("last_suggestion"):
                    st.session_state["last_suggestion"] = suggestion
                    if suggestion:
                        ask(suggestion, reports_df)

                with st.form("ask_form", clear_on_submit=True, border=False):
                    q_col, a_col = st.columns([4, 1], vertical_alignment="bottom")
                    question = q_col.text_input(
                        "Your question",
                        placeholder="Ask anything about campus reports...",
                        label_visibility="collapsed",
                    )
                    asked = a_col.form_submit_button("Ask", width="stretch")

                if asked and question.strip():
                    ask(question.strip(), reports_df)

                if "qa" in st.session_state:
                    q, a = st.session_state["qa"]
                    with st.chat_message("user"):
                        st.markdown(md_safe(q))
                    with st.chat_message("assistant", avatar="📢"):
                        st.markdown(md_safe(a))

    st.divider()

    # ---------- Category filter ----------
    selected_category = st.pills(
        "Filter by category",
        ["All"] + CATEGORIES,
        default="All",
        format_func=lambda c: "🌐 All" if c == "All" else f"{CATEGORY_ICONS[c]} {c}",
        label_visibility="collapsed",
    ) or "All"

    # ---------- Emerging issues ----------
    st.header("🚨 Emerging Issues")
    st.markdown(
        '<div class="cc-section-note">Related reports from the same place, grouped automatically.</div>',
        unsafe_allow_html=True,
    )

    if current_issues is not None and reports_df is not None:
        try:
            issues = filter_by_category(current_issues, selected_category)

            if issues is None or len(issues) == 0:
                where = "" if selected_category == "All" else f" in {selected_category}"
                st.success(f"✅ No emerging issues{where} right now.")
            else:
                cards = st.columns(2, gap="medium")
                for i, (_, issue) in enumerate(issues.iterrows()):
                    severity = norm_severity(issue.get("SEVERITY"))
                    category = issue.get("CATEGORY", "Other")
                    subcategory = issue.get("SUBCATEGORY") or "Other"
                    department = CATEGORY_DEPARTMENTS.get(category, "Campus Operations")
                    related = related_reports(issue, reports_df)

                    with cards[i % 2].container(border=True, key=f"card-{severity}-campus-{i}"):
                        st.markdown(
                            f"{severity_badge(severity)} "
                            f":blue-badge[📝 {plural(issue.get('REPORT_COUNT', '?'), 'report')}] "
                            f":gray-badge[{CATEGORY_ICONS.get(category, '📌')} {category} / {subcategory}]"
                        )
                        st.markdown(f"### {md_safe(issue.get('TITLE', 'Emerging issue'))}")
                        st.markdown(
                            f"📍 **{md_safe(issue.get('LOCATION', '–'))}** &nbsp;·&nbsp; "
                            f"🕒 Last report {format_time(issue.get('LAST_REPORTED'))}"
                        )

                        summary = issue.get("SUMMARY")
                        if not summary and not related.empty:
                            summary = related.iloc[0].get("SUMMARY")
                        if summary:
                            st.markdown(f"> {md_safe(summary)}")

                        st.caption(f"📨 Routed to **{department}**")

                        with st.expander(f"View {len(related)} report{'' if len(related) == 1 else 's'}"):
                            for _, r in related.iterrows():
                                st.markdown(
                                    f"**{format_time(r['CREATED_AT'])}** — {md_safe(r['REPORT_TEXT'])}"
                                )
        except Exception as e:
            st.error(f"Could not display issues: {e}")

    elif not waiting_for(
        ("detect_emerging_issues", detect_emerging_issues),
        ("get_recent_reports", get_recent_reports),
    ):
        st.info("No issue data is available yet.")


    st.divider()

    # ---------- Recent reports ----------
    st.header("📋 Recent Reports")

    if reports_df is not None and get_recent_reports is not None:
        shown = filter_by_category(reports_df, selected_category)

        if len(shown) == 0:
            st.info("No reports in this category yet.")
        else:
            table = shown.copy()
            table["SEVERITY"] = table["SEVERITY"].map(
                lambda s: f"{SEVERITY_DOTS.get(norm_severity(s), '⚪')} {norm_severity(s)}"
            )
            table["CATEGORY"] = table["CATEGORY"].map(
                lambda c: f"{CATEGORY_ICONS.get(c, '📌')} {c}"
            )
            st.dataframe(
                table,
                width="stretch",
                hide_index=True,
                column_order=[
                    "CREATED_AT", "SEVERITY", "CATEGORY", "SUBCATEGORY",
                    "LOCATION", "SUMMARY", "REPORT_TEXT",
                ],
                column_config={
                    "CREATED_AT": st.column_config.DatetimeColumn("Reported", format="MMM D, h:mm a"),
                    "SEVERITY": st.column_config.TextColumn("Severity"),
                    "CATEGORY": st.column_config.TextColumn("Category"),
                    "SUBCATEGORY": st.column_config.TextColumn("Type"),
                    "LOCATION": st.column_config.TextColumn("Location"),
                    "SUMMARY": st.column_config.TextColumn("AI Summary", width="large"),
                    "REPORT_TEXT": st.column_config.TextColumn("Original Report", width="medium"),
                },
            )
            st.caption(f"Showing {len(shown)} reports")


# ============================================================
# DEPARTMENT OPERATIONS TAB
# ============================================================

def set_status(incident_id, status):
    try:
        update_incident_status(incident_id, status)
        refresh_data()
        st.rerun()
    except Exception as e:
        st.error(f"Could not update incident: {e}")


with department_tab:

    st.header("🏢 Department Operations")
    st.markdown(
        '<div class="cc-section-note">Issues are routed here automatically based on their AI-classified category.</div>',
        unsafe_allow_html=True,
    )

    if waiting_for(
        ("get_department_incidents", get_department_incidents),
        ("update_incident_status", update_incident_status),
    ):
        st.stop()

    department = st.selectbox("Department", DEPARTMENTS, key="department_selector")

    try:
        incidents = get_department_incidents(department)
    except Exception as e:
        st.error(f"Could not load department incidents: {e}")
        incidents = None

    if incidents is not None:
        if incidents.empty:
            st.info("No incidents are currently routed to this department.")
        else:
            status_series = incidents["STATUS"].fillna("NEW").astype(str).str.upper()
            active_mask = status_series != "RESOLVED"
            critical_mask = (incidents["SEVERITY"].map(norm_severity) == "CRITICAL") & active_mask

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔴 New", int((status_series == "NEW").sum()))
            c2.metric("🔵 Active", int(active_mask.sum()))
            c3.metric("🚨 Critical", int(critical_mask.sum()))
            c4.metric("🟢 Resolved", int((status_series == "RESOLVED").sum()))

            st.write("")
            show_resolved = st.toggle("Show resolved incidents", value=False)

            displayed = incidents.copy()
            if not show_resolved:
                displayed = displayed[status_series != "RESOLVED"]

            if displayed.empty:
                st.success("✅ No active incidents for this department.")

            cards = st.columns(2, gap="medium")
            for i, (_, incident) in enumerate(displayed.iterrows()):
                incident_id = int(incident["INCIDENT_ID"])
                severity = norm_severity(incident["SEVERITY"])
                status = str(incident["STATUS"] or "NEW").upper()
                category = str(incident["CATEGORY"])
                subcategory = str(incident["SUBCATEGORY"] or "Other")

                with cards[i % 2].container(border=True, key=f"card-{severity}-dept-{incident_id}"):
                    st.markdown(
                        f"{severity_badge(severity)} "
                        f":blue-badge[📝 {plural(int(incident['REPORT_COUNT']), 'report')}] "
                        f":violet-badge[{STATUS_LABELS.get(status, status)}]"
                    )
                    st.markdown(f"### {md_safe(incident['TITLE'])}")
                    st.markdown(
                        f"📍 **{md_safe(incident['LOCATION'])}** &nbsp;·&nbsp; "
                        f"{CATEGORY_ICONS.get(category, '📌')} {category} / {subcategory}"
                    )
                    if incident["SUMMARY"]:
                        st.markdown(f"> {md_safe(incident['SUMMARY'])}")

                    if status == "NEW":
                        if st.button("✓ Acknowledge", key=f"ack_{incident_id}", type="primary"):
                            set_status(incident_id, "ACKNOWLEDGED")
                    elif status == "ACKNOWLEDGED":
                        if st.button("🚧 Start Work", key=f"progress_{incident_id}", type="primary"):
                            set_status(incident_id, "IN_PROGRESS")
                    elif status == "IN_PROGRESS":
                        if st.button("✅ Mark Resolved", key=f"resolve_{incident_id}", type="primary"):
                            set_status(incident_id, "RESOLVED")
                    elif status == "RESOLVED":
                        resolved_at = incident.get("RESOLVED_AT")
                        st.success(
                            "Resolved"
                            + (f" · {format_time(resolved_at)}" if pd.notna(resolved_at) else "")
                        )
