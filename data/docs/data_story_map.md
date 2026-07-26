# Investment Banking Dataset Evidence Guide

This document explains the intended analytical story inside the fictional investment banking dataset. It is an approved retrieval source for the assistant. The document should support answers with narrative context, but the structured CSV and SQLite-backed tools remain the source of truth for numbers.

## Central Case: Technology Weakness in 2026Q1

Technology shows a sharp deterioration in 2026Q1 across revenue, deal execution, pipeline activity, market conditions, and sector outlook.

Revenue evidence:

- Technology revenue fell from 162.89 USD Million in 2025Q4 to 5.39 USD Million in 2026Q1.
- The absolute revenue change was -157.5 USD Million.
- Quarter-over-quarter growth was -96.7%.
- Source table: `revenue_by_sector_quarter.csv`.

Deal execution evidence:

- Technology had 3 tracked deals in 2026Q1.
- 2 of the 3 tracked deals were delayed or withdrawn.
- Delayed deal reasons included "Financing market volatility" and "Valuation gap after multiple reset".
- Source table: `deals.csv`.

Pipeline evidence:

- Technology had 12 tracked pipeline opportunities.
- 5 of the 12 pipeline opportunities were delayed.
- Delayed pipeline represented 41.7% of the Technology pipeline.
- Main pipeline delay reasons included "IPO window score fell below launch threshold", "Financing committee paused leverage package", and "Valuation gap after 2026Q1 market reset".
- Source table: `pipeline_opportunities.csv`.

Market evidence:

- In 2026Q1, the volatility index was 29.4.
- The base rate was 4.8%.
- Credit spread was 225 bps.
- IPO window score was 34.
- M&A confidence score was 42.
- Financing condition was Tight.
- Valuation environment was "Sharp multiple reset in Technology".
- Primary market story: "Volatility spike and financing concerns delayed Technology M&A and IPO activity."
- Source table: `market_conditions.csv`.

Sector outlook evidence:

- Technology outlook tone was Negative.
- Risk level was High.
- Outlook explanation: "Technology outlook turned cautious: buyers pushed back on valuation, lenders tightened underwriting, and several sponsor-backed software processes moved from launch to delayed."
- Source table: `sector_outlook_notes.csv`.

Recommended interpretation:

The assistant may say that Technology deal activity slowed because several independent signals point in the same direction: revenue collapsed quarter-over-quarter, delayed deals increased, pipeline delays were elevated, financing conditions tightened, market confidence weakened, and the sector outlook became negative. The assistant should describe this as evidence of association, not proof of causation.

## 2025 Sector Revenue Ranking

For 2025, the revenue ranking across tracked sectors was:

1. Technology: 509.8 USD Millions.
2. Healthcare: 432.14 USD Millions.
3. Energy: 270.96 USD Millions.
4. Industrials: 261.55 USD Millions.
5. Financial Institutions: 229.82 USD Millions.
6. Consumer & Retail: 227.49 USD Millions.

Recommended interpretation:

The assistant may say that Technology generated the most tracked revenue in 2025, followed by Healthcare. The assistant should mention that the annual total is based on available quarterly records and does not independently verify whether every year has all four quarters populated.

## Healthcare Versus Industrials Pipeline Strength

Healthcare and Industrials can be compared using pipeline opportunity count, total expected fees, probability-weighted fees, and average probability.

Healthcare pipeline evidence:

- Opportunity count: 10.
- Total deal value: 23927.1 USD Millions.
- Total expected fee: 241.02 USD Millions.
- Total weighted fee: 141.75 USD Millions.
- Average probability: 0.524.
- Delayed opportunities: 0.

Industrials pipeline evidence:

- Opportunity count: 8.
- Total deal value: 11930.1 USD Millions.
- Total expected fee: 143.38 USD Millions.
- Total weighted fee: 67.16 USD Millions.
- Average probability: 0.57.
- Delayed opportunities: 0.

Recommended interpretation:

The assistant may say that Healthcare has the stronger pipeline by opportunity count and probability-weighted fees. Industrials has a slightly higher average probability, but Healthcare has the larger and higher-value pipeline overall.

## Assistant Answer Rules

When using this document, the assistant should:

1. Use this document only as approved narrative context.
2. Prefer structured tool outputs for exact metrics.
3. Avoid adding external news, real company events, or market commentary.
4. Clearly state when evidence is incomplete.
5. Treat the data as fictional and educational.
6. Avoid claiming causation when the evidence only shows association.

## Retrieval Limitations

- This document is curated for the fictional MVP dataset.
- Keyword retrieval can miss relevant passages if the user uses different phrasing.
- PDF extraction only works for machine-readable PDFs, not scanned images.
- The current assistant does not yet perform semantic search or vector retrieval.
