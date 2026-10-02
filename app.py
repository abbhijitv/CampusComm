import importlib

import streamlit as st


st.set_page_config(
    page_title="Campus Comm",
    page_icon="📢",
    layout="wide",
)


# ============================================================
# Dynamic teammate function loading
# ============================================================

def load_function(
    module_name,
    function_name,
):
    """
    Return a teammate's function,
    or None if it isn't available.
    """

    try:
        module = importlib.import_module(
            module_name
        )
    except Exception:
        return None

    return getattr(
        module,
        function_name,
        None,
    )


# --------------------------------------------------
# Person 1 — Snowflake
# --------------------------------------------------

save_report = load_function(
    "snowflake_client",
    "save_report",
)

get_recent_reports = load_function(
    "snowflake_client",
    "get_recent_reports",
)

get_dashboard_stats = load_function(
    "snowflake_client",
    "get_dashboard_stats",
)

sync_incidents = load_function(
    "snowflake_client",
    "sync_incidents",
)

get_incidents = load_function(
    "snowflake_client",
    "get_incidents",
)

get_department_incidents = load_function(
    "snowflake_client",
    "get_department_incidents",
)

update_incident_status = load_function(
    "snowflake_client",
    "update_incident_status",
)


# --------------------------------------------------
# Person 2 — AI
# --------------------------------------------------

classify_report = load_function(
    "ai",
    "classify_report",
)

generate_briefing = load_function(
    "ai",
    "generate_briefing",
)

answer_question = load_function(
    "ai",
    "answer_question",
)


# --------------------------------------------------
# Person 2 — Analytics
# --------------------------------------------------

detect_emerging_issues = load_function(
    "analytics",
    "detect_emerging_issues",
)


# ============================================================
# Helpers
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
                f"`{m}`"
                for m in missing
            )
        )

        return True

    return False


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


SEVERITY_COLORS = {
    "Critical": "red",
    "High": "red",
    "Medium": "orange",
    "Low": "green",
}


STATUS_LABELS = {
    "NEW": "🔴 New",
    "ACKNOWLEDGED": "🟡 Acknowledged",
    "IN_PROGRESS": "🔵 In Progress",
    "RESOLVED": "🟢 Resolved",
}


def severity_badge(severity):
    severity_text = str(
        severity
    ).title()

    color = SEVERITY_COLORS.get(
        severity_text,
        "gray",
    )

    return (
        f":{color}-badge["
        f"{str(severity).upper()}]"
    )


def filter_by_category(
    df,
    category,
):
    if df is None:
        return df

    if category == "All":
        return df

    if "CATEGORY" not in df.columns:
        return df

    return df[
        df["CATEGORY"] == category
    ]


def sync_current_issues(reports_df):
    """
    Detect current issues and synchronize them
    into the persistent INCIDENTS table.
    """

    if (
        reports_df is None
        or detect_emerging_issues is None
        or sync_incidents is None
    ):
        return None

    issues = detect_emerging_issues(
        reports_df
    )

    if issues is not None and not issues.empty:
        sync_incidents(
            issues
        )

    return issues


# ============================================================
# Load data
# ============================================================

reports_df = None
current_issues = None


if get_recent_reports is not None:
    try:
        reports_df = get_recent_reports(
            limit=200
        )

    except Exception as e:
        st.error(
            f"Could not load reports: {e}"
        )


if reports_df is not None:
    try:
        current_issues = sync_current_issues(
            reports_df
        )

    except Exception as e:
        st.warning(
            "Reports loaded, but incident routing "
            f"could not be synchronized: {e}"
        )


# ============================================================
# Header
# ============================================================

st.title(
    "📢 Campus Comm"
)

st.caption(
    "AI-powered campus issue reporting, "
    "detection, routing, and response."
)


# ============================================================
# Main navigation
# ============================================================

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

    st.caption(
        "Students, faculty, and staff can report issues. "
        "Campus Comm classifies reports, detects patterns, "
        "and routes incidents to the appropriate department."
    )


    # --------------------------------------------------------
    # Dashboard metrics
    # --------------------------------------------------------

    if not waiting_for(
        (
            "get_dashboard_stats",
            get_dashboard_stats,
        )
    ):
        try:
            stats = get_dashboard_stats()

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Total Reports",
                stats.get(
                    "total",
                    "–",
                ),
            )

            c2.metric(
                "Reports Today",
                stats.get(
                    "today",
                    "–",
                ),
            )

            c3.metric(
                "High Severity",
                stats.get(
                    "high_severity",
                    "–",
                ),
            )

            c4.metric(
                "Locations",
                stats.get(
                    "locations",
                    "–",
                ),
            )

        except Exception as e:
            st.error(
                f"Could not load stats: {e}"
            )


    # --------------------------------------------------------
    # Category filter
    # --------------------------------------------------------

    selected_category = st.pills(
        "Filter by category",
        ["All"] + CATEGORIES,
        default="All",
        format_func=lambda c: (
            c
            if c == "All"
            else f"{CATEGORY_ICONS[c]} {c}"
        ),
    )

    selected_category = (
        selected_category
        or "All"
    )


    # --------------------------------------------------------
    # Emerging issues
    # --------------------------------------------------------

    st.header(
        "🚨 Emerging Issues"
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
                    f"No emerging issues{where} right now."
                )

            else:
                cards = st.columns(
                    2,
                    gap="medium",
                )

                for i, (_, issue) in enumerate(
                    issues.iterrows()
                ):

                    with cards[
                        i % 2
                    ].container(
                        border=True
                    ):

                        category = issue.get(
                            "CATEGORY",
                            "Other",
                        )

                        subcategory = issue.get(
                            "SUBCATEGORY",
                            "Other",
                        )

                        severity = issue.get(
                            "SEVERITY",
                            "–",
                        )

                        report_count = issue.get(
                            "REPORT_COUNT",
                            "?",
                        )

                        department = (
                            CATEGORY_DEPARTMENTS.get(
                                category,
                                "Campus Operations",
                            )
                        )

                        st.markdown(
                            f"{severity_badge(severity)} "
                            f":blue-badge["
                            f"{report_count} reports]"
                        )

                        st.markdown(
                            f"### "
                            f"{issue.get('TITLE', 'Emerging issue')}"
                        )

                        st.markdown(
                            f"📍 **"
                            f"{issue.get('LOCATION', '–')}"
                            f"** · "
                            f"{CATEGORY_ICONS.get(category, '📌')} "
                            f"{category}"
                            f" / {subcategory}"
                        )

                        summary = issue.get(
                            "SUMMARY"
                        )

                        if summary:
                            st.write(
                                summary
                            )

                        st.caption(
                            f"📨 Routed to: {department}"
                        )

                        with st.expander(
                            "View Reports"
                        ):
                            related = reports_df[
                                (
                                    reports_df[
                                        "LOCATION"
                                    ]
                                    == issue.get(
                                        "LOCATION"
                                    )
                                )
                                & (
                                    reports_df[
                                        "CATEGORY"
                                    ]
                                    == category
                                )
                            ]

                            if (
                                subcategory
                                and "SUBCATEGORY"
                                in related.columns
                            ):
                                same_subcategory = (
                                    related[
                                        related[
                                            "SUBCATEGORY"
                                        ]
                                        == subcategory
                                    ]
                                )

                                if not same_subcategory.empty:
                                    related = (
                                        same_subcategory
                                    )

                            related = (
                                related
                                .sort_values(
                                    "CREATED_AT",
                                    ascending=False,
                                )
                            )

                            for _, r in related.iterrows():
                                st.markdown(
                                    f"- {r['REPORT_TEXT']}  \n"
                                    f"  :gray["
                                    f"{r['CREATED_AT']}]"
                                )

        except Exception as e:
            st.error(
                f"Could not display issues: {e}"
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


    # --------------------------------------------------------
    # Main columns
    # --------------------------------------------------------

    left, right = st.columns(
        [1, 1.2],
        gap="large",
    )


    # --------------------------------------------------------
    # Report form
    # --------------------------------------------------------

    with left:

        st.subheader(
            "📢 Report a Campus Issue"
        )

        st.caption(
            "Describe the problem and where it is. "
            "Campus Comm classifies and routes it automatically."
        )

        with st.form(
            "report_form",
            clear_on_submit=True,
        ):

            report_text = st.text_area(
                "What's going on?",
                placeholder=(
                    "e.g. I can smell smoke "
                    "inside Hayden Library."
                ),
            )

            location = st.selectbox(
                "Location",
                LOCATIONS,
            )

            other_location = st.text_input(
                "If Other, where?"
            )

            submitted = (
                st.form_submit_button(
                    "Submit Report",
                    type="primary",
                )
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
                        "Analyzing and routing your report..."
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

                    st.rerun()

                except Exception as e:
                    st.error(
                        f"Could not submit report: {e}"
                    )


        if (
            "last_submission"
            in st.session_state
        ):
            result = (
                st.session_state.pop(
                    "last_submission"
                )
            )

            st.success(
                "Report submitted and routed."
            )

            st.markdown(
                f"{severity_badge(result['severity'])} "
                f"{CATEGORY_ICONS.get(result['category'], '📌')} "
                f"**{result['category']}** "
                f"/ {result['subcategory']}"
            )

            st.write(
                result["summary"]
            )

            st.markdown(
                f"📍 **Location:** "
                f"{result['location']}"
            )

            st.markdown(
                f"📨 **Routed to:** "
                f"{result['department']}"
            )

            st.caption(
                "For immediate emergencies, use the "
                "appropriate emergency services."
            )


    # --------------------------------------------------------
    # AI briefing + Q&A
    # --------------------------------------------------------

    with right:

        st.subheader(
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

            if st.button(
                "Generate Briefing",
                key="generate_briefing",
            ):
                try:
                    with st.spinner(
                        "Writing campus briefing..."
                    ):
                        st.session_state[
                            "briefing"
                        ] = generate_briefing(
                            reports_df
                        )

                except Exception as e:
                    st.error(
                        f"Could not generate briefing: {e}"
                    )

            if (
                "briefing"
                in st.session_state
            ):
                st.info(
                    st.session_state[
                        "briefing"
                    ]
                )


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

            question = st.text_input(
                "Ask a question",
                placeholder=(
                    "What's happening at "
                    "Hayden Library?"
                ),
                key="campus_question",
            )

            if (
                st.button(
                    "Ask",
                    key="ask_campus",
                )
                and question.strip()
            ):
                try:
                    with st.spinner(
                        "Thinking..."
                    ):
                        st.session_state[
                            "answer"
                        ] = answer_question(
                            question,
                            reports_df,
                        )

                except Exception as e:
                    st.error(
                        f"Could not answer: {e}"
                    )

            if (
                "answer"
                in st.session_state
            ):
                st.write(
                    st.session_state[
                        "answer"
                    ]
                )


    st.divider()


    # --------------------------------------------------------
    # Recent reports
    # --------------------------------------------------------

    st.subheader(
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

        if len(shown) == 0:
            st.write(
                "No reports in this category yet."
            )

        else:
            st.dataframe(
                shown,
                width="stretch",
                hide_index=True,
            )


# ============================================================
# DEPARTMENT OPERATIONS TAB
# ============================================================

with department_tab:

    st.header(
        "🏢 Department Operations"
    )

    st.caption(
        "Campus issues are automatically routed here "
        "based on their AI-classified category."
    )


    if waiting_for(
        (
            "get_department_incidents",
            get_department_incidents,
        ),
        (
            "update_incident_status",
            update_incident_status,
        ),
    ):
        st.stop()


    department = st.selectbox(
        "Department",
        DEPARTMENTS,
        key="department_selector",
    )


    try:
        incidents = get_department_incidents(
            department
        )

    except Exception as e:
        st.error(
            f"Could not load department incidents: {e}"
        )

        incidents = None


    if incidents is not None:

        if incidents.empty:
            st.info(
                "No incidents are currently routed "
                "to this department."
            )

        else:

            status_series = (
                incidents["STATUS"]
                .fillna("NEW")
                .astype(str)
                .str.upper()
            )

            active_mask = (
                status_series != "RESOLVED"
            )

            critical_mask = (
                incidents["SEVERITY"]
                .fillna("")
                .astype(str)
                .str.upper()
                == "CRITICAL"
            ) & active_mask

            new_mask = (
                status_series == "NEW"
            )

            resolved_mask = (
                status_series == "RESOLVED"
            )


            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "New",
                int(
                    new_mask.sum()
                ),
            )

            c2.metric(
                "Active",
                int(
                    active_mask.sum()
                ),
            )

            c3.metric(
                "Critical",
                int(
                    critical_mask.sum()
                ),
            )

            c4.metric(
                "Resolved",
                int(
                    resolved_mask.sum()
                ),
            )


            st.divider()


            show_resolved = st.toggle(
                "Show resolved incidents",
                value=False,
            )


            displayed = incidents.copy()

            if not show_resolved:
                displayed = displayed[
                    displayed[
                        "STATUS"
                    ].fillna("NEW").str.upper()
                    != "RESOLVED"
                ]


            if displayed.empty:
                st.success(
                    "No active incidents for this department."
                )


            for _, incident in displayed.iterrows():

                incident_id = int(
                    incident["INCIDENT_ID"]
                )

                severity = str(
                    incident["SEVERITY"]
                ).upper()

                status = str(
                    incident["STATUS"]
                    or "NEW"
                ).upper()

                category = str(
                    incident["CATEGORY"]
                )

                subcategory = str(
                    incident["SUBCATEGORY"]
                    or "Other"
                )


                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"{severity_badge(severity)} "
                        f":blue-badge["
                        f"{int(incident['REPORT_COUNT'])} reports]"
                    )

                    st.markdown(
                        f"### {incident['TITLE']}"
                    )

                    st.markdown(
                        f"📍 **{incident['LOCATION']}** · "
                        f"{CATEGORY_ICONS.get(category, '📌')} "
                        f"{category} / {subcategory}"
                    )

                    st.write(
                        incident["SUMMARY"]
                    )

                    st.markdown(
                        f"**Status:** "
                        f"{STATUS_LABELS.get(status, status)}"
                    )

                    st.caption(
                        f"Routed to {department}"
                    )


                    if status == "NEW":

                        if st.button(
                            "✓ Acknowledge",
                            key=f"ack_{incident_id}",
                            type="primary",
                        ):
                            try:
                                update_incident_status(
                                    incident_id,
                                    "ACKNOWLEDGED",
                                )

                                st.rerun()

                            except Exception as e:
                                st.error(
                                    f"Could not update incident: {e}"
                                )


                    elif status == "ACKNOWLEDGED":

                        if st.button(
                            "🚧 Start Work",
                            key=f"progress_{incident_id}",
                            type="primary",
                        ):
                            try:
                                update_incident_status(
                                    incident_id,
                                    "IN_PROGRESS",
                                )

                                st.rerun()

                            except Exception as e:
                                st.error(
                                    f"Could not update incident: {e}"
                                )


                    elif status == "IN_PROGRESS":

                        if st.button(
                            "✅ Mark Resolved",
                            key=f"resolve_{incident_id}",
                            type="primary",
                        ):
                            try:
                                update_incident_status(
                                    incident_id,
                                    "RESOLVED",
                                )

                                st.rerun()

                            except Exception as e:
                                st.error(
                                    f"Could not update incident: {e}"
                                )


                    elif status == "RESOLVED":

                        st.success(
                            "This incident has been resolved."
                        )

                        if incident[
                            "RESOLVED_AT"
                        ] is not None:
                            st.caption(
                                f"Resolved: "
                                f"{incident['RESOLVED_AT']}"
                            )