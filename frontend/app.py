import os

import altair as alt
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

st.set_page_config(
    page_title="IB Insights Assistant",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)


def set_question(text):
    st.session_state.question_text = text


def clear_all():
    st.session_state.question_text = ""
    st.session_state.assistant_response = None


def _get_assistant_payload(body):
    if "result" in body:
        return body["result"]
    return body


def _get_supporting_evidence(body):
    payload = _get_assistant_payload(body)
    return payload.get("supporting_evidence")


def _vertical_bar_chart(df, x_column, y_column, title, color="#38bdf8"):
    chart_df = df.copy()
    chart_df[y_column] = pd.to_numeric(chart_df[y_column])

    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=color)
        .encode(
            x=alt.X(f"{x_column}:N", sort="-y", title=None),
            y=alt.Y(f"{y_column}:Q", title=None),
            tooltip=[
                alt.Tooltip(f"{x_column}:N", title=x_column.replace("_", " ").title()),
                alt.Tooltip(f"{y_column}:Q", title=y_column.replace("_", " ").title()),
            ],
        )
    )

    labels = (
        alt.Chart(chart_df)
        .mark_text(align="center", baseline="bottom", dy=-6, color="white")
        .encode(
            x=alt.X(f"{x_column}:N", sort="-y"),
            y=alt.Y(f"{y_column}:Q"),
            text=alt.Text(f"{y_column}:Q", format=".2f"),
        )
    )

    chart = (
        (bars + labels)
        .properties(title=title, height=320)
        .configure_axis(labelAngle=0)
    )
    st.altair_chart(chart, use_container_width=True)


def _metric_table(df):
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def _render_revenue_chart(evidence):
    results = evidence["results"]
    chart_df = pd.DataFrame(results)
    top_sector = chart_df.iloc[0]

    st.subheader("Revenue by sector")
    st.metric(
        label="Top revenue sector",
        value=top_sector["sector"],
        delta=f"{top_sector['total_revenue_usd_mm']} {evidence['unit']}",
    )
    _vertical_bar_chart(
        chart_df,
        x_column="sector",
        y_column="total_revenue_usd_mm",
        title=f"Sector revenue ranking, {evidence['year']}",
    )
    _metric_table(chart_df)


def _render_pipeline_chart(evidence):
    results = evidence["results"]
    chart_df = pd.DataFrame(results)

    st.subheader("Pipeline comparison")

    stronger_sector = chart_df.sort_values("total_weighted_fee", ascending=False).iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Stronger weighted-fee pipeline",
            stronger_sector["sector"],
            f"{stronger_sector['total_weighted_fee']} {evidence['unit']}",
        )
    with col2:
        st.metric(
            "Total opportunities",
            int(chart_df["opportunity_count"].sum()),
        )
    with col3:
        st.metric(
            "Average probability range",
            f"{chart_df['average_probability'].min()} - {chart_df['average_probability'].max()}",
        )

    metric_choice = st.selectbox(
        "Choose pipeline metric",
        [
            "total_weighted_fee",
            "opportunity_count",
            "total_expected_fee",
            "average_probability",
            "number_of_delayed_opportunities",
        ],
    )

    _vertical_bar_chart(
        chart_df,
        x_column="sector",
        y_column=metric_choice,
        title=f"Pipeline comparison by {metric_choice.replace('_', ' ')}",
    )
    _metric_table(chart_df)


def _render_sector_evidence_charts(evidence):
    sector_evidence = evidence["evidence"]
    revenue = sector_evidence["revenue"]
    deals = sector_evidence["deals"]
    pipeline = sector_evidence["pipeline"]

    st.subheader("Sector evidence snapshot")

    revenue_df = pd.DataFrame(
        {
            "quarter": [revenue["previous_quarter"], revenue["current_quarter"]],
            "revenue": [revenue["previous_total_revenue"], revenue["current_total_revenue"]],
        }
    ).dropna()

    delay_df = pd.DataFrame(
        {
            "category": ["Delayed/withdrawn deals", "Delayed pipeline opportunities"],
            "count": [deals["delayed_or_withdrawn_count"], pipeline["delayed_opportunities"]],
        }
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Current revenue",
            f"{revenue['current_total_revenue']} {revenue['revenue_unit']}",
            f"{revenue['qoq_growth_pct']}% QoQ" if revenue["qoq_growth_pct"] is not None else None,
        )
    with col2:
        st.metric(
            "Delayed/withdrawn deals",
            f"{deals['delayed_or_withdrawn_count']} of {deals['total_deals']}",
        )
    with col3:
        st.metric(
            "Delayed pipeline",
            f"{pipeline['delayed_opportunities']} of {pipeline['total_pipeline_opportunities']}",
            f"{pipeline['delayed_share_pct']}%",
        )

    col1, col2 = st.columns(2)
    with col1:
        _vertical_bar_chart(
            revenue_df,
            x_column="quarter",
            y_column="revenue",
            title="Quarterly revenue comparison",
        )
    with col2:
        _vertical_bar_chart(
            delay_df,
            x_column="category",
            y_column="count",
            title="Execution pressure",
            color="#f97316",
        )

    detail_df = pd.DataFrame(
        [
            {
                "metric": "Financing condition",
                "value": sector_evidence["market"]["financing_condition"],
            },
            {
                "metric": "Valuation environment",
                "value": sector_evidence["market"]["valuation_environment"],
            },
            {
                "metric": "Outlook tone",
                "value": sector_evidence["outlook"]["outlook_tone"],
            },
            {
                "metric": "Risk level",
                "value": sector_evidence["outlook"]["risk_level"],
            },
        ]
    )
    _metric_table(detail_df)


def render_charts(body):
    payload = _get_assistant_payload(body)
    evidence = _get_supporting_evidence(body)
    matched_intent = body.get("matched_intent") or payload.get("question_type")

    if not evidence:
        return

    with st.expander("Charts", expanded=True):
        if matched_intent == "revenue_ranking":
            _render_revenue_chart(evidence)
        elif matched_intent == "pipeline_comparison":
            _render_pipeline_chart(evidence)
        elif matched_intent == "sector_analysis":
            _render_sector_evidence_charts(evidence)
        else:
            st.info("No chart available for this response type yet.")


def render_success_response(body, use_ai):
    st.success("Response received")
    st.caption(f"Request ID: {body.get('request_id')}")
    if use_ai:
        st.caption(f"Answer mode: {body.get('answer_mode')}")
    else:
        st.caption("Answer mode: deterministic")

    st.subheader("Answer")
    payload = _get_assistant_payload(body)
    st.write(body["answer"] if use_ai else payload["answer"])

    render_charts(body)

    if use_ai:
        with st.expander("Deterministic fallback answer"):
            st.write(body["deterministic_answer"])

        evidence_bullets = body["evidence_bullets"]
        sources = body["sources"]
        limitations = body["limitations"]

        if body.get("ai_error"):
            st.warning(body["ai_error"])

        document_search = body.get("document_search", {})

        if document_search.get("enabled"):
            with st.expander("Approved document evidence", expanded=False):
                if document_search.get("status") == "success":
                    st.success(
                        f"Document search found "
                        f"{document_search.get('match_count', 0)} matches."
                    )
                    st.caption(
                        f"Search query used: "
                        f"{document_search.get('query', '')}"
                    )
                else:
                    st.warning("Document search did not return supporting evidence.")
                    st.caption(document_search.get("error", "Unknown retrieval error"))

                attempted_queries = document_search.get("attempted_queries", [])
                if attempted_queries:
                    st.caption(
                        "Attempted queries: "
                        + ", ".join(attempted_queries)
                    )

                for match in document_search.get("matches", []):
                    page = match.get("page")
                    page_label = f", page {page}" if page is not None else ""

                    st.markdown(
                        f"**{match.get('source', 'Unknown source')}{page_label}**"
                    )
                    st.write(match.get("snippet", ""))
    else:
        evidence_bullets = payload["evidence_bullets"]
        sources = payload["sources"]
        limitations = payload["top_level_limitations"]

        with st.expander("Raw routed response"):
            st.json(body)

    with st.expander("Evidence bullets"):
        for bullet in evidence_bullets:
            st.write(f"- {bullet}")

    with st.expander("Sources"):
        for source in sources:
            st.write(f"- {source}")

    with st.expander("Limitations"):
        for limitation in limitations:
            st.write(f"- {limitation}")


if "question_text" not in st.session_state:
    st.session_state.question_text = "Why did Technology deal activity slow recently?"

if "assistant_response" not in st.session_state:
    st.session_state.assistant_response = None


st.title("Secure AI Investment Banking Insights Assistant")
st.write(
    "Ask controlled questions about fictional investment banking revenue, "
    "pipeline strength, and sector activity."
)

role = st.selectbox(
    "Role",
    ["analyst", "senior_analyst", "admin"],
)

ai_allowed = role in {"senior_analyst", "admin"}

use_ai = st.checkbox(
    label="Use AI-polished answer",
    value=False,
    disabled=not ai_allowed,
)
include_documents = st.checkbox(
    label="Include approved document evidence",
    value=False,
    disabled=not use_ai or not ai_allowed,
)

if not ai_allowed:
    st.caption(
        "AI polishing and document retrieval require senior_analyst or admin access."
    )

question = st.text_area(
    label="Question",
    key="question_text",
    height=100,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.button(
        "Revenue Question",
        on_click=set_question,
        args=("Which sectors generated the most revenue in 2025?",),
    )

with col2:
    st.button(
        "Pipeline Question",
        on_click=set_question,
        args=("Compare Healthcare and Industrials pipeline strength.",),
    )

with col3:
    st.button(
        "Slowdown Question",
        on_click=set_question,
        args=("Why did Technology deal activity slow recently?",),
    )

st.button("Clear", on_click=clear_all)

if st.button("Ask assistant"):
    endpoint = "/api/assistant/ask-ai" if use_ai else "/api/assistant/ask"
    params = {
        "question": question,
        "role": role,
    }

    if use_ai:
        params["include_documents"] = include_documents

    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=30,
        )

        body = response.json()
        st.session_state.assistant_response = {
            "status_code": response.status_code,
            "body": body,
            "use_ai": use_ai,
        }
        
    except requests.exceptions.RequestException as error:
        st.session_state.assistant_response = {
            "status_code": None,
            "body": {
                "error": "connection_error",
                "message": str(error),
            },
            "use_ai": use_ai,
        }

if st.session_state.assistant_response:
    saved_response = st.session_state.assistant_response
    saved_body = saved_response["body"]

    if saved_response["status_code"] == 200:
        render_success_response(saved_body, saved_response["use_ai"])
    elif saved_response["status_code"] is None:
        st.error("Could not connect to the FastAPI backend.")
        st.write(saved_body["message"])
    else:
        st.error(f"Request failed with status {saved_response['status_code']}")
        st.json(saved_body)




# streamlit run frontend/app.py --server.address 0.0.0.0
