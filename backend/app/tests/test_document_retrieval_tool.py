import pytest
from backend.app.tools.document_retrieval_tool import retrieve_document_evidence

def test_retrieve_document_evidence():
    result = retrieve_document_evidence("Technology")

    assert result["query"] == "Technology"
    assert "data_story_map.md" in result["sources"]
    assert result["match_count"] >= 1
    assert len(result["matches"]) >= 1
    assert result["matches"][0]["source"]
    assert "snippet" in result["matches"][0]

def test_case_insensitive_search():
    result = retrieve_document_evidence("technology")

    assert result["match_count"] >= 1

def test_pdf_document_search():
    result = retrieve_document_evidence("sponsor-backed software")

    assert "technology_2026q1_market_update.pdf" in result["sources"]
    assert result["match_count"] >= 1
    pdf_matches = [
        match for match in result["matches"]
        if match["source"] == "technology_2026q1_market_update.pdf"
    ]
    assert pdf_matches
    assert pdf_matches[0]["page"] >= 1

def test_empty_query():
    with pytest.raises(ValueError, match="Enter a valid search query"):
        retrieve_document_evidence(" ")

def test_unknown_query():
    with pytest.raises(ValueError, match="not found"):
        retrieve_document_evidence("banana spaceship")
