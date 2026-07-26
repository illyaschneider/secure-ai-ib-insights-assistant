import pytest

from backend.app.tools import ai_response_tool
from backend.app.tools.question_router_tool import route_question


def test_build_ai_prompt_contains_controlled_evidence_sections():
    router_result = route_question("Why did Technology deal activity slow recently?")

    prompt = ai_response_tool._build_ai_prompt(router_result)

    assert "Question:" in prompt
    assert "Why did Technology deal activity slow recently?" in prompt
    assert "Evidence bullets:" in prompt
    assert "- Technology revenue declined sharply" in prompt
    assert "- Deal activity showed significant execution pressure" in prompt
    assert "- Pipeline activity showed significant delay pressure" in prompt
    assert "- Market conditions were unfavorable for deal activity" in prompt
    assert "- Sector outlook reinforced downside pressure" in prompt
    assert "Sources:" in prompt
    assert "- revenue_by_sector_quarter.csv" in prompt
    assert "- deals.csv" in prompt
    assert "Limitations:" in prompt
    assert "does not prove causation" in prompt
    assert "Write a concise analyst-style answer using only this evidence." in prompt


def test_polish_analyst_answer_uses_openai_call(monkeypatch):
    router_result = route_question("Why did Technology deal activity slow recently?")
    captured_prompt = {}

    def fake_call_open_ai(prompt):
        captured_prompt["prompt"] = prompt
        return "Mock polished analyst answer from test."

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    result = ai_response_tool.polish_analyst_answer(router_result)

    assert result["question"] == "Why did Technology deal activity slow recently?"
    assert result["matched_intent"] == "sector_analysis"
    assert result["answer_mode"] == "ai_polished"
    assert result["answer"] == "Mock polished analyst answer from test."
    assert "Technology revenue declined sharply" in result["deterministic_answer"]
    assert len(result["evidence_bullets"]) == 5
    assert "revenue_by_sector_quarter.csv" in result["sources"]
    assert "does not prove causation" in result["limitations"][0]
    assert "Evidence bullets:" in captured_prompt["prompt"]


@pytest.mark.parametrize(
    "question, expected_intent, expected_prompt_text",
    [
        (
            "Which sectors generated the most revenue in 2025?",
            "revenue_ranking",
            "Technology generated the highest sector revenue",
        ),
        (
            "Compare Healthcare and Industrials pipeline strength.",
            "pipeline_comparison",
            "Healthcare had 10 pipeline opportunities",
        ),
    ],
)
def test_polish_analyst_answer_supports_all_mvp_intents(
    monkeypatch,
    question,
    expected_intent,
    expected_prompt_text,
):
    router_result = route_question("Which sectors generated the most revenue in 2025?")
    router_result = route_question(question)
    captured_prompt = {}

    def fake_call_open_ai(prompt):
        captured_prompt["prompt"] = prompt
        return "Mock polished analyst answer."

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    result = ai_response_tool.polish_analyst_answer(router_result)

    assert result["matched_intent"] == expected_intent
    assert result["answer_mode"] == "ai_polished"
    assert result["answer"] == "Mock polished analyst answer."
    assert expected_prompt_text in captured_prompt["prompt"]
    assert result["sources"]
    assert result["limitations"]

def test_polish_analyst_answer_falls_back_when_openai_fails(monkeypatch):
    router_result = route_question("Why did Technology deal activity slow recently?")

    def fake_call_open_ai(prompt):
        raise RuntimeError("fake OpenAI failure")

    monkeypatch.setattr(ai_response_tool, "_call_open_ai", fake_call_open_ai)

    result = ai_response_tool.polish_analyst_answer(router_result)

    assert result["answer_mode"] == "deterministic_fallback"
    assert result["answer"] == result["deterministic_answer"]
    assert "fake OpenAI failure" in result["ai_error"]

def test_build_ai_prompt_includes_document_excerpts():
    router_result = route_question("Why did Technology deal activity slow recently?")
    document_result = {
        "matches": [
            {
                "source": "data_story_map.md",
                "page": None,
                "snippet": "Technology revenue fell sharply in 2026Q1.",
            },
            {
                "source": "technology_2026q1_market_update.pdf",
                "page": 2,
                "snippet": "Technology financing conditions tightened.",
            },
        ]
    }

    prompt = ai_response_tool._build_ai_prompt(
        router_result,
        document_result=document_result,
    )

    assert "Approved document excerpts:" in prompt
    assert "data_story_map.md" in prompt
    assert "technology_2026q1_market_update.pdf" in prompt
    assert "Technology revenue fell sharply in 2026Q1." in prompt
    assert "Technology financing conditions tightened." in prompt

def test_polish_analyst_answer_with_documents(monkeypatch):
    router_result = route_question("Why did Technology deal activity slow recently?")
    captured_prompt = {}

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
                    "snippet": "Technology showed weakness in 2026Q1.",
                }
            ],
            "limitations": ["Keyword search only; no semantic retrieval yet."],
        }

    def fake_call_open_ai(prompt):
        captured_prompt["prompt"] = prompt
        return "Mock polished answer using document evidence."

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

    result = ai_response_tool.polish_analyst_answer(
        router_result,
        include_documents=True,
    )

    assert result["answer_mode"] == "ai_polished"
    assert result["answer"] == "Mock polished answer using document evidence."
    assert result["document_search"]["enabled"] is True
    assert result["document_search"]["query"] == "Technology 2026Q1"
    assert result["document_search"]["match_count"] == 1
    assert result["document_search"]["sources"] == ["data_story_map.md"]
    assert "Approved document excerpts:" in captured_prompt["prompt"]
    assert "Technology showed weakness in 2026Q1." in captured_prompt["prompt"]

def test_polish_analyst_answer_continues_when_document_search_fails(monkeypatch):
    router_result = route_question("Why did Technology deal activity slow recently?")
    captured_prompt = {}

    def fake_generate_document_search_query(question):
        return "bad search phrase"

    def fake_retrieve_document_evidence(query):
        raise ValueError("bad search phrase not found in approved documents")

    def fake_call_open_ai(prompt):
        captured_prompt["prompt"] = prompt
        return "Mock polished answer without document evidence."

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

    result = ai_response_tool.polish_analyst_answer(
        router_result,
        include_documents=True,
    )

    assert result["answer_mode"] == "ai_polished"
    assert result["answer"] == "Mock polished answer without document evidence."
    assert result["document_search"]["enabled"] is True
    assert result["document_search"]["status"] == "failed"
    assert result["document_search"]["match_count"] == 0
    assert result["document_search"]["sources"] == []
    assert result["document_search"]["matches"] == []
    assert result["document_search"]["error"] == "No approved document excerpts matched attempted queries"
    assert "Approved document excerpts:" not in captured_prompt["prompt"]

def test_polish_analyst_answer_uses_fallback_document_query(monkeypatch):
    router_result = route_question("Why did Technology deal activity slow recently?")
    attempted_queries = []

    def fake_generate_document_search_query(question):
        return "bad search phrase"

    def fake_retrieve_document_evidence(query):
        attempted_queries.append(query)
        if query == "Technology 2026Q1":
            return {
                "query": query,
                "sources": ["data_story_map.md"],
                "match_count": 1,
                "matches": [
                    {
                        "source": "data_story_map.md",
                        "page": None,
                        "snippet": "Technology 2026Q1 fallback evidence.",
                    }
                ],
                "limitations": ["Keyword search only; no semantic retrieval yet."],
            }
        raise ValueError(f"{query} not found in approved documents")

    def fake_call_open_ai(prompt):
        assert "Technology 2026Q1 fallback evidence." in prompt
        return "Mock answer using fallback document query."

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

    result = ai_response_tool.polish_analyst_answer(
        router_result,
        include_documents=True,
    )

    assert result["answer"] == "Mock answer using fallback document query."
    assert result["document_search"]["status"] == "success"
    assert result["document_search"]["query"] == "Technology 2026Q1"
    assert result["document_search"]["attempted_queries"][0] == "bad search phrase"
    assert "Technology 2026Q1" in attempted_queries

def test_build_document_search_queries_deduplicates_ai_query():
    router_result = route_question("Why did Technology deal activity slow recently?")

    queries = ai_response_tool._build_document_search_queries(
        router_result,
        "Technology weakness",
    )

    assert queries.count("Technology weakness") == 1
    assert queries[0] == "Technology weakness"

def test_polish_analyst_answer_uses_fallback_when_query_generation_fails(monkeypatch):
    router_result = route_question("Why did Technology deal activity slow recently?")
    attempted_queries = []

    def fake_generate_document_search_query(question):
        raise RuntimeError("fake query generation failure")

    def fake_retrieve_document_evidence(query):
        attempted_queries.append(query)
        if query == "Technology 2026Q1":
            return {
                "query": query,
                "sources": ["data_story_map.md"],
                "match_count": 1,
                "matches": [
                    {
                        "source": "data_story_map.md",
                        "page": None,
                        "snippet": "Fallback worked after query generation failed.",
                    }
                ],
                "limitations": ["Keyword search only; no semantic retrieval yet."],
            }
        raise ValueError(f"{query} not found in approved documents")

    def fake_call_open_ai(prompt):
        assert "Fallback worked after query generation failed." in prompt
        return "Mock answer using deterministic document fallback."

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

    result = ai_response_tool.polish_analyst_answer(
        router_result,
        include_documents=True,
    )

    assert result["answer"] == "Mock answer using deterministic document fallback."
    assert result["document_search"]["status"] == "success"
    assert result["document_search"]["query"] == "Technology 2026Q1"
    assert result["document_search"]["attempted_queries"][0] == "Technology 2026Q1"
    assert result["document_search"]["error"] is None
    assert "Technology 2026Q1" in attempted_queries
