import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import main
from backend.app import audit_logger
import json

client = TestClient(app)

def test_valid_year():
    response = client.get("/api/revenue/2025", params={"role": "analyst"})
    assert response.status_code == 200

    body = response.json()
    assert body["year"] == "2025"
    assert body["results"][0]["sector"] == "Technology"

def test_year_with_no_data():
    year = 2022
    response = client.get(f"/api/revenue/{year}", params={"role": "analyst"})
    assert response.status_code == 400

    body = response.json()
    assert body["detail"] == f"No revenue data found for year {year}"


@pytest.mark.parametrize(
    "sector_a, sector_b",
    [
        ("Healthcare", "Technology"),
        ("Industrials", "Consumer & Retail"),
    ],
)
def test_valid_sector(sector_a: str, sector_b: str):
    response = client.get(
        "/api/pipeline/compare",
        params={
            "sector_a": sector_a,
            "sector_b": sector_b,
            "role": "analyst",
        },
    )
    assert response.status_code == 200

    body = response.json()
    results_by_sector = {result["sector"]: result for result in body["results"]}
    assert sector_a in results_by_sector
    assert sector_b in results_by_sector


@pytest.mark.parametrize(
    "sector_a, sector_b",
    [
        ("Healthcare", " "),
        ("    ", "Consumer & Retail"),
    ],
)
def test_empty_sector(sector_a: str, sector_b: str):
    response = client.get(
        "/api/pipeline/compare",
        params={
            "sector_a": sector_a,
            "sector_b": sector_b,
            "role": "analyst",
        },
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"] == "Enter valid sectors"

@pytest.mark.parametrize(
    "sector_a, sector_b",
    [
        ("Healthcare", "Healthcare"),
        (" Consumer & Retail ", "Consumer & Retail"),
    ],
)
def test_same_sector(sector_a, sector_b):
    response = client.get(
        "/api/pipeline/compare",
        params={
            "sector_a": sector_a,
            "sector_b": sector_b,
            "role": "analyst",
        },
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"] == "Enter different sectors"


@pytest.mark.parametrize(
    "sector_a, sector_b, invalid_sector",
    [
        ("Healthcae", "Technology", "Healthcae"),
        ("IT", "Industrials", "IT"),
        ("Industrials", "IT", "IT")
    ],
)
def test_invalid_sector(sector_a, sector_b, invalid_sector):
    response = client.get(
        "/api/pipeline/compare",
        params={
            "sector_a": sector_a,
            "sector_b": sector_b,
            "role": "analyst",
        },
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"] == f"Sector {invalid_sector} is not among valid sectors"

def test_missing_sector_param_returns_422():
    response = client.get(
        "/api/pipeline/compare",
        params={"sector_a": "Healthcare", "role": "analyst"},
    )
    assert response.status_code == 422

def test_valid_sector_evidence():
    response = client.get(
        "/api/sectors/evidence",
        params = {
            "sector": "TechNology",
            "quarter": "2026q1",
            "role": "analyst",
        }
    )
    assert response.status_code == 200

    body = response.json()
    assert len(body["evidence"]) == 5
    assert body["evidence"]["revenue"]["current_total_revenue"] == pytest.approx(5.39)
    assert body["evidence"]["deals"]["delayed_or_withdrawn_count"] == 2
    assert body["evidence"]["pipeline"]["delayed_opportunities"] == 5
    assert body["evidence"]["market"]["volatility_index"] == pytest.approx(29.4)
    assert body["evidence"]["outlook"]["outlook_tone"] == "Negative"
    assert body["sector"] == "Technology"
    assert body["quarter"] == "2026Q1"

def test_invalid_sector_evidence():
    response = client.get(
        "/api/sectors/evidence",
        params={
            "sector": "Tech",
            "quarter": "2027Q1",
            "role": "analyst",
        }
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"] == "No available revenue data for Tech 2027Q1"

def test_document_search_valid_query():
    response = client.get(
        "/api/documents/search",
        params={"query": "Technology", "role": "senior_analyst"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["query"] == "Technology"
    assert "data_story_map.md" in body["sources"]
    assert body["match_count"] >= 1
    assert len(body["matches"]) >= 1
    assert body["matches"][0]["source"]
    assert "snippet" in body["matches"][0]

def test_document_search_case_insensitive():
    response = client.get(
        "/api/documents/search",
        params={"query": "technology", "role": "senior_analyst"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["match_count"] >= 1

def test_document_search_pdf_query():
    response = client.get(
        "/api/documents/search",
        params={"query": "sponsor-backed software", "role": "senior_analyst"},
    )
    body = response.json()

    assert response.status_code == 200
    assert "technology_2026q1_market_update.pdf" in body["sources"]
    pdf_matches = [
        match for match in body["matches"]
        if match["source"] == "technology_2026q1_market_update.pdf"
    ]
    assert pdf_matches
    assert pdf_matches[0]["page"] >= 1

def test_document_search_empty_query():
    response = client.get(
        "/api/documents/search",
        params={"query": " ", "role": "senior_analyst"},
    )
    body = response.json()

    assert response.status_code == 400
    assert body["detail"] == "Enter a valid search query"

def test_document_search_unknown_query():
    response = client.get(
        "/api/documents/search",
        params={"query": "banana spaceship", "role": "senior_analyst"},
    )
    body = response.json()

    assert response.status_code == 400
    assert body["detail"] == "banana spaceship not found in approved documents"

def test_analyst_sector_analysis_valid_request():
    response = client.get(
        "/api/analyst/sector-analysis",
        params={
            "sector": "TechNology",
            "quarter": "2026q1",
            "role": "analyst",
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["question_type"] == "sector_analysis"
    assert body["sector"] == "Technology"
    assert body["quarter"] == "2026Q1"
    assert len(body["evidence_bullets"]) == 5
    assert "Technology revenue declined sharply" in body["answer"]
    assert "96.7% quarter-over-quarter decline" in body["answer"]
    assert "supporting_evidence" in body
    assert body["supporting_evidence"]["evidence"]["deals"]["delayed_or_withdrawn_count"] == 2

def test_analyst_sector_analysis_invalid_sector_returns_400():
    response = client.get(
        "/api/analyst/sector-analysis",
        params={
            "sector": "Tech",
            "quarter": "2026Q1",
            "role": "analyst",
        },
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"] == "No available revenue data for Tech 2026Q1"

def test_analyst_sector_analysis_missing_param_returns_422():
    response = client.get(
        "/api/analyst/sector-analysis",
        params={"sector": "Technology", "role": "analyst"},
    )

    assert response.status_code == 422

def test_assistant_ask_revenue_question():
    response = client.get(
        "/api/assistant/ask",
        params={"question": "Which sectors generated the most revenue in 2025?", "role": "analyst"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["matched_intent"] == "revenue_ranking"
    assert body["tool_used"] == "generate_revenue_paragraph"
    assert body["result"]["year"] == "2025"
    assert body["result"]["question_type"] == "revenue_ranking"
    assert body["result"]["supporting_evidence"]["results"][0]["sector"] == "Technology"

def test_assistant_ask_pipeline_question():
    response = client.get(
        "/api/assistant/ask",
        params={"question": "Compare Healthcare and Industrials pipeline strength.", "role": "analyst"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["matched_intent"] == "pipeline_comparison"
    assert body["tool_used"] == "generate_pipeline_comparison_paragraph"
    assert body["result"]["compared_sectors"] == ["Healthcare", "Industrials"]

def test_assistant_ask_sector_analysis_question():
    response = client.get(
        "/api/assistant/ask",
        params={"question": "Why did Technology deal activity slow recently?", "role": "analyst"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["matched_intent"] == "sector_analysis"
    assert body["tool_used"] == "generate_summary_paragraph"
    assert body["result"]["sector"] == "Technology"
    assert body["result"]["quarter"] == "2026Q1"
    assert "Technology revenue declined sharply" in body["result"]["answer"]

def test_assistant_ask_empty_question():
    response = client.get(
        "/api/assistant/ask",
        params={"question": " ", "role": "analyst"},
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"]["message"] == "Enter a valid question."

def test_assistant_ask_unsupported_question():
    response = client.get(
        "/api/assistant/ask",
        params={"question": "What is the weather today?", "role": "analyst"},
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"]["message"] == (
        "Question type not supported. Ask about annual sector revenue, "
        "pipeline comparison, or sector analysis."
    )

def test_assistant_ask_missing_question_param_returns_422():
    response = client.get("/api/assistant/ask")

    assert response.status_code == 422

def test_assistant_ask_ai_sector_analysis_question(monkeypatch):
    from backend.app.tools import ai_response_tool

    def fake_call_open_ai(prompt):
        assert "Evidence bullets:" in prompt
        assert "Technology revenue declined sharply" in prompt
        return "Mock polished analyst answer from API test."

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={"question": "Why did Technology deal activity slow recently?", "role": "senior_analyst"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["matched_intent"] == "sector_analysis"
    assert body["answer_mode"] == "ai_polished"
    assert body["answer"] == "Mock polished analyst answer from API test."
    assert len(body["evidence_bullets"]) == 5
    assert "revenue_by_sector_quarter.csv" in body["sources"]

@pytest.mark.parametrize(
    "question, expected_intent, expected_answer",
    [
        (
            "Which sectors generated the most revenue in 2025?",
            "revenue_ranking",
            "Mock polished revenue answer.",
        ),
        (
            "Compare Healthcare and Industrials pipeline strength.",
            "pipeline_comparison",
            "Mock polished pipeline answer.",
        ),
    ],
)
def test_assistant_ask_ai_supports_revenue_and_pipeline(monkeypatch, question, expected_intent, expected_answer):
    from backend.app.tools import ai_response_tool

    def fake_call_open_ai(prompt):
        assert "Evidence bullets:" in prompt
        return expected_answer

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={"question": question, "role": "senior_analyst"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["matched_intent"] == expected_intent
    assert body["answer_mode"] == "ai_polished"
    assert body["answer"] == expected_answer
    assert body["sources"]
    assert body["limitations"]

def test_assistant_ask_ai_missing_question_param_returns_422():
    response = client.get("/api/assistant/ask-ai", params={"role": "senior_analyst"})

    assert response.status_code == 422

def test_assistant_ask_ai_falls_back_when_openai_fails(monkeypatch):
    from backend.app.tools import ai_response_tool

    def fake_call_open_ai(prompt):
        raise RuntimeError("fake OpenAI failure")

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={"question": "Why did Technology deal activity slow recently?", "role": "senior_analyst"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["answer_mode"] == "deterministic_fallback"
    assert body["answer"] == body["deterministic_answer"]
    assert "fake OpenAI failure" in body["ai_error"]

def test_assistant_ask_ai_with_documents(monkeypatch):
    from backend.app.tools import ai_response_tool

    def fake_generate_document_search_query(question):
        assert question == "Why did Technology deal activity slow recently?"
        return "Technology 2026Q1"

    def fake_retrieve_document_evidence(query):
        assert query == "Technology 2026Q1"
        return {
            "query": query,
            "sources": ["data_story_map.md"],
            "match_count": 1,
            "matches": [
                {
                    "source": "data_story_map.md",
                    "page": None,
                    "snippet": "Technology evidence guide excerpt.",
                }
            ],
            "limitations": ["Keyword search only; no semantic retrieval yet."],
        }

    def fake_call_open_ai(prompt):
        assert "Approved document excerpts:" in prompt
        assert "Technology evidence guide excerpt." in prompt
        return "Mock document-enhanced AI answer."

    monkeypatch.setattr(
        ai_response_tool,
        "_generate_document_search_query",
        fake_generate_document_search_query,
    )
    monkeypatch.setattr(
        ai_response_tool,
        "retrieve_document_evidence",
        fake_retrieve_document_evidence,
    )
    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={
            "question": "Why did Technology deal activity slow recently?",
            "role": "senior_analyst",
            "include_documents": True,
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["include_documents"] is True
    assert body["answer"] == "Mock document-enhanced AI answer."
    assert body["document_search"]["enabled"] is True
    assert body["document_search"]["query"] == "Technology 2026Q1"
    assert body["document_search"]["match_count"] == 1

def test_assistant_ask_ai_with_documents_requires_document_permission(monkeypatch):
    from backend.app.tools import ai_response_tool

    def fake_call_open_ai(prompt):
        return "This should not be called."

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={
            "question": "Why did Technology deal activity slow recently?",
            "role": "analyst",
            "include_documents": True,
        },
    )
    assert response.status_code == 403

    body = response.json()
    assert body["detail"]["error"] == "permission_denied"
    assert body["detail"]["role"] == "analyst"
    assert body["detail"]["required_permission"] == "document_search"

def test_assistant_ask_ai_with_documents_continues_when_document_search_fails(monkeypatch):
    from backend.app.tools import ai_response_tool

    def fake_generate_document_search_query(question):
        return "bad search phrase"

    def fake_retrieve_document_evidence(query):
        raise ValueError("bad search phrase not found in approved documents")

    def fake_call_open_ai(prompt):
        assert "Approved document excerpts:" not in prompt
        return "Mock answer after document search failed."

    monkeypatch.setattr(
        ai_response_tool,
        "_generate_document_search_query",
        fake_generate_document_search_query,
    )
    monkeypatch.setattr(
        ai_response_tool,
        "retrieve_document_evidence",
        fake_retrieve_document_evidence,
    )
    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={
            "question": "Why did Technology deal activity slow recently?",
            "role": "senior_analyst",
            "include_documents": True,
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["answer"] == "Mock answer after document search failed."
    assert body["document_search"]["enabled"] is True
    assert body["document_search"]["status"] == "failed"
    assert body["document_search"]["match_count"] == 0
    assert body["document_search"]["error"] == "No approved document excerpts matched attempted queries"

def test_assistant_ask_invalid_role_returns_400():
    response = client.get(
        "/api/assistant/ask",
        params={"question": "Which sectors generated the most revenue in 2025?", "role": "intern"},
    )
    assert response.status_code == 400

    body = response.json()
    assert body["detail"]["message"] == "Invalid role intern"

def test_assistant_ask_ai_analyst_forbidden():
    response = client.get(
        "/api/assistant/ask-ai",
        params={"question": "Why did Technology deal activity slow recently?", "role": "analyst"},
    )
    assert response.status_code == 403

    body = response.json()
    assert body["detail"]["request_id"]
    assert body["detail"]["error"] == "permission_denied"
    assert body["detail"]["role"] == "analyst"
    assert body["detail"]["required_permission"] == "ai_polishing"

def test_document_search_analyst_forbidden():
    response = client.get(
        "/api/documents/search",
        params={"query": "Technology", "role": "analyst"},
    )
    assert response.status_code == 403

    body = response.json()
    assert body["detail"]["request_id"]
    assert body["detail"]["error"] == "permission_denied"
    assert body["detail"]["role"] == "analyst"
    assert body["detail"]["required_permission"] == "document_search"

def test_admin_can_use_ai_endpoint(monkeypatch):
    from backend.app.tools import ai_response_tool

    def fake_call_open_ai(prompt):
        return "Mock admin AI answer."

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={"question": "Which sectors generated the most revenue in 2025?", "role": "admin"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["answer"] == "Mock admin AI answer."

def test_write_audit_log_writes_json_line(tmp_path, monkeypatch):
    temp_log_path = tmp_path / "audit_log.jsonl"

    monkeypatch.setattr(audit_logger, "AUDIT_PATH", temp_log_path)

    event = audit_logger.write_audit_log(
        request_id="request-1",
        endpoint="/api/assistant/ask",
        role="analyst",
        question="Which sectors generated the most revenue in 2025?",
        matched_intent="revenue_ranking",
        tool_used="generate_revenue_paragraph",
        answer_mode="deterministic",
        status="success",
    )

    lines = temp_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    saved_event = json.loads(lines[0])

    assert saved_event["request_id"] == "request-1"
    assert saved_event["status"] == "success"
    assert saved_event["timestamp"]

def test_success_calls_audit_logger(monkeypatch):
    captured_events = []

    def fake_write_audit_log(**kwargs):
        captured_events.append(kwargs)
        return kwargs

    monkeypatch.setattr(main, "write_audit_log", fake_write_audit_log)

    response = client.get(
        "/api/assistant/ask",
        params={
            "question": "Which sectors generated the most revenue in 2025?",
            "role": "analyst",
        },
    )

    assert response.status_code == 200
    assert len(captured_events) == 1
    assert captured_events[0]["status"] == "success"
    assert captured_events[0]["endpoint"] == "/api/assistant/ask"
    assert captured_events[0]["role"] == "analyst"
    assert captured_events[0]["matched_intent"] == "revenue_ranking"
    assert captured_events[0]["tool_used"] == "generate_revenue_paragraph"
    assert captured_events[0]["answer_mode"] == "deterministic"

def test_permission_denial_calls_audit_logger(monkeypatch):
    captured_events = []

    def fake_write_audit_log(**kwargs):
        captured_events.append(kwargs)
        return kwargs

    monkeypatch.setattr(main, "write_audit_log", fake_write_audit_log)

    response = client.get(
        "/api/assistant/ask-ai",
        params={
            "question": "Why did Technology deal activity slow recently?",
            "role": "analyst",
        },
    )

    assert response.status_code == 403
    assert len(captured_events) == 1
    assert captured_events[0]["status"] == "permission_denied"
    assert captured_events[0]["endpoint"] == "/api/assistant/ask-ai"
    assert captured_events[0]["role"] == "analyst"
    assert captured_events[0]["required_permission"] == "ai_polishing"

def test_validation_error_calls_audit_logger(monkeypatch):
    captured_events = []

    def fake_write_audit_log(**kwargs):
        captured_events.append(kwargs)
        return kwargs

    monkeypatch.setattr(main, "write_audit_log", fake_write_audit_log)

    response = client.get(
        "/api/assistant/ask",
        params={
            "question": "What is the weather today?",
            "role": "analyst",
        },
    )

    assert response.status_code == 400
    assert len(captured_events) == 1
    assert captured_events[0]["status"] == "validation_error"
    assert captured_events[0]["endpoint"] == "/api/assistant/ask"
    assert captured_events[0]["role"] == "analyst"
    assert "Question type not supported" in captured_events[0]["message"]

def test_ai_success_without_documents_audit_fields(monkeypatch):
    from backend.app.tools import ai_response_tool

    captured_events = []

    def fake_write_audit_log(**kwargs):
        captured_events.append(kwargs)
        return kwargs

    def fake_call_open_ai(prompt):
        return "Mock AI answer."

    monkeypatch.setattr(main, "write_audit_log", fake_write_audit_log)
    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={
            "question": "Which sectors generated the most revenue in 2025?",
            "role": "senior_analyst",
        },
    )

    assert response.status_code == 200
    assert len(captured_events) == 1
    assert captured_events[0]["include_documents"] is False
    assert captured_events[0]["document_search_status"] == "disabled"
    assert captured_events[0]["document_search_query"] is None
    assert captured_events[0]["answer_mode"] == "ai_polished"

def test_ai_success_with_documents_audit_fields(monkeypatch):
    from backend.app.tools import ai_response_tool

    captured_events = []

    def fake_write_audit_log(**kwargs):
        captured_events.append(kwargs)
        return kwargs

    def fake_generate_document_search_query(question):
        return "Technology 2026Q1"

    def fake_retrieve_document_evidence(query):
        return {
            "query": query,
            "sources": ["data_story_map.md"],
            "match_count": 1,
            "matches": [
                {
                    "source": "data_story_map.md",
                    "page": None,
                    "snippet": "Technology evidence snippet.",
                }
            ],
            "limitations": ["Keyword search only; no semantic retrieval yet."],
        }

    def fake_call_open_ai(prompt):
        return "Mock document-enhanced AI answer."

    monkeypatch.setattr(main, "write_audit_log", fake_write_audit_log)
    monkeypatch.setattr(
        ai_response_tool,
        "_generate_document_search_query",
        fake_generate_document_search_query,
    )
    monkeypatch.setattr(
        ai_response_tool,
        "retrieve_document_evidence",
        fake_retrieve_document_evidence,
    )
    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    response = client.get(
        "/api/assistant/ask-ai",
        params={
            "question": "Why did Technology deal activity slow recently?",
            "role": "senior_analyst",
            "include_documents": True,
        },
    )

    assert response.status_code == 200
    assert len(captured_events) == 1
    assert captured_events[0]["include_documents"] is True
    assert captured_events[0]["document_search_status"] == "success"
    assert captured_events[0]["document_search_query"] == "Technology 2026Q1"
    assert captured_events[0]["tool_used"] == "generate_summary_paragraph, get_documents_search"
