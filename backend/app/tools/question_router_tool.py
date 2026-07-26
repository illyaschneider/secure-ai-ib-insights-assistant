import re
from backend.app.tools.revenue_summary_tool import revenue_by_year
from backend.app.tools.pipeline_comparison_tool import pipeline_comparison
from backend.app.tools.analyst_response_tool import generate_summary_paragraph, generate_revenue_paragraph, generate_pipeline_comparison_paragraph

VALID_SECTORS = ["Technology", "Healthcare", "Industrials", "Consumer & Retail", "Energy", "Financial Institutions"]
DEFAULT_RECENT_QUARTER = "2026Q1"

def _extract_year(question: str):
    year_regex = r"(\d{4})"
    year_match = re.search(year_regex, question)
    if year_match:
        year = year_match.group()
    else:
        raise ValueError("Couldn't extract a year from the question. Try again.")
    return year

def _extract_quarter(question: str):
    quarter_regex = r"\b(\d{4}[qQ][1-4])\b"
    quarter_match = re.search(quarter_regex, question)

    if quarter_match:
        return quarter_match.group(1).upper()
    elif "recently" in question.casefold():
        return DEFAULT_RECENT_QUARTER
    else:
        raise ValueError("Couldn't extract a quarter from the question. Try again.")

def _extract_sectors(question: str):
    matched_sectors = []
    for sector in VALID_SECTORS:
        if sector.casefold() in question.casefold():
            matched_sectors.append(sector)
    return matched_sectors

def call_revenue_tool(question: str):
    year = _extract_year(question)
    return generate_revenue_paragraph(year)


def call_pipeline_comparison_tool(question: str):
    sector_list = _extract_sectors(question)
    if len(sector_list) == 2:
        sector1 = sector_list[0]
        sector2 = sector_list[1]
        return generate_pipeline_comparison_paragraph(sector1, sector2)
    elif len(sector_list) < 2:
        raise ValueError("Pipeline comparison requires exactly 2 valid sectors.")
    else:
        raise ValueError("Pipeline comparison supports exactly 2 sectors.")

def call_sector_analysis_tool(question: str):
    sector_list = _extract_sectors(question)
    quarter = _extract_quarter(question)
    if len(sector_list) == 1:
        sector = sector_list[0]
        return generate_summary_paragraph(sector, quarter)
    elif len(sector_list) > 1:
        raise ValueError("Too many sectors in your question for called tool. Input only 1 sector.")
    else:
        raise ValueError("Couldn't find any sectors in your question. Try again.")

def route_question(question):
    question = str(question).strip()

    if not question:
        raise ValueError("Enter a valid question.")

    normalized_question = question.casefold()

    if ("pipeline" in normalized_question and "compare" in normalized_question) or " vs " in normalized_question:
        result = call_pipeline_comparison_tool(question)
        return {
            "question": question,
            "matched_intent": "pipeline_comparison",
            "tool_used": "generate_pipeline_comparison_paragraph",
            "result": result,
            "limitations": ["Router uses simple keyword matching; no AI intent detection yet.",
                            "Revenue keyword currently maps to annual ranking rather than distinguishing ranking, trend, and causal questions."]
        }

    # Sector performance language maps to the deterministic analyst response generator.
    if "slow" in normalized_question or "weaken" in normalized_question or "decline" in normalized_question:
        result = call_sector_analysis_tool(question)
        return {
            "question": question,
            "matched_intent": "sector_analysis",
            "tool_used": "generate_summary_paragraph",
            "result": result,
            "limitations": ["Router uses simple keyword matching; no AI intent detection yet."]
        }

    # Revenue ranking currently supports questions only with an extractable year.
    if "revenue" in normalized_question:
        result = call_revenue_tool(question)
        return {
            "question": question,
            "matched_intent": "revenue_ranking",
            "tool_used": "generate_revenue_paragraph",
            "result": result,
            "limitations": ["Router uses simple keyword matching; no AI intent detection yet."]
        }

    raise ValueError(
        "Question type not supported. Ask about annual sector revenue, "
        "pipeline comparison, or sector analysis."
    )

def main():
    #question = "Which sectors generated the most revenue in 2025?"
    question = "Compare Healthcare and Industrials pipeline strength."
    #question = "Why did Technology deal activity slow recently?"

    #print(call_revenue_tool(question))
    #print(call_pipeline_comparison_tool(question))
    #print(call_analyst_response_tool(question))
    print(route_question(question))

if __name__ == '__main__':
    main()
