import pytest

from backend.app.tools.analyst_response_tool import (
    _classify_growth,
    _classify_market_conditions,
    _classify_pipeline_opportunities,
    _format_list_with_and,
    generate_pipeline_comparison_paragraph,
    generate_revenue_paragraph,
    generate_summary_paragraph,
)


def test_format_list_with_and():
    assert _format_list_with_and([]) == ""
    assert _format_list_with_and(['"A"']) == '"A"'
    assert _format_list_with_and(['"A"', '"B"']) == '"A" and "B"'
    assert _format_list_with_and(['"A"', '"B"', '"C"']) == '"A", "B", and "C"'


@pytest.mark.parametrize(
    "qoq_growth_pct, expected_classification",
    [
        (None, "missing_comparison"),
        (-96.7, "sharp_decline"),
        (-5.0, "modest_decline"),
        (0, "flat"),
        (4.5, "modest_growth"),
        (25.0, "strong_growth"),
    ],
)
def test_classify_growth(qoq_growth_pct, expected_classification):
    assert _classify_growth(qoq_growth_pct) == expected_classification


@pytest.mark.parametrize(
    "total_count, delay_count, expected_classification",
    [
        (None, 1, "missing_pipeline_count"),
        (0, 0, "missing_pipeline_count"),
        (10, None, "missing_delay_count"),
        (10, 0, "no_pressure"),
        (10, 2, "moderate_pressure"),
        (10, 4, "significant_pressure"),
    ],
)
def test_classify_pipeline_opportunities(total_count, delay_count, expected_classification):
    assert _classify_pipeline_opportunities(total_count, delay_count) == expected_classification


def test_classify_market_conditions_unfavorable():
    market = {
        "financing_condition": "Tight",
        "volatility_index": 29.4,
        "ipo_window_score": 34,
        "ma_confidence_score": 42,
    }

    assert _classify_market_conditions(market) == "unfavorable_conditions"


def test_generate_summary_paragraph_for_technology_slowdown():
    result = generate_summary_paragraph("TechNology", "2026q1")

    assert result["question_type"] == "sector_analysis"
    assert result["sector"] == "Technology"
    assert result["quarter"] == "2026Q1"

    assert len(result["evidence_bullets"]) == 5
    assert "\n\n" in result["answer"]

    assert "Technology revenue declined sharply" in result["answer"]
    assert "96.7% quarter-over-quarter decline" in result["answer"]
    assert "2 of 3 tracked Technology deals were delayed or withdrawn" in result["answer"]
    assert "5 of 12 tracked Technology pipeline opportunities were delayed" in result["answer"]
    assert "Market conditions were unfavorable for deal activity" in result["answer"]
    assert "Sector outlook reinforced downside pressure" in result["answer"]

    assert result["supporting_evidence"]["evidence"]["revenue"]["current_total_revenue"] == pytest.approx(5.39)
    assert result["supporting_evidence"]["evidence"]["pipeline"]["delayed_share_pct"] == pytest.approx(41.7)
    assert result["top_level_limitations"] == [
        "This evidence indicates association across revenue, deal, pipeline, market, and outlook signals, but does not prove causation."
    ]


def test_generate_revenue_paragraph():
    result = generate_revenue_paragraph(2025)

    assert result["question_type"] == "revenue_ranking"
    assert result["year"] == 2025
    assert "Technology generated the most revenue" in result["answer"]
    assert len(result["evidence_bullets"]) == 3
    assert "Technology generated the highest sector revenue" in result["evidence_bullets"][0]
    assert result["sources"] == ["revenue_by_sector_quarter.csv"]
    assert result["supporting_evidence"]["results"][0]["sector"] == "Technology"
    assert result["top_level_limitations"]


def test_generate_pipeline_comparison_paragraph():
    result = generate_pipeline_comparison_paragraph("Healthcare", "Industrials")

    assert result["question_type"] == "pipeline_comparison"
    assert result["compared_sectors"] == ["Healthcare", "Industrials"]
    assert "Healthcare had 10 pipeline opportunities" in result["answer"]
    assert "141.75" in result["answer"]
    assert len(result["evidence_bullets"]) == 3
    assert result["sources"] == ["pipeline_opportunities.csv"]
    assert result["supporting_evidence"]["results"][0]["sector"] in ["Healthcare", "Industrials"]
    assert result["top_level_limitations"]
