import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.utils import get_db_connection

router = APIRouter()


# Helper to verify company exists
def check_company_exists(ticker: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM companies WHERE company_id = ?", (ticker,))
    exists = cursor.fetchone()
    conn.close()
    if not exists:
        raise HTTPException(
            status_code=404, detail=f"Company with ticker {ticker} not found"
        )


@router.get("/companies")
def get_companies(
    sector: str | None = Query(None, description="Filter by broad sector name"),
    market_cap_category: str | None = Query(
        None, description="Filter by market cap category (e.g. Large Cap)"
    ),
    search: str | None = Query(None, description="Search company name or ticker"),
):
    """
    List all companies with basic info: id, company_name, broad_sector, sub_sector, roe_pct, roce_pct.
    Supports filtering by sector, market cap category, and text search.
    """
    conn = get_db_connection()
    query = """
        SELECT c.company_id as id, c.company_name, s.broad_sector, c.sub_sector, 
               c.roe_percentage as roe_pct, c.roce_percentage as roce_pct, c.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON c.sector_id = s.sector_id
        WHERE 1=1
    """
    params = []

    if sector:
        query += " AND LOWER(s.broad_sector) = LOWER(?)"
        params.append(sector)
    if market_cap_category:
        query += " AND LOWER(c.market_cap_category) = LOWER(?)"
        params.append(market_cap_category)
    if search:
        query += " AND (LOWER(c.company_name) LIKE ? OR LOWER(c.company_id) LIKE ?)"
        params.append(f"%{search.lower()}%")
        params.append(f"%{search.lower()}%")

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}")
def get_company_profile(ticker: str):
    """
    Return full company profile: basic company info, latest year financial KPIs, and broad sector.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check company details
    cursor.execute(
        """
        SELECT c.*, s.broad_sector
        FROM companies c
        LEFT JOIN sectors s ON c.sector_id = s.sector_id
        WHERE c.company_id = ?
    """,
        (ticker.upper(),),
    )
    comp_row = cursor.fetchone()
    if not comp_row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Company with ticker {ticker} not found"
        )

    company_data = dict(comp_row)

    # Get latest KPIs from financial_ratios
    cursor.execute(
        """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
    """,
        (ticker.upper(),),
    )
    ratio_row = cursor.fetchone()

    # Get pros and cons
    cursor.execute(
        "SELECT pros, cons FROM prosandcons WHERE company_id = ?", (ticker.upper(),)
    )
    pros_cons_row = cursor.fetchone()

    conn.close()

    company_data["latest_ratios"] = dict(ratio_row) if ratio_row else None
    company_data["pros_cons"] = (
        dict(pros_cons_row) if pros_cons_row else {"pros": "", "cons": ""}
    )
    return company_data


@router.get("/companies/{ticker}/pl")
def get_pl_history(
    ticker: str,
    from_year: str | None = Query(None, description="Start year in YYYY-MM format"),
    to_year: str | None = Query(None, description="End year in YYYY-MM format"),
):
    """
    Return profit and loss history array. Supports YYYY-MM filters.
    """
    check_company_exists(ticker.upper())
    conn = get_db_connection()
    query = "SELECT * FROM profitandloss WHERE company_id = ? "
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ? "
        params.append(from_year)
    if to_year:
        query += " AND year <= ? "
        params.append(to_year)

    query += " ORDER BY year"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/bs")
def get_bs_history(
    ticker: str,
    from_year: str | None = Query(None, description="Start year in YYYY-MM format"),
    to_year: str | None = Query(None, description="End year in YYYY-MM format"),
):
    """
    Return balance sheet history array. Supports YYYY-MM filters.
    """
    check_company_exists(ticker.upper())
    conn = get_db_connection()
    query = "SELECT * FROM balancesheet WHERE company_id = ? "
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ? "
        params.append(from_year)
    if to_year:
        query += " AND year <= ? "
        params.append(to_year)

    query += " ORDER BY year"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/cashflow")
def get_cashflow_history(
    ticker: str,
    from_year: str | None = Query(None, description="Start year in YYYY-MM format"),
    to_year: str | None = Query(None, description="End year in YYYY-MM format"),
):
    """
    Return cash flow history array. Supports YYYY-MM filters.
    """
    check_company_exists(ticker.upper())
    conn = get_db_connection()
    query = "SELECT * FROM cashflow WHERE company_id = ? "
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ? "
        params.append(from_year)
    if to_year:
        query += " AND year <= ? "
        params.append(to_year)

    query += " ORDER BY year"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/ratios")
def get_ratios_history(
    ticker: str,
    year: str | None = Query(
        None, description="Optional year filter in YYYY-MM format"
    ),
):
    """
    Return all computed KPIs per year for the company.
    """
    check_company_exists(ticker.upper())
    conn = get_db_connection()
    query = "SELECT * FROM financial_ratios WHERE company_id = ? "
    params = [ticker.upper()]

    if year:
        query += " AND year = ? "
        params.append(year)

    query += " ORDER BY year"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    """
    Returns the pre-generated tearsheet PDF as a binary file download.
    """
    check_company_exists(ticker.upper())

    # Tearsheet path
    pdf_path = f"reports/tearsheets/{ticker.upper()}_tearsheet.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404, detail=f"Tearsheet PDF for company {ticker} not found"
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{ticker.upper()}_tearsheet.pdf",
    )
