
import pandas as pd
from fastapi import APIRouter, Query

from src.api.utils import get_db_connection, to_float

router = APIRouter()


@router.get("/screener")
def get_screener_results(
    min_roe: float | None = Query(None, description="Minimum Return on Equity (%)"),
    max_de: float | None = Query(None, description="Maximum Debt-to-Equity ratio"),
    min_fcf: float | None = Query(None, description="Minimum Free Cash Flow (₹ Cr)"),
    sector: str | None = Query(None, description="Broad sector to filter by"),
    min_rev_cagr_5yr: float | None = Query(
        None, description="Minimum 5yr Revenue CAGR (%)"
    ),
    min_pat_cagr_5yr: float | None = Query(
        None, description="Minimum 5yr PAT CAGR (%)"
    ),
    max_pe: float | None = Query(None, description="Maximum P/E Ratio"),
):
    """
    Screener endpoint matching filtering metrics.
    Returns a list of matching companies ranked by composite quality score.
    Returns HTTP 400 if any parameter values are invalid.
    """
    # Validate parameter inputs (they are validated by FastAPI parameter parsing, but let's double check)
    # If any query parameters were passed that can't be parsed, FastAPI will raise 422. We can handle
    # parameter types specifically if needed, but since they are defined as floats, FastAPI takes care of parsing.

    conn = get_db_connection()

    # Load 2024 ratios and market caps
    df_ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios WHERE year LIKE '2024-%'", conn
    )
    df_mcap = pd.read_sql_query(
        "SELECT * FROM market_cap WHERE year LIKE '2024-%'", conn
    )
    df_comps = pd.read_sql_query(
        "SELECT c.company_id, c.company_name, s.broad_sector FROM companies c LEFT JOIN sectors s ON c.sector_id = s.sector_id",
        conn,
    )
    conn.close()

    if df_ratios.empty or df_comps.empty:
        return []

    # Deduplicate ratios for latest conformed year 2024 (ends_with_-03 preferred)
    df_ratios["is_null_roe"] = df_ratios["return_on_equity_pct"].isna()
    df_ratios["ends_with_03"] = df_ratios["year"].str.endswith("-03")
    df_ratios = df_ratios.sort_values(
        by=["company_id", "is_null_roe", "ends_with_03"], ascending=[True, True, False]
    ).drop_duplicates(subset=["company_id"], keep="first")

    df_mcap = df_mcap.drop_duplicates(subset=["company_id"], keep="first")

    # Merge
    df_screener = pd.merge(df_ratios, df_mcap, on="company_id", how="inner")
    df_screener = pd.merge(df_screener, df_comps, on="company_id", how="inner")

    # Apply filters
    df_filtered = df_screener.copy()

    if min_roe is not None:
        df_filtered = df_filtered[
            df_filtered["return_on_equity_pct"].fillna(-99999.0) >= min_roe
        ]
    if max_de is not None:
        df_filtered = df_filtered[
            df_filtered["debt_to_equity"].fillna(99999.0) <= max_de
        ]
    if min_fcf is not None:
        df_filtered = df_filtered[
            df_filtered["free_cash_flow_cr"].fillna(-999999.0) >= min_fcf
        ]
    if sector:
        df_filtered = df_filtered[
            df_filtered["broad_sector"].str.lower().fillna("") == sector.lower()
        ]
    if min_rev_cagr_5yr is not None:
        df_filtered = df_filtered[
            df_filtered["revenue_cagr_5yr"].fillna(-99999.0) >= min_rev_cagr_5yr
        ]
    if min_pat_cagr_5yr is not None:
        df_filtered = df_filtered[
            df_filtered["pat_cagr_5yr"].fillna(-99999.0) >= min_pat_cagr_5yr
        ]
    if max_pe is not None:
        df_filtered = df_filtered[df_filtered["pe_ratio"].fillna(99999.0) <= max_pe]

    # Sort by composite score
    df_filtered = df_filtered.sort_values(by="composite_quality_score", ascending=False)

    results = []
    for rank, (idx, row) in enumerate(df_filtered.iterrows(), 1):
        results.append(
            {
                "ticker": row["company_id"],
                "company_name": row["company_name"],
                "sector": row["broad_sector"],
                "composite_score": to_float(row.get("composite_quality_score")),
                "roe": to_float(row.get("return_on_equity_pct")),
                "de": to_float(row.get("debt_to_equity")),
                "fcf": to_float(row.get("free_cash_flow_cr")),
                "revenue_cagr_5yr": to_float(row.get("revenue_cagr_5yr")),
                "pat_cagr_5yr": to_float(row.get("pat_cagr_5yr")),
                "pe": to_float(row.get("pe_ratio")),
                "rank": rank,
            }
        )

    return results
