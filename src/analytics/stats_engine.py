import os
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")


def main():
    print("=" * 60)
    print("STARTING PORTFOLIO STATISTICS & PEER ANALYTICS (DAY 37)")
    print("=" * 60)

    # 1. Connect to DB
    conn = sqlite3.connect(DB_PATH)

    # Load companies, sectors, ratios, and market cap
    df_comps = pd.read_sql_query(
        "SELECT c.company_id, c.company_name, s.broad_sector as sector FROM companies c JOIN sectors s ON c.sector_id = s.sector_id",
        conn,
    )
    df_ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios WHERE year LIKE '2024-%'", conn
    )

    # Deduplicate ratios for latest conformed year 2024
    df_ratios["is_null_roe"] = df_ratios["return_on_equity_pct"].isna()
    df_ratios["ends_with_03"] = df_ratios["year"].str.endswith("-03")
    df_ratios = df_ratios.sort_values(
        by=["company_id", "is_null_roe", "ends_with_03"], ascending=[True, True, False]
    ).drop_duplicates(subset=["company_id"], keep="first")

    df_mcap = pd.read_sql_query(
        "SELECT * FROM market_cap WHERE year LIKE '2024-%'", conn
    )
    df_mcap = df_mcap.drop_duplicates(subset=["company_id"], keep="first")

    # Merge datasets
    df_data = pd.merge(df_comps, df_ratios, on="company_id", how="inner")
    df_data = pd.merge(
        df_data,
        df_mcap[["company_id", "pe_ratio", "pb_ratio", "dividend_yield_pct"]],
        on="company_id",
        how="left",
    )

    # Define the 10 KPIs
    kpi_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "interest_coverage",
    ]

    # Impute missing values with sector median for Z-scores and Correlation
    df_imputed = df_data.copy()
    for col in kpi_cols:
        sector_medians = df_imputed.groupby("sector")[col].transform("median")
        df_imputed[col] = df_imputed[col].fillna(sector_medians)
        global_median = df_imputed[col].median()
        df_imputed[col] = df_imputed[col].fillna(global_median)

    # ────────────────────────────────────────────────────────
    # 2. Correlation Matrix Heatmap
    # ────────────────────────────────────────────────────────
    corr_df = df_imputed[kpi_cols].copy()
    corr_df.columns = [
        "ROE (%)",
        "D/E",
        "FCF (Cr)",
        "Rev CAGR 5yr (%)",
        "PAT CAGR 5yr (%)",
        "OPM (%)",
        "P/E",
        "P/B",
        "Div Yield (%)",
        "ICR",
    ]
    corr_matrix = corr_df.corr(method="pearson")

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5,
        annot_kws={"size": 8},
    )
    plt.title(
        "Pearson Correlation Heatmap of 10 Core KPIs (Latest Year)",
        fontweight="bold",
        pad=15,
    )
    plt.tight_layout()
    os.makedirs("reports", exist_ok=True)
    plt.savefig("reports/correlation_heatmap.png", dpi=300)
    plt.close()
    print("[OK] Saved correlation heatmap to reports/correlation_heatmap.png")

    # ────────────────────────────────────────────────────────
    # 3. Outlier Detection (Z-score > 3 per sector)
    # ────────────────────────────────────────────────────────
    outliers = []
    # Calculate Z-score for each metric per broad_sector
    for sector, grp in df_imputed.groupby("sector"):
        for col in kpi_cols:
            vals = grp[col].values
            if len(grp) < 3:  # Not enough points to calculate z-score reliably
                continue
            mean_val = vals.mean()
            std_val = vals.std(ddof=1) if vals.std(ddof=1) > 0 else 0.0

            if std_val > 0:
                for idx, r in grp.iterrows():
                    val = r[col]
                    z = (val - mean_val) / std_val
                    if abs(z) > 3.0:
                        outliers.append(
                            {
                                "company_id": r["company_id"],
                                "metric": col,
                                "value": round(val, 4),
                                "z_score": round(z, 4),
                                "sector": sector,
                                "sector_mean": round(mean_val, 4),
                                "sector_std": round(std_val, 4),
                            }
                        )

    outlier_df = pd.DataFrame(outliers)
    os.makedirs("output", exist_ok=True)
    if outlier_df.empty:
        outlier_df = pd.DataFrame(
            columns=[
                "company_id",
                "metric",
                "value",
                "z_score",
                "sector",
                "sector_mean",
                "sector_std",
            ]
        )
    outlier_df.to_csv("output/outlier_report.csv", index=False)
    print(f"[OK] Saved {len(outlier_df)} outliers to output/outlier_report.csv")

    # ────────────────────────────────────────────────────────
    # 4. Portfolio Stats (P10, P25, P50, P75, P90, Mean, Std)
    # ────────────────────────────────────────────────────────
    stats_rows = []
    kpi_names_map = {
        "return_on_equity_pct": "ROE (%)",
        "debt_to_equity": "D/E Ratio",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Revenue CAGR 5yr (%)",
        "pat_cagr_5yr": "PAT CAGR 5yr (%)",
        "operating_profit_margin_pct": "OPM (%)",
        "pe_ratio": "P/E Ratio",
        "pb_ratio": "P/B Ratio",
        "dividend_yield_pct": "Dividend Yield (%)",
        "interest_coverage": "ICR",
    }

    for col in kpi_cols:
        vals = df_data[col].dropna()
        if len(vals) > 0:
            stats_rows.append(
                {
                    "Metric": kpi_names_map[col],
                    "P10": round(vals.quantile(0.10), 4),
                    "P25": round(vals.quantile(0.25), 4),
                    "P50": round(vals.quantile(0.50), 4),
                    "P75": round(vals.quantile(0.75), 4),
                    "P90": round(vals.quantile(0.90), 4),
                    "Mean": round(vals.mean(), 4),
                    "Std": round(vals.std(), 4),
                }
            )

    portfolio_stats_df = pd.DataFrame(stats_rows)
    portfolio_stats_df.to_csv("output/portfolio_stats.csv", index=False)
    print("[OK] Saved portfolio stats to output/portfolio_stats.csv")

    # ────────────────────────────────────────────────────────
    # 5. Populate peer_percentiles table
    # ────────────────────────────────────────────────────────
    print("Populating peer_percentiles table...")
    # Create table if not exists
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS peer_percentiles (
        company_id TEXT,
        peer_group TEXT NOT NULL,
        metric TEXT NOT NULL,
        value REAL,
        percentile_rank REAL,
        year TEXT,
        PRIMARY KEY (company_id, metric, year),
        FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
    );
    """)
    conn.commit()

    # Load peer group configurations
    df_peers = pd.read_sql_query("SELECT * FROM peer_groups", conn)

    # Query all years from financial_ratios and market_cap to calculate percentiles historically
    df_all_ratios = pd.read_sql_query(
        "SELECT company_id, year, return_on_equity_pct, debt_to_equity, free_cash_flow_cr, revenue_cagr_5yr, pat_cagr_5yr, operating_profit_margin_pct, interest_coverage, net_profit_margin_pct, eps_cagr_5yr FROM financial_ratios",
        conn,
    )
    df_all_mcap = pd.read_sql_query(
        "SELECT company_id, year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap",
        conn,
    )

    # Calculate ROCE dynamically just like the dashboard does
    df_all_pl = pd.read_sql_query(
        "SELECT company_id, year, profit_before_tax, interest, depreciation FROM profitandloss",
        conn,
    )
    df_all_bs = pd.read_sql_query(
        "SELECT company_id, year, equity_capital, reserves, borrowings FROM balancesheet",
        conn,
    )

    # Merge for ROCE calculation
    df_roce_calc = pd.merge(
        df_all_pl, df_all_bs, on=["company_id", "year"], how="inner"
    )
    df_roce_calc["roce"] = np.nan
    for idx, r in df_roce_calc.iterrows():
        pbt = to_float(r.get("profit_before_tax"))
        interest = to_float(r.get("interest"))
        ebit = pbt + interest
        equity = to_float(r.get("equity_capital")) + to_float(r.get("reserves"))
        borrowings = to_float(r.get("borrowings"))
        cap_emp = equity + borrowings
        if cap_emp > 0:
            df_roce_calc.at[idx, "roce"] = (ebit / cap_emp) * 100.0

    # Combine all metrics in a single dataframe
    df_metrics = pd.merge(
        df_all_ratios, df_all_mcap, on=["company_id", "year"], how="outer"
    )
    df_metrics = pd.merge(
        df_metrics,
        df_roce_calc[["company_id", "year", "roce"]],
        on=["company_id", "year"],
        how="left",
    )
    df_metrics = pd.merge(df_metrics, df_peers, on="company_id", how="inner")

    # The 10 metrics for percentile ranks
    percentile_metrics = [
        "return_on_equity_pct",
        "roce",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "eps_cagr_5yr",
        "pe_ratio",
        "pb_ratio",
    ]

    peer_percentile_records = []

    # Calculate percentiles partition by peer_group and year
    for (group_name, year_val), grp in df_metrics.groupby(["peer_group_name", "year"]):
        for col in percentile_metrics:
            valid_grp = grp.dropna(subset=[col])
            n = len(valid_grp)
            if n == 0:
                continue

            # Rank values within group
            ranks = valid_grp[col].rank(method="min")

            for idx, r in valid_grp.iterrows():
                val = r[col]
                rk = ranks.loc[idx]
                pct_rank = (rk - 1) / (n - 1) if n > 1 else 1.0

                peer_percentile_records.append(
                    {
                        "company_id": r["company_id"],
                        "peer_group": group_name,
                        "metric": col,
                        "value": round(val, 4),
                        "percentile_rank": round(pct_rank, 4),
                        "year": year_val,
                    }
                )

    if peer_percentile_records:
        peer_pct_df = pd.DataFrame(peer_percentile_records)
        cursor.execute("DELETE FROM peer_percentiles;")
        conn.commit()
        peer_pct_df.to_sql(
            "peer_percentiles", con=conn, if_exists="append", index=False
        )
        print(f"[OK] Loaded {len(peer_pct_df)} records into peer_percentiles table.")

    conn.close()


def to_float(val):
    if val is None or pd.isna(val):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0


if __name__ == "__main__":
    main()
