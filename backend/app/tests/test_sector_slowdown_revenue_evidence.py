from backend.app.tools.sector_evidence_tool import _get_revenue_evidence
import pytest

@pytest.mark.parametrize(
    "sector, quarter, current_total_revenue",
    [
        ("Technology", "2026Q1", 5.39),
        ("Healthcare", "2024Q2", 9.46),
        ("Industrials", "2025Q3", 65.3),
    ]
)
def test_current_data(sector, quarter, current_total_revenue):
    result = _get_revenue_evidence(sector, quarter)

    assert result["chosen_sector"] == sector
    assert result["current_quarter"] == quarter
    assert result["current_total_revenue"] == pytest.approx(current_total_revenue)


@pytest.mark.parametrize(
    "sector, quarter, previous_quarter, previous_total_revenue",
    [
        ("Technology", "2026Q1", "2025Q4", 162.89),
        ("Healthcare", "2024Q2", "2024Q1", None),
        ("Industrials", "2025Q3", "2025Q2", 78.3),
    ]
)
def test_previous_data(sector, quarter, previous_quarter, previous_total_revenue):
    result = _get_revenue_evidence(sector, quarter)

    assert result["previous_quarter"] == pytest.approx(previous_quarter)
    assert result["previous_total_revenue"] == pytest.approx(previous_total_revenue)


@pytest.mark.parametrize(
    "sector, quarter, absolute_change, qoq_growth",
    [
        ("Technology", "2026Q1", -157.5, -96.7),
        ("Healthcare", "2024Q2", None, None),
        ("Industrials", "2025Q3", -13.0, -16.6),
    ]
)
def test_calculations(sector, quarter, absolute_change, qoq_growth):
    result = _get_revenue_evidence(sector, quarter)

    assert result["absolute_change"] == pytest.approx(absolute_change)
    assert result["qoq_growth_pct"] == pytest.approx(qoq_growth)

@pytest.mark.parametrize(
    "sector, quarter",
    [
        ("Technolog", "2026Q1"),
        ("Healthre", "2024Q2"),
        ("Industrial", "2025Q3"),
    ]
)
def test_invalid_sector(sector, quarter):
    with pytest.raises(ValueError, match = f"No available revenue data for {sector}"):
        _get_revenue_evidence(sector, quarter)


@pytest.mark.parametrize(
    "sector, quarter",
    [
        ("Technology", "22026Q1"),
        ("Healthcare", "2023 Q2"),
        ("Industrials", "2025Q5"),
    ]
)
def test_invalid_quarter(sector, quarter):
    with pytest.raises(ValueError, match="Quarter must use format YYYYQ#"):
        _get_revenue_evidence(sector, quarter)

@pytest.mark.parametrize(
    "sector, quarter",
    [
        ("Technology", "2026Q2"),
        ("Healthcare", "2023Q3"),
        ("Industrials", "2020Q2"),
    ]
)
def test_unavailable_quarter(sector, quarter):
    with pytest.raises(ValueError, match=f"No available revenue data for {sector} {quarter}"):
        _get_revenue_evidence(sector, quarter)
