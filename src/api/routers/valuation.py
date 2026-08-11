
from fastapi import APIRouter, HTTPException, Query

from src.api.utils import get_db_connection

router = APIRouter()


@router.get("/market-cap/{ticker}")
def get_valuation_history(
    ticker: str,
    from_year: str | None = Query(None, description="Start year in YYYY-MM format"),
    to_year: str | None = Query(None, description="End year in YYYY-MM format"),
):
    """
    Return historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield) from 2019 to 2024.
    Returns HTTP 404 if ticker is not found in companies table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify company exists
    cursor.execute("SELECT 1 FROM companies WHERE company_id = ?", (ticker.upper(),))
    exists = cursor.fetchone()
    if not exists:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Company with ticker {ticker} not found"
        )

    query = "SELECT * FROM market_cap WHERE company_id = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
