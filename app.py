import importlib

import streamlit as st

st.set_page_config(page_title="Campus Comm", page_icon="📢", layout="wide")


def load_function(module_name, function_name):
    """Return a teammate's function, or None if it isn't written yet."""
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None
    return getattr(module, function_name, None)


# snowflake_client.py (Person 1)
save_report = load_function("snowflake_client", "save_report")
get_recent_reports = load_function("snowflake_client", "get_recent_reports")
get_dashboard_stats = load_function("snowflake_client", "get_dashboard_stats")

# ai.py (Person 2)
classify_report = load_function("ai", "classify_report")
generate_briefing = load_function("ai", "generate_briefing")
answer_question = load_function("ai", "answer_question")

# analytics.py (Person 2)
detect_emerging_issues = load_function("analytics", "detect_emerging_issues")


def waiting_for(*names):
    missing = [name for name, fn in names if fn is None]
    if missing:
        st.info("Waiting for: " + ", ".join(f"`{m}`" for m in missing))
        return True
    return False


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

SEVERITY_COLORS = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}


def severity_badge(severity):
    color = SEVERITY_COLORS.get(str(severity).title(), "gray")
    return f":{color}-badge[{str(severity).upper()}]"


def filter_by_category(df, category):
    if df is None or category == "All" or "CATEGORY" not in df.columns:
        return df
    return df[df["CATEGORY"] == category]


# ---------- Header ----------
st.title("📢 Campus Comm")
st.caption("Know what's happening on campus, before it becomes a bigger problem.")

# ---------- Load reports once for the sections that need them ----------
reports_df = None
if get_recent_reports is not None:
    try:
        reports_df = get_recent_reports(limit=200)
    except Exception as e:
        st.error(f"Could not load reports: {e}")

# ---------- Metrics ----------
if not waiting_for(("get_dashboard_stats", get_dashboard_stats)):
    try:
        stats = get_dashboard_stats()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Reports", stats.get("total", "–"))
        c2.metric("Reports Today", stats.get("today", "–"))
        c3.metric("🔴 Critical", stats.get("critical", "–"))
        c4.metric("🟠 High", stats.get("high", "–"))
        c5.metric("Active", stats.get("active", "–"))
    except Exception as e:
        st.error(f"Could not load stats: {e}")

# ---------- Category filter ----------
selected_category = st.pills(
    "Filter by category",
    ["All"] + CATEGORIES,
    default="All",
    format_func=lambda c: c if c == "All" else f"{CATEGORY_ICONS[c]} {c}",
)
selected_category = selected_category or "All"

# ---------- Emerging issues ----------
st.header("🚨 Emerging Issues")
if not waiting_for(
    ("detect_emerging_issues", detect_emerging_issues),
    ("get_recent_reports", get_recent_reports),
) and reports_df is not None:
    try:
        issues = filter_by_category(detect_emerging_issues(reports_df), selected_category)
        if issues is None or len(issues) == 0:
            where = "" if selected_category == "All" else f" in {selected_category}"
            st.success(f"No emerging issues{where} right now.")
        else:
            cards = st.columns(2, gap="medium")
            for i, (_, issue) in enumerate(issues.iterrows()):
                with cards[i % 2].container(border=True):
                    category = issue.get("CATEGORY", "Other")
                    subcategory = issue.get("SUBCATEGORY")
                    st.markdown(
                        f"{severity_badge(issue.get('SEVERITY', '–'))} "
                        f":blue-badge[{issue.get('REPORT_COUNT', '?')} reports]"
                    )
                    st.markdown(f"### {issue.get('TITLE', 'Emerging issue')}")
                    st.markdown(
                        f"📍 **{issue.get('LOCATION', '–')}** · "
                        f"{CATEGORY_ICONS.get(category, '📌')} {category}"
                        + (f" / {subcategory}" if subcategory else "")
                    )
                    if issue.get("SUMMARY"):
                        st.write(issue["SUMMARY"])
                    with st.expander("View Reports"):
                        related = reports_df[
                            (reports_df["LOCATION"] == issue.get("LOCATION"))
                            & (reports_df["CATEGORY"] == category)
                        ]
                        for _, r in related.iterrows():
                            st.markdown(f"- {r['REPORT_TEXT']}  \n  :gray[{r['CREATED_AT']}]")
    except Exception as e:
        st.error(f"Could not detect issues: {e}")

st.divider()

left, right = st.columns([1, 1.2], gap="large")

# ---------- Report form ----------
with left:
    st.subheader("📢 Report a Campus Issue")
    st.caption("Just describe the problem and where it is — our AI handles the rest.")
    with st.form("report_form", clear_on_submit=True):
        report_text = st.text_area(
            "What's going on?",
            placeholder="e.g. Wi-Fi isn't working on the second floor of Hayden.",
        )
        location = st.selectbox("Location", LOCATIONS)
        other_location = st.text_input("If Other, where?")
        submitted = st.form_submit_button("Submit Report", type="primary")

    if submitted:
        final_location = other_location.strip() if location == "Other" else location
        if not report_text.strip():
            st.warning("Please describe the issue.")
        elif not final_location:
            st.warning("Please enter a location.")
        elif not waiting_for(("classify_report", classify_report), ("save_report", save_report)):
            try:
                with st.spinner("Analyzing your report with Snowflake Cortex AI..."):
                    result = classify_report(report_text)
                    save_report(
                        report_text,
                        final_location,
                        result["category"],
                        result["subcategory"],
                        result["severity"],
                        result["summary"],
                    )
                # Rerun so the new report shows up in issues and the table right away
                st.session_state.last_submission = result
                st.rerun()
            except Exception as e:
                st.error(f"Could not submit report: {e}")

    if "last_submission" in st.session_state:
        result = st.session_state.pop("last_submission")
        st.success("Report submitted. Thank you!")
        st.markdown(
            f"{severity_badge(result['severity'])} "
            f"{CATEGORY_ICONS.get(result['category'], '📌')} "
            f"**{result['category']}** / {result['subcategory']}  \n"
            f"{result['summary']}"
        )

# ---------- AI briefing + Ask ----------
with right:
    st.subheader("✨ AI Campus Briefing")
    if not waiting_for(
        ("generate_briefing", generate_briefing),
        ("get_recent_reports", get_recent_reports),
    ) and reports_df is not None:
        if st.button("Generate Briefing"):
            try:
                with st.spinner("Writing campus briefing..."):
                    st.session_state.briefing = generate_briefing(reports_df)
            except Exception as e:
                st.error(f"Could not generate briefing: {e}")
        if "briefing" in st.session_state:
            st.info(st.session_state.briefing)

    st.subheader("💬 Ask Campus Comm")
    if not waiting_for(
        ("answer_question", answer_question),
        ("get_recent_reports", get_recent_reports),
    ) and reports_df is not None:
        question = st.text_input("Ask a question", placeholder="What's happening at Hayden Library?")
        if st.button("Ask") and question.strip():
            try:
                with st.spinner("Thinking..."):
                    st.session_state.answer = answer_question(question, reports_df)
            except Exception as e:
                st.error(f"Could not answer: {e}")
        if "answer" in st.session_state:
            st.write(st.session_state.answer)

st.divider()

# ---------- Recent reports ----------
st.subheader("📋 Recent Reports")
if not waiting_for(("get_recent_reports", get_recent_reports)) and reports_df is not None:
    shown = filter_by_category(reports_df, selected_category)
    if len(shown) == 0:
        st.write("No reports in this category yet.")
    else:
        st.dataframe(shown, width="stretch", hide_index=True)
