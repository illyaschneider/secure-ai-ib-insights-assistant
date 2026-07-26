from pathlib import Path
import sqlite3

CURRENT_PATH = Path(__file__).resolve()
ROOT_PATH = CURRENT_PATH.parents[2]
DATABASE_PATH = ROOT_PATH / "data" / "ib_fictional_bank.sqlite"


def _get_read_only_connection():
    database_uri = f"{DATABASE_PATH.as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection

def _query_revenue_summary(year):
    connection = _get_read_only_connection()
    try:
        query = """
            SELECT
                sector,
                ROUND(SUM(total_revenue_usd_mm), 2) AS total_revenue_usd_mm
            FROM revenue_by_sector_quarter
            WHERE quarter LIKE ?
            GROUP BY sector
            ORDER BY total_revenue_usd_mm DESC;
        """
        parameters = (f"{year}%",)

        rows = connection.execute(query, parameters).fetchall()
        row_list = [dict(row) for row in rows]
        return row_list
    finally:
        connection.close()


def main():
    year = 2025

    result = _query_revenue_summary(year)
    print(result)

if __name__ == "__main__":
    main()
