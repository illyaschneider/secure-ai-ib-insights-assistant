from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TABLES = [
    "teams",
    "bankers",
    "clients",
    "deals",
    "pipeline_opportunities",
    "revenue_by_sector_quarter",
    "revenue_by_region_quarter",
    "market_conditions",
    "sector_outlook_notes",
    "client_activity",
    "banker_coverage_summary",
    "data_sources",
]

TYPE_HINTS = {
    "relationship_start_year": "INTEGER",
    "annual_revenue_usd_mm": "REAL",
    "volatility_index": "REAL",
    "base_rate_pct": "REAL",
    "credit_spread_bps": "INTEGER",
    "ipo_window_score": "INTEGER",
    "ma_confidence_score": "INTEGER",
    "coverage_meetings": "INTEGER",
    "pitch_books_sent": "INTEGER",
    "management_calls": "INTEGER",
    "engagement_score": "INTEGER",
    "deal_value_usd_mm": "REAL",
    "estimated_fee_usd_mm": "REAL",
    "recognized_revenue_usd_mm": "REAL",
    "probability_of_close": "REAL",
    "estimated_deal_value_usd_mm": "REAL",
    "expected_fee_usd_mm": "REAL",
    "probability": "REAL",
    "weighted_fee_usd_mm": "REAL",
    "advisory_revenue_usd_mm": "REAL",
    "ecm_revenue_usd_mm": "REAL",
    "dcm_revenue_usd_mm": "REAL",
    "total_revenue_usd_mm": "REAL",
    "qoq_growth_pct": "REAL",
    "deal_count": "INTEGER",
    "closed_deal_count": "INTEGER",
    "delayed_deal_count": "INTEGER",
    "active_client_count": "INTEGER",
    "historical_deal_count": "INTEGER",
    "pipeline_opportunity_count": "INTEGER",
    "historical_recognized_revenue_usd_mm": "REAL",
    "pipeline_weighted_fee_usd_mm": "REAL",
}

PRIMARY_KEYS = {
    "teams": "team_id",
    "bankers": "banker_id",
    "clients": "client_id",
    "deals": "deal_id",
    "pipeline_opportunities": "opportunity_id",
    "data_sources": "source_id",
}


def sql_type(column: str) -> str:
    return TYPE_HINTS.get(column, "TEXT")


def create_table(conn: sqlite3.Connection, table_name: str, fieldnames: list[str]) -> None:
    columns = []
    pk = PRIMARY_KEYS.get(table_name)
    for col in fieldnames:
        col_type = sql_type(col)
        if col == pk:
            columns.append(f'"{col}" {col_type} PRIMARY KEY')
        else:
            columns.append(f'"{col}" {col_type}')
    columns.append('"_source_file" TEXT NOT NULL')
    columns.append('"_loaded_at_utc" TEXT NOT NULL')
    ddl = f'DROP TABLE IF EXISTS "{table_name}";\nCREATE TABLE "{table_name}" ({", ".join(columns)});'
    conn.executescript(ddl)


def convert_value(column: str, value: str):
    if value == "":
        return None
    col_type = sql_type(column)
    if col_type == "INTEGER":
        return int(float(value))
    if col_type == "REAL":
        return float(value)
    return value


def load_csv(conn: sqlite3.Connection, csv_path: Path, table_name: str) -> int:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"No header found in {csv_path}")
        fieldnames = reader.fieldnames
        create_table(conn, table_name, fieldnames)
        load_time = datetime.now(timezone.utc).isoformat()
        insert_cols = fieldnames + ["_source_file", "_loaded_at_utc"]
        placeholders = ", ".join(["?"] * len(insert_cols))
        col_sql = ", ".join([f'"{c}"' for c in insert_cols])
        sql = f'INSERT INTO "{table_name}" ({col_sql}) VALUES ({placeholders})'
        count = 0
        for row in reader:
            values = [convert_value(c, row[c]) for c in fieldnames]
            values += [csv_path.name, load_time]
            conn.execute(sql, values)
            count += 1
    return count


def create_indexes(conn: sqlite3.Connection) -> None:
    index_statements = [
        'CREATE INDEX IF NOT EXISTS idx_deals_client ON deals(client_id);',
        'CREATE INDEX IF NOT EXISTS idx_deals_quarter_sector ON deals(quarter, sector);',
        'CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);',
        'CREATE INDEX IF NOT EXISTS idx_pipeline_sector_stage ON pipeline_opportunities(sector, stage);',
        'CREATE INDEX IF NOT EXISTS idx_revenue_sector_quarter ON revenue_by_sector_quarter(quarter, sector);',
        'CREATE INDEX IF NOT EXISTS idx_market_quarter ON market_conditions(quarter);',
        'CREATE INDEX IF NOT EXISTS idx_outlook_quarter_sector ON sector_outlook_notes(quarter, sector);',
        'CREATE INDEX IF NOT EXISTS idx_activity_client_quarter ON client_activity(client_id, quarter);',
    ]
    for stmt in index_statements:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            # Allows selected-table ingestion without failing if an optional table was skipped.
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Load selected fictional IB CSVs into SQLite.")
    parser.add_argument("--csv-dir", default="csv", help="Directory containing CSV source files.")
    parser.add_argument("--db", default="ib_fictional_bank.sqlite", help="Output SQLite database path.")
    parser.add_argument("--tables", nargs="*", default=DEFAULT_TABLES, help="Table names to load. Name must match CSV file stem.")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    db_path = Path(args.db)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    loaded = []
    try:
        for table_name in args.tables:
            csv_path = csv_dir / f"{table_name}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing CSV for table '{table_name}': {csv_path}")
            row_count = load_csv(conn, csv_path, table_name)
            loaded.append((table_name, row_count, csv_path.name))
        create_indexes(conn)
        conn.commit()
    finally:
        conn.close()

    print(f"Loaded {len(loaded)} tables into {db_path}")
    for table_name, row_count, source in loaded:
        print(f"- {table_name}: {row_count} rows from {source}")


if __name__ == "__main__":
    main()
