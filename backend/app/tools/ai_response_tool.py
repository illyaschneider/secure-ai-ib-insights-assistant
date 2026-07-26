import os

from backend.app.tools.question_router_tool import route_question
from backend.app.tools.document_retrieval_tool import retrieve_document_evidence
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PLACEHOLDER_OPENAI_KEYS = {
    "",
    "your_openai_api_key_here",
    "your_real_key_here",
}

OPENAI_CALL_INSTRUCTIONS = (
            "You are an investment banking analyst assistant. "
            "Use only the provided evidence. "
            "Do not invent facts, numbers, sectors, quarters, or causes. "
            "If evidence is insufficient, say so. "
            "Write a concise analyst-style answer. "
        )
DOCUMENT_SEARCH_QUERY_INSTRUCTIONS = (
    "You generate short search phrases for approved internal document retrieval. "
    "Return only one search phrase. "
    "Do not answer the question. "
    "Do not explain your reasoning. "
    "Use 2 to 5 words when possible. "
    "Prefer exact sectors, years, quarters, and analytical concepts from the question. "
    "If the question says recently, use 2026Q1. "
    "Do not use punctuation unless it is part of a sector name such as Consumer & Retail."
)

def _require_real_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key in PLACEHOLDER_OPENAI_KEYS or api_key.casefold().startswith("your_"):
        raise ValueError("OPENAI_API_KEY is not configured with a real key")

def _build_ai_prompt(router_result, document_result=None):
    main_question = router_result["question"]
    evidence_bullets = router_result["result"]["evidence_bullets"]
    sources = router_result["result"]["sources"]
    limitations = router_result["result"]["top_level_limitations"]

    evidence_bullets_str = "\n".join(
        f"- {bullet}"
        for bullet in evidence_bullets
    )
    sources_str = "\n".join(
        f"- {source}"
        for source in sources
    )
    limitations_str = "\n".join(
        f"- {limit}"
        for limit in limitations
    )



    prompt = (
        f"Question:\n{main_question}\n\n"
        f"Evidence bullets:\n{evidence_bullets_str}\n\n"
    )

    if document_result:
        document_lines = []

        for match in document_result["matches"]:
            document_lines.append(
                f"- Source: {match['source']}, page: {match['page']}, snippet: {match['snippet']}"
            )

        document_text = "\n".join(document_lines)
        prompt += f"Approved document excerpts:\n{document_text}\n\n"
    prompt += (f"Sources:\n{sources_str}\n\n"
            f"Limitations:\n{limitations_str}\n\n"
            "Task:\n"
            "Write a concise analyst-style answer using only this evidence.\n")

    return prompt

def _generate_document_search_query(question):
    question = str(question).strip()
    prompt = (
        f"Given this analyst question, produce one short search phrase for searching approved internal documents. "
        f"Return only the search phrase. "
        f"Do not answer the question. "
        f"Do not include punctuation. "
        f"Example: Which sectors generated the most revenue in 2025? → revenue in 2025 "
        f"Question: {question} "
    )
    search_query = _call_open_ai_for_document_search_query(prompt)
    return search_query.strip()


def _call_open_ai(prompt):
    _require_real_openai_api_key()
    client = OpenAI()
    
    response = client.responses.create(
        model = "gpt-4.1-mini",
        instructions = OPENAI_CALL_INSTRUCTIONS,
        input = prompt
    )

    return response.output_text

def _call_open_ai_for_document_search_query(prompt):
    _require_real_openai_api_key()
    client = OpenAI()

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=DOCUMENT_SEARCH_QUERY_INSTRUCTIONS,
        input=prompt,
    )

    return response.output_text

def _build_document_search_queries(router_result, ai_generated_query):
    queries = []

    if ai_generated_query:
        queries.append(ai_generated_query)

    if router_result["matched_intent"] == "sector_analysis":
        sector = router_result["result"]["sector"]
        quarter = router_result["result"]["quarter"]

        queries.append(f"{sector} {quarter}")
        queries.append(f"{sector} weakness")
        queries.append("valuation gap")
    elif router_result["matched_intent"] == "revenue_ranking":
        year = router_result["result"]["year"]

        queries.append(f"{year} revenue")
        queries.append(f"{year} Sector Revenue Ranking")
    elif router_result["matched_intent"] == "pipeline_comparison":
        sector_a = router_result["result"]["compared_sectors"][0]
        sector_b = router_result["result"]["compared_sectors"][1]

        queries.append(f"{sector_a} Versus {sector_b} Pipeline Strength")
        queries.append("pipeline strength")

    return list(dict.fromkeys(queries))

def polish_analyst_answer(router_result, include_documents=False):
    if router_result["matched_intent"] not in ["sector_analysis", "revenue_ranking", "pipeline_comparison"]:
        raise ValueError(
            "AI polishing currently supports only sector analysis, revenue ranking, and pipeline comparison answers")


    document_result = None
    document_search = {
        "enabled": False,
    }

    if include_documents:
        document_search = {
            "enabled": True,
            "status": "failed",
            "query": None,
            "match_count": 0,
            "sources": [],
            "matches": [],
            "error": None,
        }

        query_generation_error = None

        try:
            ai_search_query = _generate_document_search_query(router_result["question"])
        except Exception as error:
            ai_search_query = None
            query_generation_error = str(error)

        search_queries = _build_document_search_queries(router_result, ai_search_query)
        document_search["attempted_queries"] = search_queries

        try:
            document_result = None

            for search_query in search_queries:
                try:
                    document_result = retrieve_document_evidence(search_query)

                    document_search = {
                        "enabled": True,
                        "status": "success",
                        "query": search_query,
                        "attempted_queries": search_queries,
                        "match_count": document_result["match_count"],
                        "sources": document_result["sources"],
                        "matches": document_result["matches"],
                        "error": None,
                    }

                    break

                except ValueError:
                    continue

            if document_result is None:
                document_search["error"] = "No approved document excerpts matched attempted queries"
                if query_generation_error:
                    document_search["query_generation_error"] = query_generation_error

        except Exception as error:
            document_result = None
            document_search["error"] = str(error)
            if query_generation_error:
                document_search["query_generation_error"] = query_generation_error

    combined_sources = list(router_result["result"]["sources"])

    if document_result:
        combined_sources.extend(document_result["sources"])

    combined_sources = list(dict.fromkeys(combined_sources))

    prompt = _build_ai_prompt(router_result, document_result=document_result)

    try:
        polished_answer = _call_open_ai(prompt)
        answer_mode = "ai_polished"
        ai_error = None
    except Exception as error:
        polished_answer = router_result["result"]["answer"]
        answer_mode = "deterministic_fallback"
        ai_error = str(error)

    response_dict = {
        "question": router_result["question"],
        "matched_intent": router_result["matched_intent"],
        "answer_mode": answer_mode,
        "answer": polished_answer,
        "deterministic_answer": router_result["result"]["answer"],
        "evidence_bullets": router_result["result"]["evidence_bullets"],
        "include_documents": include_documents,
        "document_search": document_search,
        "approved_document_excerpts": document_result,
        "supporting_evidence": router_result["result"]["supporting_evidence"],
        "sources": combined_sources,
        "limitations": router_result["result"]["top_level_limitations"],
        "ai_error": ai_error,
    }

    return response_dict


def main():
    #question = "Why did Technology deal activity slow recently?"
    #question = "Compare Healthcare and Industrials pipeline strength."
    question = "Which sectors generated the most revenue in 2025?"
    router_result = route_question(question)
    result = polish_analyst_answer(router_result)

    print(result["answer"])

if __name__ == "__main__":
    main()
