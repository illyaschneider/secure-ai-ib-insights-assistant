# Fictional Investment Bank Dataset for AI Assistant Practice

This package contains a coherent fictional investment-banking dataset designed for a secure AI assistant project.

The dataset is not real client data. It is synthetic, but it uses realistic investment-banking entities, formats, units, and relationships.

## Size

- 30 clients
- 110 historical / in-quarter deals
- 54 pipeline opportunities
- 8 quarters: 2024Q2 through 2026Q1
- 4 regions: North America, Europe, Asia-Pacific, Latin America
- 6 sectors: Technology, Healthcare, Industrials, Consumer & Retail, Energy, Financial Institutions
- 12 bankers across 5 teams

## Deliberate Data Stories

This dataset is intentionally internally consistent. It is designed so an AI assistant can produce grounded answers rather than generic fabricated-sounding explanations.

1. Technology revenue declines in 2026Q1.
2. Market volatility and credit spreads increase in 2026Q1.
3. Several Technology deals and pipeline opportunities are delayed in 2026Q1.
4. The Technology sector outlook notes explain valuation gaps, tighter financing, and sponsor hesitation.
5. Healthcare and Energy are comparatively resilient into 2026Q1.
6. Revenue, deal status, market conditions, and sector notes can be joined to explain business performance.

## CSV Files

CSV source files are in `/csv` and should be treated as traceable source material.

- clients.csv
- bankers.csv
- teams.csv
- deals.csv
- pipeline_opportunities.csv
- revenue_by_sector_quarter.csv
- revenue_by_region_quarter.csv
- market_conditions.csv
- sector_outlook_notes.csv
- client_activity.csv
- banker_coverage_summary.csv
- data_sources.csv

## SQLite Ingestion

Run from the package root:

```bash
python scripts/ingest_to_sqlite.py --csv-dir csv --db ib_fictional_bank.sqlite
```

Load only selected CSVs:

```bash
python scripts/ingest_to_sqlite.py --csv-dir csv --db ib_fictional_bank.sqlite --tables clients bankers deals revenue_by_sector_quarter market_conditions sector_outlook_notes
```

The ingestion process adds these traceability columns to every SQLite table:

- `_source_file`
- `_loaded_at_utc`

This keeps CSV files as the auditable source of truth while letting your backend query SQLite.


## Good Test Questions

1. Which sectors generated the most revenue in 2026Q1?
2. Why did Technology revenue decline in the latest quarter?
3. Which Technology deals were delayed in 2026Q1 and why?
4. Which sector has the strongest forward pipeline?
5. Which bankers own the largest weighted pipeline?
6. Compare Healthcare vs Technology in 2026Q1.
7. Which region had the strongest advisory performance?
8. What should leadership prioritize next quarter?

## Files for Development

- `sql/sample_queries.sql`: starter SQL questions
- `sql/schema_notes.sql`: relationships and intended keys
- `docs/data_story_map.md`: explanation of the intentional dataset logic
- `manifest.json`: dataset metadata and row counts







