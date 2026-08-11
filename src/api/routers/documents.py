import re

from fastapi import APIRouter, HTTPException, Query

from src.api.utils import get_db_connection

router = APIRouter()

# Regex for syntax validation
URL_REGEX = re.compile(
    r"^(?:http|ftp)s?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    if not url or str(url).lower() in ("nan", "null", ""):
        return False
    return bool(URL_REGEX.match(str(url).strip()))


@router.get("/companies/{ticker}/documents")
def get_company_documents(
    ticker: str,
    from_year: str | None = Query(None, description="Start year in YYYY-MM format"),
    to_year: str | None = Query(None, description="End year in YYYY-MM format"),
):
    """
    Return annual report links with an is_url_valid boolean flag for each.
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

    query = "SELECT year, annual_report FROM documents WHERE company_id = ?"
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

    results = []
    for row in rows:
        url = row["annual_report"]
        results.append(
            {
                "year": row["year"],
                "annual_report": url,
                "is_url_valid": is_valid_url(url),
            }
        )

    return results
