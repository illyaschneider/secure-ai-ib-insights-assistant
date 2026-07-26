from backend.app.tools.revenue_summary_tool import revenue_by_year
import pytest

def test_year():
    result = revenue_by_year(2025)
    assert result["year"] == "2025"

def test_source():
    result = revenue_by_year(2025)
    assert result["source"] == "revenue_by_sector_quarter.csv"

def test_len_results():
    result = revenue_by_year(2025)
    assert len(result["results"]) == 6

def test_sorted_values():
    result = revenue_by_year(2025)
    revenues = [row["total_revenue_usd_mm"] for row in result["results"]]
    assert revenues == sorted(revenues, reverse=True)

def test_invalid_year_format():
    with pytest.raises(ValueError, match = "Year must contain exactly 4 digits"):
        revenue_by_year("hello")

def test_year_with_no_data():
    with pytest.raises(ValueError, match = "No revenue data found for year"):
        revenue_by_year(2035)

def test_order_in_results():
    result = revenue_by_year(2025)
    assert result["results"][0]["sector"] == "Technology"
    assert result["results"][0]["total_revenue_usd_mm"] == pytest.approx(509.8)

def test_query():
    result = revenue_by_year(2025)
    assert result["query_source"] == "SQLite"
    assert result["source_table"] == "revenue_by_sector_quarter"