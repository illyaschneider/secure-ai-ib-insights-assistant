from pathlib import Path
import pandas as pd


CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parents[2]
PIPELINE_OPPORTUNITIES_DIR = ROOT_DIR / "data" / "csv" / "pipeline_opportunities.csv"


def _load_pipeline_data(path):
    df = pd.read_csv(path)
    return df


def pipeline_comparison(sector_a, sector_b):
    df = _load_pipeline_data(PIPELINE_OPPORTUNITIES_DIR)

    sector_a = str(sector_a).strip()
    sector_b = str(sector_b).strip()

    if not sector_a or not sector_b:
        raise ValueError("Enter valid sectors")

    unique_sectors = df["sector"].dropna().unique()
    unique_sector_dict = {
        sector.casefold(): sector for sector in unique_sectors
    }
    sector_a_key = sector_a.casefold()
    sector_b_key = sector_b.casefold()
    if sector_a_key not in unique_sector_dict:
        raise ValueError(f"Sector {sector_a} is not among valid sectors")
    if sector_b_key not in unique_sector_dict:
        raise ValueError(f"Sector {sector_b} is not among valid sectors")
    sector_a = unique_sector_dict[sector_a_key]
    sector_b = unique_sector_dict[sector_b_key]
    if sector_a == sector_b:
        raise ValueError("Enter different sectors")

    sectors = [sector_a, sector_b]

    sector_mask = df["sector"].isin(sectors)
    chosen_sectors_df = df.loc[sector_mask]

    pipeline_summary = chosen_sectors_df.groupby("sector").agg(
        opportunity_count = ("opportunity_id", "count"),
        total_deal_value = ("estimated_deal_value_usd_mm", "sum"),
        total_expected_fee = ("expected_fee_usd_mm", "sum"),
        total_weighted_fee = ("weighted_fee_usd_mm", "sum"),
        average_probability = ("probability", "mean"),
        number_of_delayed_opportunities = ("stage", lambda x: (x == "Delayed").sum())
    )

    pipeline_summary = pipeline_summary.round({
        "total_deal_value": 2,
        "total_expected_fee": 2,
        "total_weighted_fee": 2,
        "average_probability": 3,
    })
    pipeline_summary = pipeline_summary.reset_index()

    pipeline_summary_dict = {
        "compared_sectors": sectors,
        "available_sectors": unique_sectors.tolist(),
        "primary_metric": "total_weighted_fee",
        "unit": "USD Millions",
        "probability_unit": "decimal from 0 to 1",
        "source": "pipeline_opportunities.csv",
        "results": pipeline_summary.to_dict(orient="records")
    }
    return pipeline_summary_dict


def main():
    comparison_summary = pipeline_comparison("Healthcare", "Industrials")
    print(comparison_summary)

if __name__ == "__main__":
    main()

