
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# Configuration
# =========================================================

API_BASE_URL = os.getenv(
    "COPILOT_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

st.set_page_config(
    page_title="Data Quality Copilot",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# Theme and CSS
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #0b1020;
        --panel: #111a2e;
        --panel-2: #151f35;
        --border: #26344d;
        --text: #edf3ff;
        --muted: #93a4bf;
        --cyan: #54d6e8;
        --green: #4ade80;
        --red: #fb7185;
        --amber: #fbbf24;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, #142541 0%, transparent 36%),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(11, 16, 32, 0.88);
    }

    [data-testid="stSidebar"] {
        background: #0c1425;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }

    h1, h2, h3 {
        letter-spacing: -0.035em;
        color: var(--text);
    }

    p, label, .stMarkdown {
        color: var(--text);
    }

    .brand {
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--cyan);
        font-weight: 800;
    }

    .brand-title {
        font-size: 22px;
        line-height: 1.25;
        font-weight: 800;
        color: var(--text);
        margin-top: 7px;
    }

    .muted {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
    }

    .eyebrow {
        color: var(--cyan);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 11px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .page-title {
        font-size: 31px;
        line-height: 1.2;
        font-weight: 800;
        letter-spacing: -1.2px;
        margin: 0 0 8px 0;
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 25px;
    }

    .metric-card {
        background: linear-gradient(145deg, #15223a, #10192b);
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 19px 20px;
        min-height: 137px;
        margin-bottom: 12px;
    }

    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--muted);
        margin-bottom: 15px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -1px;
        color: var(--text);
        line-height: 1.2;
    }

    .metric-caption {
        color: var(--muted);
        font-size: 11px;
        margin-top: 10px;
    }

    .panel {
        background: rgba(17, 26, 46, 0.92);
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .panel-title {
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .panel-subtitle {
        font-size: 12px;
        color: var(--muted);
        margin-bottom: 18px;
    }

    .status-pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.7px;
    }

    .status-pass {
        background: rgba(74, 222, 128, 0.12);
        color: var(--green);
        border: 1px solid rgba(74, 222, 128, 0.3);
    }

    .status-fail {
        background: rgba(251, 113, 133, 0.12);
        color: var(--red);
        border: 1px solid rgba(251, 113, 133, 0.3);
    }

    .status-unknown {
        background: rgba(251, 191, 36, 0.12);
        color: var(--amber);
        border: 1px solid rgba(251, 191, 36, 0.3);
    }

    .issue-card {
        background: #111a2e;
        border: 1px solid var(--border);
        border-left: 3px solid var(--red);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }

    .issue-name {
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 6px;
    }

    .issue-description {
        font-size: 12px;
        color: var(--muted);
        line-height: 1.6;
    }

    .footer {
        border-top: 1px solid var(--border);
        padding-top: 17px;
        margin-top: 35px;
        color: var(--muted);
        font-size: 11px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }

    div[data-testid="stMetric"] {
        background: #111a2e;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px;
    }

    .stButton button, .stDownloadButton button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 40px;
    }

    .stButton button[kind="primary"] {
        background: #38bdf8;
        color: #07111f;
        border: none;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background: #111a2e;
        border-color: var(--border);
    }

    [data-testid="stSidebar"] .stRadio label {
        padding: 5px 0;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API helpers
# =========================================================

class APIError(Exception):
    """Raised when the backend cannot provide a usable response."""


def api_get(path, params=None):
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise APIError(
            f"Could not reach the API endpoint {path}. "
            "Check that FastAPI is running and the API URL is correct."
        ) from exc
    except ValueError as exc:
        raise APIError(
            f"The API returned an invalid response for {path}."
        ) from exc


@st.cache_data(ttl=30, show_spinner=False)
def load_overview():
    return api_get("/overview")


@st.cache_data(ttl=30, show_spinner=False)
def load_quality_results():
    data = api_get("/quality-results")
    if not isinstance(data, list):
        raise APIError("Quality results were not returned as a list.")
    return pd.DataFrame(data)


@st.cache_data(ttl=30, show_spinner=False)
def load_records(layer, limit):
    data = api_get(f"/records/{layer}", params={"limit": limit})
    if not isinstance(data, list):
        raise APIError("The records endpoint did not return a list.")
    return pd.DataFrame(data)


def load_health(path):
    try:
        return api_get(path)
    except APIError as exc:
        return {"status": "failed", "error": str(exc)}


def safe_int(value):
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def format_number(value):
    return f"{safe_int(value):,}"


def metric_card(label, value, caption, accent="#54d6e8"):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{accent}">
                {value}
            </div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title, subtitle, section="DATA OBSERVABILITY"):
    st.markdown(
        f"""
        <div class="eyebrow">{section}</div>
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(status):
    value = str(status).upper()
    if value == "PASS":
        css_class = "status-pass"
    elif value == "FAIL":
        css_class = "status-fail"
    else:
        css_class = "status-unknown"

    return (
        f'<span class="status-pill {css_class}">'
        f"{value}</span>"
    )


def explain_check(check_name):
    explanations = {
        "duplicate_order_id": (
            "Duplicate order identifiers were found in the raw Bronze "
            "data. Check source-system retries, repeated file ingestion, "
            "and the business key used to identify an order."
        ),
        "missing_customer_id": (
            "Some orders do not have a customer identifier. Investigate "
            "source completeness, customer mapping, and upstream joins."
        ),
        "missing_unit_price": (
            "Some orders are missing their unit price. Verify source "
            "pricing fields and reject or repair records according to "
            "your business rules."
        ),
        "negative_quantity": (
            "Negative quantities may represent invalid transactions "
            "or legitimate returns. Confirm the business rule before "
            "automatically removing these records."
        ),
        "invalid_payment_method": (
            "Payment methods contain values outside the accepted "
            "domain. Standardize source values and maintain a controlled "
            "set of supported payment methods."
        ),
        "silver_duplicate_order_id": (
            "The Silver table should contain unique order identifiers. "
            "Investigate deduplication logic if this check fails."
        ),
        "silver_missing_required_fields": (
            "Required fields remain missing after transformation. "
            "Review validation rules and the quarantine criteria."
        ),
        "bronze_silver_reconciliation": (
            "Bronze record counts do not reconcile with Silver and "
            "Quarantine. Verify ingestion counts, filtering, and "
            "the transformation process."
        ),
    }
    return explanations.get(
        str(check_name),
        "Review the failed rule, inspect affected records, and trace "
        "the issue back to the source or transformation step.",
    )


def prepare_quality_frame(df):
    if df.empty:
        return df

    df = df.copy()

    if "failed_records" in df.columns:
        df["failed_records"] = pd.to_numeric(
            df["failed_records"], errors="coerce"
        ).fillna(0).astype(int)

    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.upper()

    return df


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    st.markdown('<div class="brand">DATA ENGINEERING</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-title">Quality<br>Copilot</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted">Governed pipelines. '
        'Trustworthy data.</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    pages = [
        "Overview",
        "Quality Monitor",
        "Data Explorer",
        "AI Copilot",
        "System Health",
    ]

    selected_page = st.radio(
        "WORKSPACE",
        pages,
        label_visibility="visible",
    )

    st.divider()

    st.markdown(
        '<div class="eyebrow">CONNECTED SERVICES</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted">FastAPI · Databricks SQL<br>'
        'PostgreSQL · Streamlit</div>',
        unsafe_allow_html=True,
    )

    if st.button("↻ Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="muted">AI Data Quality Copilot<br>'
        'Portfolio edition · v2.0</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# Fetch current metrics
# =========================================================

try:
    overview = load_overview()
    quality_df = prepare_quality_frame(load_quality_results())
    api_available = True
    api_error = None
except APIError as exc:
    overview = {}
    quality_df = pd.DataFrame()
    api_available = False
    api_error = str(exc)


# =========================================================
# Overview
# =========================================================

if selected_page == "Overview":
    page_header(
        "Pipeline overview",
        "A live operational view of your data pipeline and validation results.",
    )

    if not api_available:
        st.error(api_error)
        st.info(
            "Start the FastAPI backend in another terminal, then refresh "
            "this page."
        )
        st.code("uvicorn backend.main:app --reload")
    else:
        records = overview.get("records", {})
        quality = overview.get("quality", {})

        bronze = safe_int(records.get("bronze", 0))
        silver = safe_int(records.get("silver", 0))
        quarantine = safe_int(records.get("quarantine", 0))
        total_checks = safe_int(quality.get("total_checks", 0))
        passed = safe_int(quality.get("passed_checks", 0))
        failed = safe_int(quality.get("failed_checks", 0))
        score = float(quality.get("score", 0) or 0)

        cols = st.columns(4)
        with cols[0]:
            metric_card("BRONZE RECORDS", format_number(bronze),
                        "Raw ingested records")
        with cols[1]:
            metric_card("SILVER RECORDS", format_number(silver),
                        "Records accepted by transformations",
                        "#4ade80")
        with cols[2]:
            metric_card("QUARANTINED", format_number(quarantine),
                        "Records isolated from Silver", "#fb7185")
        with cols[3]:
            metric_card("CHECK PASS RATE", f"{score:.1f}%",
                        f"{passed} passed of {total_checks} checks",
                        "#fbbf24" if failed else "#4ade80")

        st.markdown("")

        left, right = st.columns([1.15, 1])

        with left:
            st.markdown(
                '<div class="panel-title">Pipeline distribution</div>'
                '<div class="panel-subtitle">'
                'Current record counts by processing layer</div>',
                unsafe_allow_html=True,
            )

            pipeline_df = pd.DataFrame({
                "Layer": ["Bronze", "Silver", "Quarantine"],
                "Records": [bronze, silver, quarantine],
            })

            fig = px.bar(
                pipeline_df,
                x="Layer",
                y="Records",
                color="Layer",
                color_discrete_map={
                    "Bronze": "#54d6e8",
                    "Silver": "#4ade80",
                    "Quarantine": "#fb7185",
                },
                text="Records",
            )
            fig.update_traces(
                texttemplate="%{text:,}",
                textposition="outside",
                cliponaxis=False,
            )
            fig.update_layout(
                height=320,
                showlegend=False,
                margin=dict(l=10, r=10, t=25, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c7d4e8", family="Inter"),
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#26344d",
                    zeroline=False,
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.markdown(
                '<div class="panel-title">Validation summary</div>'
                '<div class="panel-subtitle">'
                'Latest recorded quality-check outcomes</div>',
                unsafe_allow_html=True,
            )

            summary_df = pd.DataFrame({
                "Outcome": ["Passed", "Failed"],
                "Checks": [passed, failed],
            })

            if total_checks:
                fig = px.pie(
                    summary_df,
                    names="Outcome",
                    values="Checks",
                    hole=0.72,
                    color="Outcome",
                    color_discrete_map={
                        "Passed": "#4ade80",
                        "Failed": "#fb7185",
                    },
                )
                fig.update_traces(
                    textinfo="label+value",
                    textfont_size=12,
                    marker=dict(line=dict(color="#111a2e", width=3)),
                )
                fig.update_layout(
                    height=320,
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#c7d4e8", family="Inter"),
                    annotations=[dict(
                        text=f"{total_checks}<br><sup>checks</sup>",
                        x=0.5, y=0.5,
                        font_size=22,
                        showarrow=False,
                        font_color="#edf3ff",
                    )],
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No quality-check results are available.")

        st.markdown("### Latest quality results")

        if not quality_df.empty:
            failed_df = quality_df[
                quality_df["status"] == "FAIL"
            ].copy()

            if failed_df.empty:
                st.success("All recorded quality checks passed.")
            else:
                display_cols = [
                    c for c in [
                        "dataset", "check_name", "status", "failed_records"
                    ] if c in failed_df.columns
                ]
                st.dataframe(
                    failed_df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                )
                if st.button("Investigate failed checks",
                             type="primary"):
                    st.session_state["requested_page"] = "Quality Monitor"
                    st.rerun()

        total_accounted = silver + quarantine
        if bronze:
            reconciliation = total_accounted == bronze
            if reconciliation:
                st.success(
                    f"Reconciliation passed: {bronze:,} Bronze records = "
                    f"{silver:,} Silver + {quarantine:,} Quarantined."
                )
            else:
                st.warning(
                    f"Reconciliation needs investigation: Bronze has "
                    f"{bronze:,} records, while Silver + Quarantine has "
                    f"{total_accounted:,}."
                )

        st.caption(
            "Metrics reflect the latest available API results. "
            "Historical trends are not shown because this dashboard "
            "does not yet store time-series snapshots."
        )


# =========================================================
# Quality Monitor
# =========================================================

elif selected_page == "Quality Monitor":
    page_header(
        "Quality monitor",
        "Filter validation rules, prioritize failures, and investigate causes.",
    )

    if not api_available:
        st.error(api_error)
    elif quality_df.empty:
        st.info("No quality-check results are available.")
    else:
        status_values = (
            sorted(quality_df["status"].dropna().unique().tolist())
            if "status" in quality_df.columns else []
        )

        c1, c2 = st.columns([1, 1.5])

        with c1:
            selected_status = st.multiselect(
                "Filter by status",
                options=status_values,
                default=[s for s in status_values if s == "FAIL"],
            )

        with c2:
            query = st.text_input(
                "Search checks",
                placeholder="Search a rule or dataset...",
            )

        filtered = quality_df.copy()

        if selected_status and "status" in filtered.columns:
            filtered = filtered[
                filtered["status"].isin(selected_status)
            ]

        if query.strip():
            searchable = filtered.astype(str).apply(
                lambda col: col.str.contains(
                    query.strip(), case=False, na=False
                )
            ).any(axis=1)
            filtered = filtered[searchable]

        fail_count = int(
            (quality_df["status"] == "FAIL").sum()
        ) if "status" in quality_df.columns else 0

        m1, m2, m3 = st.columns(3)
        with m1:
            metric_card("TOTAL RULES", str(len(quality_df)),
                        "Rules in latest result set")
        with m2:
            metric_card("FAILED RULES", str(fail_count),
                        "Rules requiring investigation", "#fb7185")
        with m3:
            metric_card("DISPLAYED", str(len(filtered)),
                        "Results matching your filters")

        st.markdown("### Validation results")

        if filtered.empty:
            st.info("No checks match your filters.")
        else:
            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "failed_records": st.column_config.NumberColumn(
                        "Failed records", format="%d"
                    )
                },
            )

        failures = quality_df[
            quality_df["status"] == "FAIL"
        ].copy() if "status" in quality_df.columns else pd.DataFrame()

        if not failures.empty:
            st.markdown("### Failure investigation")

            options = failures["check_name"].tolist()
            selected_check = st.selectbox(
                "Select a failed rule",
                options=options,
            )

            row = failures[
                failures["check_name"] == selected_check
            ].iloc[0]

            left, right = st.columns([2, 1])

            with left:
                st.markdown(
                    f"""
                    <div class="issue-card">
                        <div class="issue-name">{selected_check}</div>
                        <div class="issue-description">
                            {explain_check(selected_check)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with right:
                metric_card(
                    "AFFECTED RECORDS",
                    format_number(row.get("failed_records", 0)),
                    "Reported by the quality rule",
                    "#fb7185",
                )

            st.caption(
                "These explanations are deterministic guidance from "
                "predefined rules, not output from a connected LLM."
            )

        csv_bytes = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export filtered results",
            data=csv_bytes,
            file_name="quality_results.csv",
            mime="text/csv",
        )


# =========================================================
# Data Explorer
# =========================================================

elif selected_page == "Data Explorer":
    page_header(
        "Data explorer",
        "Inspect pipeline layers, search sample records, and export data.",
    )

    layer_labels = {
        "Bronze — raw": "bronze",
        "Silver — validated": "silver",
        "Quarantine — rejected": "quarantine",
    }

    c1, c2 = st.columns([1, 1])

    with c1:
        chosen_label = st.selectbox(
            "Pipeline layer",
            list(layer_labels.keys()),
            index=1,
        )

    with c2:
        record_limit = st.select_slider(
            "Maximum records to load",
            options=[25, 50, 100, 250, 500],
            value=100,
        )

    if st.button("Load records", type="primary"):
        st.session_state["explorer_layer"] = layer_labels[chosen_label]
        st.session_state["explorer_limit"] = record_limit

    active_layer = st.session_state.get("explorer_layer")
    active_limit = st.session_state.get("explorer_limit", 100)

    if active_layer:
        try:
            records_df = load_records(active_layer, active_limit)

            st.markdown(
                f"### {active_layer.title()} records"
            )

            if records_df.empty:
                st.info("No records were returned for this layer.")
            else:
                st.caption(
                    f"Loaded {len(records_df):,} records. "
                    "Search applies to the loaded sample."
                )

                search_term = st.text_input(
                    "Search loaded records",
                    placeholder="Enter an order ID, city, payment method...",
                )

                visible_df = records_df.copy()

                if search_term.strip():
                    matches = visible_df.astype(str).apply(
                        lambda col: col.str.contains(
                            search_term.strip(),
                            case=False,
                            na=False,
                        )
                    ).any(axis=1)
                    visible_df = visible_df[matches]

                st.dataframe(
                    visible_df,
                    use_container_width=True,
                    hide_index=True,
                    height=440,
                )

                st.download_button(
                    "Export displayed records",
                    data=visible_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"{active_layer}_records.csv",
                    mime="text/csv",
                )

                if "order_value" in records_df.columns:
                    values = pd.to_numeric(
                        records_df["order_value"], errors="coerce"
                    ).dropna()

                    if not values.empty:
                        st.markdown("### Order value profile")
                        a, b, c = st.columns(3)
                        a.metric("Average", f"{values.mean():,.2f}")
                        b.metric("Median", f"{values.median():,.2f}")
                        c.metric("Maximum", f"{values.max():,.2f}")

        except APIError as exc:
            st.error(str(exc))
    else:
        st.info(
            "Choose a pipeline layer and select **Load records** "
            "to inspect its data."
        )


# =========================================================
# AI Copilot
# =========================================================

elif selected_page == "AI Copilot":
    page_header(
        "AI copilot",
        "Understand data-quality failures and get practical investigation guidance.",
        section="ASSISTED INVESTIGATION",
    )

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Investigation assistant</div>
            <div class="panel-subtitle">
                This version uses transparent, predefined diagnostic rules.
                A live LLM or Databricks Genie integration is not yet connected.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not api_available:
        st.error(api_error)
    elif quality_df.empty:
        st.info("No quality results are available to investigate.")
    else:
        failed_df = quality_df[
            quality_df["status"] == "FAIL"
        ].copy() if "status" in quality_df.columns else pd.DataFrame()

        if failed_df.empty:
            st.success("No failed checks were returned.")
        else:
            check_names = failed_df["check_name"].tolist()

            selected_check = st.selectbox(
                "Which issue do you want to investigate?",
                check_names,
                key="copilot_selected_check",
            )

            selected_row = failed_df[
                failed_df["check_name"] == selected_check
            ].iloc[0]

            st.markdown("### Diagnostic report")

            st.markdown(
                f"""
                <div class="issue-card">
                    <div class="eyebrow">DETECTED RULE FAILURE</div>
                    <div class="issue-name">{selected_check}</div>
                    <div class="issue-description">
                        {explain_check(selected_check)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.metric(
                "Reported failed records",
                format_number(selected_row.get("failed_records", 0)),
            )

            st.markdown("### Recommended investigation steps")

            steps = [
                "Confirm the affected source file or upstream table.",
                "Inspect sample records in the relevant pipeline layer.",
                "Validate the business rule with the data owner.",
                "Correct the source or transformation logic.",
                "Rerun the pipeline and verify the quality check.",
            ]

            for index, step in enumerate(steps, start=1):
                st.markdown(f"**{index}.** {step}")

            st.info(
                "These are recommended investigation steps, not an "
                "automated repair. Review business rules before modifying "
                "or deleting records."
            )

            report = (
                f"AI Data Quality Copilot - Investigation Report\n\n"
                f"Rule: {selected_check}\n"
                f"Status: FAIL\n"
                f"Reported failed records: "
                f"{safe_int(selected_row.get('failed_records', 0))}\n\n"
                f"Diagnostic guidance:\n{explain_check(selected_check)}\n\n"
                f"Recommended next steps:\n"
                + "\n".join(
                    f"{i}. {step}" for i, step in enumerate(steps, 1)
                )
            )

            st.download_button(
                "Download investigation report",
                data=report,
                file_name="quality_investigation.txt",
                mime="text/plain",
            )


# =========================================================
# System Health
# =========================================================

elif selected_page == "System Health":
    page_header(
        "System health",
        "Check API availability and connections to the data platform.",
        section="PLATFORM STATUS",
    )

    st.markdown(
        f'<div class="muted">API endpoint: {API_BASE_URL}</div>',
        unsafe_allow_html=True,
    )

    if st.button("Run health checks", type="primary"):
        st.cache_data.clear()
        st.rerun()

    api_health = load_health("/health")
    databricks_health = load_health("/databricks-health")

    services = [
        ("FastAPI / PostgreSQL", api_health),
        ("Databricks workspace", databricks_health),
    ]

    for service_name, result in services:
        is_healthy = (
            str(result.get("status", "")).lower()
            in {"healthy", "connected", "success"}
        )

        status_text = "HEALTHY" if is_healthy else "UNAVAILABLE"
        color = "#4ade80" if is_healthy else "#fb7185"

        st.markdown(
            f"""
            <div class="panel">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;gap:12px;">
                    <div class="panel-title">{service_name}</div>
                    <div style="color:{color};font-weight:800;
                                font-size:11px;">
                        ● {status_text}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"View details — {service_name}"):
            st.json(result)

    st.markdown("### Runtime configuration")
    st.write({
        "API base URL": API_BASE_URL,
        "Dashboard time": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "Refresh cache": "30 seconds",
    })

    st.caption(
        "A healthy response confirms the tested endpoint is reachable. "
        "It does not guarantee that every pipeline job or table is healthy."
    )


# =========================================================
# Footer
# =========================================================

st.markdown(
    """
    <div class="footer">
        AI DATA QUALITY COPILOT &nbsp;·&nbsp;
        DATABRICKS SQL &nbsp;·&nbsp; FASTAPI &nbsp;·&nbsp; STREAMLIT
        <br><br>
        Metrics are based on the latest available query results.
        Diagnostic recommendations require human validation.
    </div>
    """,
    unsafe_allow_html=True,
)
