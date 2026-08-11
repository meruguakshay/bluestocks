
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api.utils import get_db_connection, to_float

router = APIRouter()


@router.get("/peers/{group_name}")
def get_peer_group_percentiles(
    group_name: str,
    year: str | None = Query(
        None, description="Optional year filter in YYYY-MM format"
    ),
):
    """
    Return all companies in a peer group with percentile rank for each of 10 metrics.
    Returns HTTP 404 for unknown group.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify group exists in peer_groups table
    cursor.execute(
        "SELECT 1 FROM peer_groups WHERE LOWER(peer_group_name) = LOWER(?)",
        (group_name,),
    )
    group_exists = cursor.fetchone()
    if not group_exists:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Peer group '{group_name}' not found"
        )

    # Query peer_percentiles
    query = "SELECT * FROM peer_percentiles WHERE LOWER(peer_group) = LOWER(?)"
    params = [group_name]

    if year:
        query += " AND year = ?"
        params.append(year)
    else:
        # Get latest year available in peer_percentiles for this group
        query += """
            AND year = (
                SELECT MAX(year) FROM peer_percentiles 
                WHERE LOWER(peer_group) = LOWER(?)
            )
        """
        params.append(group_name)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    results = {}
    for row in rows:
        c_id = row["company_id"]
        if c_id not in results:
            results[c_id] = {
                "company_id": c_id,
                "peer_group": row["peer_group"],
                "year": row["year"],
                "metrics": {},
            }
        results[c_id]["metrics"][row["metric"]] = {
            "value": to_float(row["value"]),
            "percentile_rank": to_float(row["percentile_rank"]),
        }

    return list(results.values())


@router.get("/companies/{ticker}/peers/compare")
def get_peer_radar_comparison(
    ticker: str,
    year: str | None = Query(
        None, description="Optional year filter in YYYY-MM format"
    ),
):
    """
    Return radar comparison data: 8 axis metric values for the company + peer group average + benchmark company.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Get peer group of the company
    cursor.execute(
        """
        SELECT peer_group_name 
        FROM peer_groups 
        WHERE LOWER(company_id) = LOWER(?)
    """,
        (ticker,),
    )
    peer_grp_row = cursor.fetchone()
    if not peer_grp_row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"No peer group configuration found for company {ticker}",
        )

    group_name = peer_grp_row["peer_group_name"]

    # 2. Find latest conformed year for the group if not specified
    if not year:
        cursor.execute(
            """
            SELECT MAX(year) FROM peer_percentiles 
            WHERE LOWER(peer_group) = LOWER(?)
        """,
            (group_name,),
        )
        year = cursor.fetchone()[0]
        if not year:
            year = "2024-03"  # Fallback

    # 3. Query all peer group companies for this year
    cursor.execute(
        """
        SELECT pg.company_id, pg.is_benchmark, c.company_name
        FROM peer_groups pg
        JOIN companies c ON pg.company_id = c.company_id
        WHERE LOWER(pg.peer_group_name) = LOWER(?)
    """,
        (group_name,),
    )
    peers_list = cursor.fetchall()

    peer_tickers = [p["company_id"] for p in peers_list]
    benchmark_ticker = next(
        (p["company_id"] for p in peers_list if p["is_benchmark"] == 1), None
    )

    # Query ratios
    placeholders = ",".join(["?"] * len(peer_tickers))
    cursor.execute(
        f"""
        SELECT * FROM financial_ratios 
        WHERE company_id IN ({placeholders}) AND year LIKE '{year.split('-')[0]}-%'
    """,
        peer_tickers,
    )
    df_ratios = pd.DataFrame([dict(r) for r in cursor.fetchall()])

    # Query P&L and BS for ROCE calculation
    cursor.execute(
        f"SELECT company_id, year, profit_before_tax, interest, depreciation FROM profitandloss WHERE company_id IN ({placeholders}) AND year LIKE '{year.split('-')[0]}-%'",
        peer_tickers,
    )
    df_pl = pd.DataFrame([dict(r) for r in cursor.fetchall()])
    cursor.execute(
        f"SELECT company_id, year, equity_capital, reserves, borrowings FROM balancesheet WHERE company_id IN ({placeholders}) AND year LIKE '{year.split('-')[0]}-%'",
        peer_tickers,
    )
    df_bs = pd.DataFrame([dict(r) for r in cursor.fetchall()])

    conn.close()

    if df_ratios.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No financial data available for peer comparison in year {year}",
        )

    # Deduplicate years (prefer -03)
    df_ratios["is_null_roe"] = df_ratios["return_on_equity_pct"].isna()
    df_ratios["ends_with_03"] = df_ratios["year"].str.endswith("-03")
    df_ratios = df_ratios.sort_values(
        by=["company_id", "is_null_roe", "ends_with_03"], ascending=[True, True, False]
    ).drop_duplicates(subset=["company_id"], keep="first")

    # Compute ROCE
    df_roce = pd.merge(df_pl, df_bs, on=["company_id", "year"], how="inner")
    df_roce["roce"] = np.nan
    for idx, r in df_roce.iterrows():
        pbt = to_float(r.get("profit_before_tax"))
        interest = to_float(r.get("interest"))
        ebit = pbt + interest
        equity = to_float(r.get("equity_capital")) + to_float(r.get("reserves"))
        borrowings = to_float(r.get("borrowings"))
        cap_emp = equity + borrowings
        if cap_emp > 0:
            df_roce.at[idx, "roce"] = (ebit / cap_emp) * 100.0

    df_roce = df_roce.drop_duplicates(subset=["company_id"], keep="first")

    df_compare = pd.merge(
        df_ratios, df_roce[["company_id", "roce"]], on="company_id", how="left"
    )

    # 8 Axes
    axes = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR", "Rev CAGR", "EPS CAGR"]
    metrics_map = {
        "ROE": "return_on_equity_pct",
        "ROCE": "roce",
        "NPM": "net_profit_margin_pct",
        "D/E": "debt_to_equity",
        "FCF": "free_cash_flow_cr",
        "PAT CAGR": "pat_cagr_5yr",
        "Rev CAGR": "revenue_cagr_5yr",
        "EPS CAGR": "eps_cagr_5yr",
    }

    # Compute group averages
    group_avg = {}
    for axis in axes:
        col = metrics_map[axis]
        group_avg[axis] = to_float(df_compare[col].median())  # use median or mean

    # Selected company values
    comp_vals = {}
    df_comp_row = df_compare[df_compare["company_id"] == ticker.upper()]
    for axis in axes:
        col = metrics_map[axis]
        comp_vals[axis] = (
            to_float(df_comp_row[col].iloc[0]) if not df_comp_row.empty else None
        )

    # Benchmark company values
    bench_vals = {}
    df_bench_row = pd.DataFrame()
    if benchmark_ticker:
        df_bench_row = df_compare[df_compare["company_id"] == benchmark_ticker]
    for axis in axes:
        col = metrics_map[axis]
        bench_vals[axis] = (
            to_float(df_bench_row[col].iloc[0]) if not df_bench_row.empty else None
        )

    return {
        "ticker": ticker.upper(),
        "peer_group": group_name,
        "year": year,
        "axes": axes,
        "company_values": [comp_vals[ax] for ax in axes],
        "group_averages": [group_avg[ax] for ax in axes],
        "benchmark_ticker": benchmark_ticker,
        "benchmark_values": (
            [bench_vals[ax] for ax in axes] if benchmark_ticker else None
        ),
    }
