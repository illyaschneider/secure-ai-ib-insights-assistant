from backend.app.tools.sector_evidence_tool import get_sector_evidence
from backend.app.tools.revenue_summary_tool import revenue_by_year
from backend.app.tools.pipeline_comparison_tool import pipeline_comparison

def _format_list_with_and(items):
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _classify_growth(qoq_growth_pct):
    if qoq_growth_pct is None:
        return "missing_comparison"
    if qoq_growth_pct < -10:
        return "sharp_decline"
    if qoq_growth_pct < 0:
        return "modest_decline"
    if qoq_growth_pct == 0:
        return "flat"
    if qoq_growth_pct <= 10:
        return "modest_growth"
    return "strong_growth"

def _build_revenue_verdict(classification):
    revenue_tone_by_signal = {
        "missing_comparison": "missing comparison",
        "sharp_decline": "declined sharply",
        "modest_decline": "declined modestly",
        "flat": "was broadly flat",
        "modest_growth": "increased modestly",
        "strong_growth": "increased strongly",
    }
    return revenue_tone_by_signal[classification]

def _build_revenue_sentence(revenue, sector):
    classification = _classify_growth(revenue["qoq_growth_pct"])
    revenue_verdict = _build_revenue_verdict(classification)
    if revenue["previous_total_revenue"] is None:
        return (f"{sector} revenue was {revenue['current_total_revenue']} {revenue['revenue_unit']} in {revenue['current_quarter']},"
                f" but prior-quarter revenue was unavailable.")
    else:
        revenue_sentence = (
            f"{sector} revenue {revenue_verdict} from "
            f"{revenue['previous_total_revenue']} {revenue['revenue_unit']} in {revenue['previous_quarter']} "
            f"to {revenue['current_total_revenue']} {revenue['revenue_unit']} in {revenue['current_quarter']}, "
        )
        if revenue["qoq_growth_pct"] > 0:
            revenue_sentence += f"a {abs(revenue['qoq_growth_pct'])}% quarter-over-quarter increase."
        else:
            revenue_sentence += f"a {abs(revenue['qoq_growth_pct'])}% quarter-over-quarter decline."
    return revenue_sentence


def _classify_deal_pressure(total_count, delay_count):
    if total_count is None or total_count == 0:
        return "missing_deals_count"
    if delay_count is None:
        return "missing_delay_count"
    if (delay_count / total_count) < 0.4:
        return "moderate_pressure"
    return "significant_pressure"

def _build_deals_verdict(classification, sector):
    deals_tone_by_signal = {
        "missing_deals_count": f"No tracked deals for {sector} were found for the quarter, so deal-level evidence is unavailable.",
        "missing_delay_count": "Deal activity showed no execution pressure:",
        "moderate_pressure": "Deal activity showed moderate execution pressure:",
        "significant_pressure": "Deal activity showed significant execution pressure:"
    }
    return deals_tone_by_signal[classification]

def _build_deals_sentence(deals, sector):
    classification = _classify_deal_pressure(deals["total_deals"], deals["delayed_or_withdrawn_count"])
    deals_verdict = _build_deals_verdict(classification, sector)
    if classification == "missing_deals_count":
        return deals_verdict
    delay_reasons = [row["delay_or_loss_reason"] for row in deals["delay_evidence"]]
    unique_delay_reasons = list(dict.fromkeys(delay_reasons))
    quoted_reasons = [f'"{reason}"'for reason in unique_delay_reasons]
    formatted_reasons = _format_list_with_and(quoted_reasons)
    deals_sentence = (
        f"{deals_verdict} {deals['delayed_or_withdrawn_count']} of {deals['total_deals']} tracked {sector} deals were delayed or withdrawn."
        f" The main deal delay reasons included {formatted_reasons}."
    )
    return deals_sentence


def _classify_pipeline_opportunities(total_count, delay_count):
    if total_count is None or total_count == 0:
        return "missing_pipeline_count"
    if delay_count is None:
        return "missing_delay_count"
    if delay_count == 0:
        return "no_pressure"
    if (delay_count / total_count) < 0.4:
        return "moderate_pressure"
    return "significant_pressure"

def _build_pipeline_verdict(classification, sector):
    pipeline_tone_by_signal = {
        "missing_pipeline_count": f"No tracked pipeline opportunities for {sector} were found, so pipeline-level evidence is unavailable.",
        "missing_delay_count": "Pipeline evidence was incomplete because delayed opportunity count was unavailable.",
        "no_pressure": "Pipeline activity showed limited delay pressure:",
        "moderate_pressure": "Pipeline activity showed moderate delay pressure:",
        "significant_pressure": "Pipeline activity showed significant delay pressure:",
    }
    return pipeline_tone_by_signal[classification]

def _build_pipeline_sentence(pipeline, sector):
    classification = _classify_pipeline_opportunities(
        pipeline["total_pipeline_opportunities"],
        pipeline["delayed_opportunities"],
    )
    pipeline_verdict = _build_pipeline_verdict(classification, sector)
    if classification == "missing_pipeline_count":
        return pipeline_verdict

    pipeline_sentence = (
        f"{pipeline_verdict} {pipeline['delayed_opportunities']} of "
        f"{pipeline['total_pipeline_opportunities']} tracked {sector} pipeline opportunities "
        f"were delayed, representing {pipeline['delayed_share_pct']}% of the sector pipeline."
    )
    delay_reasons = [
        row["delay_reason"]
        for row in pipeline["delay_evidence"]
    ]
    unique_delay_reasons = list(dict.fromkeys(delay_reasons))
    quoted_reasons = [f'"{reason}"'for reason in unique_delay_reasons]
    formatted_reasons = _format_list_with_and(quoted_reasons)
    if delay_reasons:
        pipeline_sentence += f" The main pipeline delay reasons included {formatted_reasons}."
    return pipeline_sentence


def _classify_market_conditions(market):
    financing = market["financing_condition"]
    volatility = market["volatility_index"]
    ipo_score = market["ipo_window_score"]
    ma_score = market["ma_confidence_score"]

    if (
        financing == "Tight"
        or volatility >= 25
        or ipo_score < 40
        or ma_score < 45
    ):
        return "unfavorable_conditions"

    if (
        financing == "Supportive"
        and volatility < 18
        and ipo_score >= 60
        and ma_score >= 60
    ):
        return "favorable_conditions"

    return "mixed_conditions"

def _build_market_verdict(classification):
    market_tone_by_signal = {
        "unfavorable_conditions": "Market conditions were unfavorable for deal activity:",
        "mixed_conditions": "Market conditions were mixed for deal activity:",
        "favorable_conditions": "Market conditions were favorable for deal activity:",
    }
    return market_tone_by_signal[classification]

def _build_market_sentence(market):
    classification = _classify_market_conditions(market)
    market_verdict = _build_market_verdict(classification)
    market_sentence = (
        f'{market_verdict} '
        f'financing conditions were {market["financing_condition"].lower()} with a base rate of {market["base_rate_pct"]}% and credit spread at {market["credit_spread_bps"]} bps. '
        f'The valuation environment was "{market["valuation_environment"]}", '
        f'volatility index was {market["volatility_index"]}, '
        f'IPO window score was {market["ipo_window_score"]}, '
        f'and M&A confidence score was {market["ma_confidence_score"]}.'
    )

    if market["primary_story"]:
        market_sentence += f" The market story was: \"{market['primary_story']}\""

    return market_sentence


def _classify_outlook(outlook):
    tone = outlook["outlook_tone"]
    risk = outlook["risk_level"]

    if tone == "Negative" and risk == "High":
        return "negative_high_risk"

    if tone == "Negative":
        return "negative_outlook"

    if tone == "Positive" and risk in ["Low", "Medium"]:
        return "positive_outlook"

    if tone == "Positive":
        return "positive_but_risky"

    return "neutral_or_mixed_outlook"

def _build_outlook_verdict(classification):
    outlook_tone_by_signal = {
        "negative_high_risk": "Sector outlook reinforced downside pressure:",
        "negative_outlook": "Sector outlook was cautious:",
        "positive_outlook": "Sector outlook was constructive:",
        "positive_but_risky": "Sector outlook was positive but still carried risk:",
        "neutral_or_mixed_outlook": "Sector outlook was mixed:",
    }
    return outlook_tone_by_signal[classification]

def _build_outlook_sentence(outlook):
    classification = _classify_outlook(outlook)
    outlook_verdict = _build_outlook_verdict(classification)

    outlook_sentence = (
        f"{outlook_verdict} outlook tone was {outlook['outlook_tone']}, "
        f"risk level was {outlook['risk_level']}."
    )

    if outlook["key_explanation"]:
        outlook_sentence += f" Outlook explanation: \"{outlook['key_explanation']}\""

    return outlook_sentence

def _build_revenue_summary_sentence(year):
    revenue_summary = revenue_by_year(year)
    results = revenue_summary["results"]
    revenue_sentence = (
        f"In {year}, {results[0]['sector']} generated the most revenue among tracked sectors ({results[0]['total_revenue_usd_mm']} {revenue_summary['unit']}), followed by {results[1]['sector']} ({results[1]['total_revenue_usd_mm']} {revenue_summary['unit']})."
    )
    evidence_bullets = [
        f"For {year}, {results[0]['sector']} generated the highest sector revenue at {results[0]['total_revenue_usd_mm']} {revenue_summary['unit']}. ",
        f"{results[1]['sector']} ranked second at {results[1]['total_revenue_usd_mm']} {revenue_summary['unit']}. ",
        f"The revenue ranking includes {len(results)} sectors from {revenue_summary['source']}. "
    ]
    return revenue_sentence, evidence_bullets

def _build_pipeline_comparison_sentence(sector1, sector2):
    pipeline_comparison_evidence = pipeline_comparison(sector1, sector2)
    results = pipeline_comparison_evidence["results"]
    results_by_sector = {
        row["sector"]: row
        for row in results
    }
    sector1_result = results_by_sector[sector1]
    sector2_result = results_by_sector[sector2]
    pipeline_sentence = (
        f"{sector1} had {sector1_result['opportunity_count']} pipeline opportunities versus {sector2} with {sector2_result['opportunity_count']}. "
        f"{sector1} had {sector1_result['total_weighted_fee']} {pipeline_comparison_evidence['unit']} in weighted fees versus {sector2} with {sector2_result['total_weighted_fee']}. "
        f"{sector1} had average probability {sector1_result['average_probability']} versus {sector2} {sector2_result['average_probability']}."
    )
    evidence_bullets = [
        f"{sector1} had {sector1_result['opportunity_count']} pipeline opportunities versus {sector2} with {sector2_result['opportunity_count']}. ",
        f"{sector1} had {sector1_result['total_weighted_fee']} {pipeline_comparison_evidence['unit']} in weighted fees versus {sector2} with {sector2_result['total_weighted_fee']}. ",
        f"{sector1} had average probability {sector1_result['average_probability']} versus {sector2} {sector2_result['average_probability']}. "
    ]
    return pipeline_sentence, evidence_bullets

def generate_summary_paragraph(sector, quarter):
    sector_evidence = get_sector_evidence(sector, quarter)
    canonical_sector = sector_evidence["sector"]
    canonical_quarter = sector_evidence["quarter"]

    revenue = sector_evidence["evidence"]["revenue"]
    deals = sector_evidence["evidence"]["deals"]
    pipeline = sector_evidence["evidence"]["pipeline"]
    market = sector_evidence["evidence"]["market"]
    outlook = sector_evidence["evidence"]["outlook"]

    revenue_sentence = _build_revenue_sentence(revenue, canonical_sector)
    deals_sentence = _build_deals_sentence(deals, canonical_sector)
    pipeline_sentence = _build_pipeline_sentence(pipeline, canonical_sector)
    market_sentence = _build_market_sentence(market)
    outlook_sentence = _build_outlook_sentence(outlook)

    sentences = [revenue_sentence, deals_sentence, pipeline_sentence, market_sentence, outlook_sentence]
    response_dict = {
        "question_type": "sector_analysis",
        "sector": canonical_sector,
        "quarter": canonical_quarter,
        "answer": "\n\n".join(sentences),
        "evidence_bullets": sentences,
        "supporting_evidence": sector_evidence,
        "sources": sector_evidence["sources"],
        "top_level_limitations": ["This evidence indicates association across revenue, deal, pipeline, market, and outlook signals, but does not prove causation."]
    }
    return response_dict

def generate_revenue_paragraph(year):
    revenue_sentence, evidence_bullets = _build_revenue_summary_sentence(year)
    revenue_evidence = revenue_by_year(year)

    response_dict = {
        "question_type": "revenue_ranking",
        "year": year,
        "answer": revenue_sentence,
        "evidence_bullets": evidence_bullets,
        "supporting_evidence": revenue_evidence,
        "sources": [revenue_evidence["source"]],
        "top_level_limitations": ["The tool sums all available quarters for the selected year but does not yet verify that all four quarters are present. Therefore, incomplete-year data could be presented as an annual total."]
    }
    return response_dict

def generate_pipeline_comparison_paragraph(sector1, sector2):
    pipeline_comparison_evidence = pipeline_comparison(sector1, sector2)
    pipeline_comparison_sentence, evidence_bullets = _build_pipeline_comparison_sentence(sector1, sector2)

    response_dict = {
        "question_type": "pipeline_comparison",
        "compared_sectors": pipeline_comparison_evidence["compared_sectors"],
        "answer": pipeline_comparison_sentence,
        "evidence_bullets": evidence_bullets,
        "supporting_evidence": pipeline_comparison_evidence,
        "sources": [pipeline_comparison_evidence["source"]],
        "top_level_limitations": ["Compares pipeline strength quantitatively but does not explain causes of pipeline weakness or strength without additional document/market context."]
    }
    return response_dict

def main():
    #question = "Why did Technology deal activity slow recently?"
    sector = "Technology"
    quarter = "2026Q1"
    year = 2025
    sector1 = "Healthcare"
    sector2 = "Industrials"
    #result = generate_summary_paragraph(sector, quarter)
    #result = generate_revenue_paragraph(year)
    result = generate_pipeline_comparison_paragraph(sector1, sector2)
    print(result)


if __name__ == "__main__":
    main()
