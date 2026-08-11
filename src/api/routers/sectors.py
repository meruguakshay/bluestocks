
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api.utils import get_db_connection, to_float

router = APIRouter()


@router.get("/sectors")
def get_sectors_summary():
    """
    Return all sectors with company count, median ROE, median P/E, and median D/E.
    """
    conn = get_db_connection()

    # Load 2024 ratios and market caps
    df_ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios WHERE year LIKE '2024-%'", conn
    )
    df_mcap = pd.read_sql_query(
        "SELECT * FROM market_cap WHERE year LIKE '2024-%'", conn
    )
    df_comps = pd.read_sql_query(
        "SELECT c.company_id, s.broad_sector FROM companies c LEFT JOIN sectors s ON c.sector_id = s.sector_id",
        conn,
    )
    conn.close()

    if df_comps.empty:
        return []

    # Deduplicate ratios for latest conformed year 2024
    df_ratios["is_null_roe"] = df_ratios["return_on_equity_pct"].isna()
    df_ratios["ends_with_03"] = df_ratios["year"].str.endswith("-03")
    df_ratios = df_ratios.sort_values(
        by=["company_id", "is_null_roe", "ends_with_03"], ascending=[True, True, False]
    ).drop_duplicates(subset=["company_id"], keep="first")

    df_mcap = df_mcap.drop_duplicates(subset=["company_id"], keep="first")

    # Merge
    df_merged = pd.merge(df_ratios, df_mcap, on="company_id", how="inner")
    df_merged = pd.merge(df_merged, df_comps, on="company_id", how="inner")

    # Compute aggregates per broad_sector
    summary = []
    for sector_name, grp in df_merged.groupby("broad_sector"):
        summary.append(
            {
                "sector": sector_name,
                "company_count": len(grp),
                "median_roe": to_float(grp["return_on_equity_pct"].median()),
                "median_pe": to_float(grp["pe_ratio"].median()),
                "median_de": to_float(grp["debt_to_equity"].median()),
            }
        )

    return summary


@router.get("/sectors/{sector}/companies")
def get_companies_in_sector(
    sector: str,
    year: str | None = Query(
        None, description="Optional year filter in YYYY-MM format"
    ),
):
    """
    Return all companies in a sector with latest year KPIs (or custom year).
    Returns HTTP 404 for unknown sector.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify sector exists
    cursor.execute(
        "SELECT 1 FROM sectors WHERE LOWER(broad_sector) = LOWER(?)", (sector,)
    )
    sect_exists = cursor.fetchone()
    if not sect_exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

    # Load companies in sector
    cursor.execute(
        """
        SELECT c.company_id, c.company_name, c.sub_sector, c.market_cap_category
        FROM companies c
        JOIN sectors s ON c.sector_id = s.sector_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
    """,
        (sector,),
    )
    companies = cursor.fetchall()

    if not companies:
        conn.close()
        return []

    # Query ratios for these companies
    tickers = [c["company_id"] for c in companies]
    placeholders = ",".join(["?"] * len(tickers))

    if year:
        ratio_query = f"SELECT * FROM financial_ratios WHERE company_id IN ({placeholders}) AND year = ?"
        params = tickers + [year]
    else:
        # Get latest year for each company
        ratio_query = f"""
            SELECT fr.* FROM financial_ratios fr
            JOIN (
                SELECT company_id, MAX(year) as max_year 
                FROM financial_ratios 
                WHERE company_id IN ({placeholders})
                GROUP BY company_id
            ) my ON fr.company_id = my.company_id AND fr.year = my.max_year
        """
        params = tickers

    cursor.execute(ratio_query, params)
    ratios = cursor.fetchall()
    conn.close()

    ratios_dict = {r["company_id"]: dict(r) for r in ratios}

    results = []
    for comp in companies:
        ticker = comp["company_id"]
        results.append(
            {
                "ticker": ticker,
                "company_name": comp["company_name"],
                "sub_sector": comp["sub_sector"],
                "market_cap_category": comp["market_cap_category"],
                "latest_kpis": ratios_dict.get(ticker, None),
            }
        )

    return results
