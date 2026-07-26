import pytest

from backend.app.tools.question_router_tool import (
    _extract_quarter,
    _extract_sectors,
    _extract_year,
    route_question,
)


def test_extract_year():
    assert _extract_year("Which sectors generated the most revenue in 2025?") == "2025"


def test_extract_year_missing():
    with pytest.raises(ValueError, match="Couldn't extract a year"):
        _extract_year("Which sectors generated the most revenue?")


@pytest.mark.parametrize(
    "question, expected_quarter",
    [
        ("Why did Technology slow in 2025q4?", "2025Q4"),
        ("Why did Technology deal activity slow recently?", "2026Q1"),
    ],
)
def test_extract_quarter(question, expected_quarter):
    assert _extract_quarter(question) == expected_quarter


def test_extract_quarter_missing():
    with pytest.raises(ValueError, match="Couldn't extract a quarter"):
        _extract_quarter("Why did Technology deal activity slow?")


@pytest.mark.parametrize(
    "question, expected_sectors",
    [
        ("Why did technology deal activity slow recently?", ["Technology"]),
        ("Compare Healthcare and Industrials pipeline strength.", ["Healthcare", "Industrials"]),
        (
            "Compare Consumer & Retail vs Financial Institutions pipeline strength.",
            ["Consumer & Retail", "Financial Institutions"],
        ),
    ],
)
def test_extract_sectors(question, expected_sectors):
    assert _extract_sectors(question) == expected_sectors


def test_route_revenue_question():
    result = route_question("Which sectors generated the most revenue in 2025?")

    assert result["matched_intent"] == "revenue_ranking"
    assert result["tool_used"] == "generate_revenue_paragraph"
    assert result["result"]["year"] == "2025"
    assert result["result"]["question_type"] == "revenue_ranking"
    assert "Technology generated the most revenue" in result["result"]["answer"]
    assert result["result"]["supporting_evidence"]["results"][0]["sector"] == "Technology"


def test_route_pipeline_question():
    result = route_question("Compare Healthcare and Industrials pipeline strength.")

    assert result["matched_intent"] == "pipeline_comparison"
    assert result["tool_used"] == "generate_pipeline_comparison_paragraph"
    assert result["result"]["compared_sectors"] == ["Healthcare", "Industrials"]
    assert result["result"]["question_type"] == "pipeline_comparison"
    assert len(result["result"]["supporting_evidence"]["results"]) == 2


def test_route_pipeline_vs_question():
    result = route_question("Consumer & Retail vs Financial Institutions pipeline strength.")

    assert result["matched_intent"] == "pipeline_comparison"
    assert result["result"]["compared_sectors"] == ["Consumer & Retail", "Financial Institutions"]


def test_route_sector_analysis_question():
    result = route_question("Why did Technology deal activity slow recently?")

    assert result["matched_intent"] == "sector_analysis"
    assert result["tool_used"] == "generate_summary_paragraph"
    assert result["result"]["sector"] == "Technology"
    assert result["result"]["quarter"] == "2026Q1"
    assert "Technology revenue declined sharply" in result["result"]["answer"]


def test_route_empty_question():
    with pytest.raises(ValueError, match="Enter a valid question"):
        route_question(" ")


def test_route_unsupported_question():
    with pytest.raises(ValueError, match="Question type not supported"):
        route_question("What is the weather today?")


def test_route_pipeline_requires_two_sectors():
    with pytest.raises(ValueError, match="Pipeline comparison requires exactly 2 valid sectors"):
        route_question("Compare Healthcare pipeline strength.")
