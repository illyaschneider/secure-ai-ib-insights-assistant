from pathlib import Path
import pandas as pd

CURRENT_PATH = Path(__file__).resolve()
ROOT_FILEPATH = CURRENT_PATH.parents[3]

REVENUE_BY_SECTOR_PATH = ROOT_FILEPATH / "data" / "csv" / "revenue_by_sector_quarter.csv"
PIPELINE_OPPORTUNITIES_PATH = ROOT_FILEPATH / "data" / "csv" / "pipeline_opportunities.csv"
DEALS_PATH = ROOT_FILEPATH / "data" / "csv" / "deals.csv"
MARKET_CONDITIONS_PATH = ROOT_FILEPATH / "data" / "csv" / "market_conditions.csv"
SECTOR_OUTLOOK_NOTES_PATH = ROOT_FILEPATH / "data" / "csv" / "sector_outlook_notes.csv"

def _load_csv_data(path):
    df = pd.read_csv(path)
    return df

def _get_outlook_evidence(sector, quarter):
    df = _load_csv_data(SECTOR_OUTLOOK_NOTES_PATH)
    sector = str(sector).strip()
    quarter = str(quarter).strip()

    if df.empty:
        raise ValueError("Sector outlook source is empty")

    sector_mask = df["sector"].str.casefold() == sector.casefold()
    quarter_mask = df["quarter"].str.casefold() == quarter.casefold()
    sector_quarter_outlook_df = df.loc[sector_mask & quarter_mask]

    if sector_quarter_outlook_df.empty:
        raise ValueError("No outlook evidence found using current input. Check your sector or quarter")

    matching_row = sector_quarter_outlook_df.iloc[0]
    canonical_quarter = matching_row["quarter"]
    canonical_sector = matching_row["sector"]

    outlook_summary_dict = {
        "chosen_sector": canonical_sector,
        "current_quarter": canonical_quarter,
        "outlook_tone": matching_row["outlook_tone"],
        "risk_level": matching_row["risk_level"],
        "key_explanation": matching_row["key_explanation"],
        "source": "sector_outlook_notes.csv"
    }
    return outlook_summary_dict

def _get_market_evidence(quarter):
    df = _load_csv_data(MARKET_CONDITIONS_PATH)
    quarter = str(quarter).strip()

    if df.empty:
        raise ValueError("Market conditions source is empty")

    quarter_mask = df["quarter"].str.casefold() == quarter.casefold()
    market_conditions_quarter_df = df.loc[quarter_mask]

    if market_conditions_quarter_df.empty:
        raise ValueError("No Market Conditions found for {}".format(quarter))

    matching_row = market_conditions_quarter_df.iloc[0]
    canonical_quarter = matching_row["quarter"]
    market_summary_dict = {
        "quarter": canonical_quarter,
        "volatility_index": float(matching_row["volatility_index"]),
        "base_rate_pct": float(matching_row["base_rate_pct"]),
        "credit_spread_bps": int(matching_row["credit_spread_bps"]),
        "ipo_window_score": int(matching_row["ipo_window_score"]),
        "ma_confidence_score": int(matching_row["ma_confidence_score"]),
        "financing_condition": matching_row["financing_condition"],
        "valuation_environment": matching_row["valuation_environment"],
        "primary_story": matching_row["primary_story"],
        "source": "market_conditions.csv"
    }
    return market_summary_dict

def _get_pipeline_evidence(sector):
    df = _load_csv_data(PIPELINE_OPPORTUNITIES_PATH)
    sector = str(sector).strip()
    if df.empty:
        raise ValueError("Pipeline opportunities source is empty")

    sector_mask = df["sector"].str.casefold() == sector.casefold()
    pipeline_df = df.loc[sector_mask]
    if pipeline_df.empty:
        raise ValueError("No pipeline opportunities found for {}".format(sector))
    canonical_sector = pipeline_df.iloc[0]["sector"]

    delayed_mask = pipeline_df["stage"] == "Delayed"
    delayed_df = pipeline_df.loc[delayed_mask]
    delay_evidence_df = delayed_df[["deal_type", "stage", "target_announcement_quarter", "probability", "delay_reason"]]
    total_pipeline_opportunities_count = len(pipeline_df)
    delayed_opportunities_count = len(delayed_df)
    delayed_share_pct = round(delayed_opportunities_count / total_pipeline_opportunities_count * 100, 1)
    pipeline_summary_dict = {
        "chosen_sector": canonical_sector,
        "total_pipeline_opportunities": total_pipeline_opportunities_count,
        "delayed_opportunities": delayed_opportunities_count,
        "delayed_share_pct": delayed_share_pct,
        "delay_reason_distribution": delayed_df["delay_reason"].value_counts().to_dict(),
        "delay_evidence": delay_evidence_df.to_dict(orient="records"),
        "source": "pipeline_opportunities.csv"
    }

    return pipeline_summary_dict

def _get_deals_evidence(sector, quarter):
    df = _load_csv_data(DEALS_PATH)
    sector = str(sector).strip()
    quarter = str(quarter).strip()
    if df.empty:
        raise ValueError("Deals source is empty")

    sector_mask = df["sector"].str.casefold() == sector.casefold()
    quarter_mask = df["quarter"].str.casefold() == quarter.casefold()
    deals_df = df.loc[sector_mask & quarter_mask]
    delayed_or_withdrawn_mask = deals_df["status"].isin(["Delayed", "Withdrawn"])
    delay_evidence_df = deals_df.loc[deals_df["status"].isin(["Delayed", "Withdrawn"]), ["deal_type", "status", "probability_of_close", "delay_or_loss_reason"]]
    canonical_sector = deals_df.iloc[0]["sector"]
    canonical_quarter = deals_df.iloc[0]["quarter"]
    deals_summary_dict = {
        "chosen_sector": canonical_sector,
        "current_quarter": canonical_quarter,
        "total_deals": len(deals_df),
        "status_distribution": deals_df["status"].value_counts().to_dict(),
        "delayed_or_withdrawn_count": len(deals_df.loc[delayed_or_withdrawn_mask]),
        "delay_evidence": delay_evidence_df.to_dict(orient="records"),
        "source": "deals.csv"
    }
    return deals_summary_dict

def _previous_quarter_helper(quarter):
    quarter = str(quarter).strip().upper()

    if len(quarter) != 6:
        raise ValueError("Quarter must use format YYYYQ#")

    year = quarter[:4]
    quarter_number = quarter[4:]

    if not year.isdigit():
        raise ValueError("Quarter must use format YYYYQ#")

    valid_quarters = ["Q1", "Q2", "Q3", "Q4"]

    if quarter_number not in valid_quarters:
        raise ValueError("Quarter must use format YYYYQ#")

    if quarter_number == "Q1":
        year = str(int(year) - 1)
        quarter_number = "Q4"
    else:
        quarter_number = f"Q{int(quarter_number[1:]) - 1}"

    return year + quarter_number

def _get_revenue_evidence(sector, quarter):
    df = _load_csv_data(REVENUE_BY_SECTOR_PATH)
    sector = str(sector).strip()
    quarter = str(quarter).strip()
    previous_quarter = _previous_quarter_helper(quarter)
    if df.empty:
        raise ValueError("Revenue-by-sector source is empty")

    sector_mask = df["sector"].str.casefold() == sector.casefold()
    current_quarter_mask = df["quarter"].str.casefold() == quarter.casefold()
    current_quarter_revenue_df = df.loc[sector_mask & current_quarter_mask]
    if current_quarter_revenue_df.empty:
        raise ValueError("No available revenue data for {} {}".format(sector, quarter))
    matching_row = current_quarter_revenue_df.iloc[0]
    canonical_sector = matching_row["sector"]
    canonical_quarter = matching_row["quarter"]
    current_total = float(matching_row["total_revenue_usd_mm"])

    previous_quarter_mask = df["quarter"].str.casefold() == previous_quarter.casefold()
    previous_quarter_revenue_df = df.loc[sector_mask & previous_quarter_mask]
    if previous_quarter_revenue_df.empty:
        previous_total = None
        absolute_change = None
        qoq_growth = None
    else:
        previous_row = previous_quarter_revenue_df.iloc[0]
        previous_total = float(previous_row["total_revenue_usd_mm"])
        absolute_change = float(matching_row["total_revenue_usd_mm"]) - float(previous_row["total_revenue_usd_mm"])
        absolute_change = round(absolute_change, 2)
        if previous_total == 0:
            qoq_growth = None
        else:
            qoq_growth = round(((current_total / previous_total) - 1) * 100, 1)

    revenue_dict = {
        "chosen_sector": canonical_sector,
        "current_quarter": canonical_quarter,
        "previous_quarter": previous_quarter,
        "current_total_revenue": current_total,
        "previous_total_revenue": previous_total,
        "revenue_unit": "USD Million",
        "absolute_change": absolute_change,
        "qoq_growth_pct": qoq_growth,
        "qoq_growth_unit": "%",
        "source": "revenue_by_sector_quarter.csv",
    }
    return revenue_dict

def get_sector_evidence(sector, quarter):
    sector = str(sector).strip()
    quarter = str(quarter).strip()

    revenue_evidence = _get_revenue_evidence(sector, quarter)
    deals_evidence = _get_deals_evidence(sector, quarter)
    pipeline_evidence = _get_pipeline_evidence(sector)
    market_evidence = _get_market_evidence(quarter)
    outlook_evidence = _get_outlook_evidence(sector, quarter)

    canonical_sector = revenue_evidence["chosen_sector"]
    canonical_quarter = revenue_evidence["current_quarter"]
    summary_dict = {
        "sector": canonical_sector,
        "quarter": canonical_quarter,
        "evidence": {
            "revenue": revenue_evidence,
            "deals": deals_evidence,
            "pipeline": pipeline_evidence,
            "market": market_evidence,
            "outlook": outlook_evidence
        },
        "sources": ["revenue_by_sector_quarter.csv", "deals.csv", "pipeline_opportunities.csv", "market_conditions.csv", "sector_outlook_notes.csv"],
        "evidence_used_limitations": ["Evidence indicates association, not proven causation.", "Pipeline data is a current snapshot.", "The current implementation requires all configured sources; if any source is unavailable, the request fails instead of returning partial evidence."]
    }

    return summary_dict

def main():
    quarter = "2026Q1"
    sector = "Technology"
    #result_outlook = _get_outlook_evidence(sector = sector, quarter = quarter)
    #result_market = _get_market_evidence(quarter = quarter)
    #result_revenue = _get_revenue_evidence(sector = sector, quarter = quarter)
    #result_deals = _get_deals_evidence(sector = sector, quarter = quarter)
    #result_pipeline = _get_pipeline_evidence(sector = sector)
    overall_result = get_sector_evidence(sector, quarter)
    #print(result_outlook)
    #print(result_market)
    #print(result_revenue)
    #print(result_deals)
    #print(result_pipeline)
    print(overall_result)

if __name__ == "__main__":
    main()
