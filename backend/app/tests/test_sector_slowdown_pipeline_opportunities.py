from backend.app.tools.sector_evidence_tool import _get_pipeline_evidence
import pytest

@pytest.mark.parametrize(
    "sector, total_pipeline_opportunities, delayed_opportunities",
    [
        ("Technology", 12, 5)
    ]
)
def test_get_pipeline_evidence_ideal(sector, total_pipeline_opportunities, delayed_opportunities):
    result = _get_pipeline_evidence(sector)

    assert result["chosen_sector"] == sector
    assert result["total_pipeline_opportunities"] == total_pipeline_opportunities
    assert result["delayed_opportunities"] == delayed_opportunities
    assert result["source"] == "pipeline_opportunities.csv"
    assert result["delayed_share_pct"] == pytest.approx(41.7)

def test_invalid_sector():
    sector = "invalid_sector"
    with pytest.raises(ValueError, match = "No pipeline opportunities found for {}".format(sector)):
        _get_pipeline_evidence(sector)