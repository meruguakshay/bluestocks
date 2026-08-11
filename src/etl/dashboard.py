import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")


def connect_db():
    return sqlite3.connect(DB_PATH)


def main():
    print("=" * 60)
    print("GENERATING DASHBOARD VISUALS")
    print("=" * 60)

    conn = connect_db()
    os.makedirs("reports/charts", exist_ok=True)

    # Set seaborn style for clean, professional aesthetics
    sns.set_theme(style="whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 11

    # 1. Chart: Sector Distribution
    sectors_df = pd.read_sql_query(
        """
        SELECT s.broad_sector, COUNT(c.company_id) as count
        FROM companies c
        JOIN sectors s ON c.sector_id = s.sector_id
        GROUP BY s.broad_sector
        ORDER BY count DESC
    """,
        conn,
    )

    plt.figure()
    sns.barplot(data=sectors_df, x="count", y="broad_sector", palette="viridis")
    plt.title(
        "Nifty 100 Company Distribution across Sectors",
        fontsize=14,
        weight="bold",
        pad=15,
    )
    plt.xlabel("Number of Companies")
    plt.ylabel("Sector")
    plt.tight_layout()
    plt.savefig("reports/charts/sector_distribution.png", dpi=300)
    plt.close()
    print("[OK] Generated reports/charts/sector_distribution.png")

    # 2. Chart: Top 10 Companies by Revenue vs Profit in FY 2024
    latest_yr = pd.read_sql_query(
        "SELECT MAX(year) as max_yr FROM profitandloss", conn
    ).iloc[0]["max_yr"]

    pnl_df = pd.read_sql_query(
        f"""
        SELECT pnl.sales, pnl.net_profit, c.company_name, pnl.company_id
        FROM profitandloss pnl
        JOIN companies c ON pnl.company_id = c.company_id
        WHERE pnl.year = {latest_yr}
        ORDER BY pnl.sales DESC
        LIMIT 10
    """,
        conn,
    )

    plt.figure()
    # Melt dataframe for side-by-side bar plot
    melted = pd.melt(
        pnl_df,
        id_vars=["company_id"],
        value_vars=["sales", "net_profit"],
        var_name="Metric",
        value_name="Amount",
    )
    melted["Metric"] = melted["Metric"].map(
        {"sales": "Sales", "net_profit": "Net Profit"}
    )

    sns.barplot(data=melted, x="Amount", y="company_id", hue="Metric", palette="muted")
    plt.title(
        f"Top 10 Nifty 100 Companies by Sales vs Net Profit (FY {latest_yr})",
        fontsize=14,
        weight="bold",
        pad=15,
    )
    plt.xlabel("Amount (in Cr)")
    plt.ylabel("Company Ticker")
    plt.legend(title="Financial Metric")
    plt.tight_layout()
    plt.savefig("reports/charts/revenue_vs_profit_top10.png", dpi=300)
    plt.close()
    print("[OK] Generated reports/charts/revenue_vs_profit_top10.png")

    # 3. Chart: Return on Equity (ROE) distribution in FY 2024
    roe_df = pd.read_sql_query(
        f"""
        SELECT return_on_equity_pct
        FROM financial_ratios
        WHERE year = {latest_yr} AND return_on_equity_pct IS NOT NULL
    """,
        conn,
    )

    # Filter out extreme outliers for a clean visualization
    roe_clean = roe_df[
        (roe_df["return_on_equity_pct"] > -50) & (roe_df["return_on_equity_pct"] < 100)
    ]

    plt.figure()
    sns.histplot(
        data=roe_clean, x="return_on_equity_pct", kde=True, bins=20, color="teal"
    )
    plt.title(
        f"Distribution of Return on Equity (ROE %) in FY {latest_yr}",
        fontsize=14,
        weight="bold",
        pad=15,
    )
    plt.xlabel("ROE (%)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("reports/charts/roe_distribution.png", dpi=300)
    plt.close()
    print("[OK] Generated reports/charts/roe_distribution.png")

    conn.close()
    print("Dashboard visuals generation completed successfully!")


if __name__ == "__main__":
    main()
