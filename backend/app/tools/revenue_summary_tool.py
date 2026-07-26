from pathlib import Path
from backend.app.database import _query_revenue_summary

def revenue_by_year(year):
    year = str(year).strip()
    if len(year) != 4 or not year.isdigit():
        raise ValueError("Year must contain exactly 4 digits")

    revenue_list = _query_revenue_summary(year)
    if not revenue_list:
        raise ValueError(f"No revenue data found for year {year}")

    summary_dict = {
        "year": year,
        "unit": "USD Millions",
        "source": "revenue_by_sector_quarter.csv",
        "query_source": "SQLite",
        "source_table": "revenue_by_sector_quarter",
        "results": revenue_list,
    }

    return summary_dict

def main():
    year = 2025
    summary = revenue_by_year(year)
    print(summary)

if __name__ == "__main__":
    main()
