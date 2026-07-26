import pytest
from backend.app.tools.pipeline_comparison_tool import pipeline_comparison

def test_known_comparison():
    result = pipeline_comparison("Healthcare", "Industrials")
    results_by_sector = {
        row["sector"]: row
        for row in result["results"]
    }

    assert result["source"] == "pipeline_opportunities.csv"
    assert len(result["results"]) == 2

    assert results_by_sector["Healthcare"]["opportunity_count"] == 10
    assert results_by_sector["Industrials"]["opportunity_count"] == 8

    assert results_by_sector["Healthcare"]["total_weighted_fee"] == pytest.approx(141.75)
    assert results_by_sector["Industrials"]["total_weighted_fee"] == pytest.approx(67.16)

def test_mixed_case_input():
    result = pipeline_comparison("HEALTHCARE", "industrials")
    assert result["compared_sectors"] == ["Healthcare", "Industrials"]

def test_same_input():
    with pytest.raises(ValueError, match = "Enter different sectors"):
        pipeline_comparison("HEALTHCARE", "healthcare")

def test_unknown_sector_a():
    sector_a, sector_b = "IT", "Healthcare"
    with pytest.raises(ValueError, match = f"Sector {sector_a} is not among valid sectors"):
        pipeline_comparison(sector_a, sector_b)
def test_unknown_sector_b():
    sector_a, sector_b = "Healthcare", "IT"
    with pytest.raises(ValueError, match = f"Sector {sector_b} is not among valid sectors"):
        pipeline_comparison(sector_a, sector_b)

def test_empty_input():
    with pytest.raises(ValueError, match = "Enter valid sectors"):
        pipeline_comparison(" ", "Healthcare")

def test_pipeline_results_have_required_fields():
    result = pipeline_comparison("Healthcare", "Industrials")

    required_fields = {
        "sector",
        "opportunity_count",
        "total_deal_value",
        "total_expected_fee",
        "total_weighted_fee",
        "average_probability",
        "number_of_delayed_opportunities",
    }

    for row in result["results"]:
        assert required_fields.issubset(row.keys())
"""

@pytest.mark.parametrize(
    "sector_a, sector_b, invalid_sector",
    [
        ("IT", "Healthcare", "IT"),
        ("Healthcare", "IT", "IT"),
    ],
)
def test_rejects_unknown_sector(sector_a, sector_b, invalid_sector):
    with pytest.raises(
        ValueError,
        match=f"Sector {invalid_sector} is not among valid sectors",
    ):
        pipeline_comparison(sector_a, sector_b)
        
@pytest.mark.parametrize(
    "sector_a, sector_b",
    [
        ("", "Healthcare"),
        ("Healthcare", ""),
        ("   ", "Industrials"),
    ],
)
def test_rejects_empty_sector(sector_a, sector_b):
    with pytest.raises(ValueError, match="Enter valid sectors"):
        pipeline_comparison(sector_a, sector_b)

"""
