from backend.app.tools.sector_evidence_tool import get_sector_evidence
import pytest


def test_get_sector_evidence():
    sector = "TeChnology"
    quarter = "2026q1"
    result = get_sector_evidence(sector, quarter)

    assert len(result["evidence"]) == 5
    assert result["evidence"]["revenue"]["current_total_revenue"] == pytest.approx(5.39)
    assert result["evidence"]["deals"]["delayed_or_withdrawn_count"] == 2
    assert result["evidence"]["pipeline"]["delayed_opportunities"] == 5
    assert result["evidence"]["market"]["volatility_index"] == pytest.approx(29.4)
    assert result["evidence"]["outlook"]["outlook_tone"] == "Negative"
    assert result["sector"] == "Technology"
    assert result["quarter"] == "2026Q1"