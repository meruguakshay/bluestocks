import os
import sqlite3

import numpy as np
import pandas as pd

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "db", "nifty100.db")
MCAP_XLSX_PATH = os.path.join(BASE_DIR, "data", "raw", "market_cap.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("=" * 60)
    print("RUNNING VALUATION MODULE")
    print("=" * 60)

    # 1. Connect to SQLite DB and load company details and FCF
    conn = sqlite3.connect(DB_PATH)

    # Fetch companies and sectors
    query_comp = """
    SELECT c.company_id, c.company_name, s.broad_sector as sector
    FROM companies c
    LEFT JOIN sectors s ON c.sector_id = s.sector_id
    """
    df_comp = pd.read_sql(query_comp, conn)

    # Fetch ratios for 2024 (using our de-duplication selection logic)
    query_rat = "SELECT company_id, year, free_cash_flow_cr FROM financial_ratios WHERE year LIKE '2024-%'"
    df_rat_raw = pd.read_sql(query_rat, conn)

    # De-duplicate 2024 ratios: sort by company_id, then by non-null FCF first, then by March ending
    df_rat_raw["is_null_fcf"] = df_rat_raw["free_cash_flow_cr"].isna()
    df_rat_raw["ends_with_03"] = df_rat_raw["year"].str.endswith("-03")
    df_rat_sorted = df_rat_raw.sort_values(
        by=["company_id", "is_null_fcf", "ends_with_03"], ascending=[True, True, False]
    )
    df_rat = df_rat_sorted.drop_duplicates(subset=["company_id"], keep="first").copy()
    df_rat = df_rat[["company_id", "free_cash_flow_cr"]]

    conn.close()

    # 2. Read market_cap.xlsx
    if not os.path.exists(MCAP_XLSX_PATH):
        raise FileNotFoundError(f"Missing market cap file at {MCAP_XLSX_PATH}")

    df_mcap_all = pd.read_excel(MCAP_XLSX_PATH)

    # Normalize column names just in case
    df_mcap_all.columns = [c.strip() for c in df_mcap_all.columns]

    # Filter for year 2024 to get the latest market cap multiples
    # In the Excel file, year is stored as integer 2024
    df_mcap_2024 = df_mcap_all[df_mcap_all["year"] == 2024].copy()

    # 3. Calculate 5-year median PE (2020-2024) for each company
    df_mcap_5yr = df_mcap_all[
        df_mcap_all["year"].isin([2020, 2021, 2022, 2023, 2024])
    ].copy()
    # Filter positive PE ratios for a valid median calculation
    df_mcap_5yr_valid = df_mcap_5yr[df_mcap_5yr["pe_ratio"] > 0].copy()

    df_median_pe = (
        df_mcap_5yr_valid.groupby("company_id")["pe_ratio"].median().reset_index()
    )
    df_median_pe.columns = ["company_id", "5yr_median_PE"]

    # 4. Merge all data sources
    # Start with all 92 companies to ensure we have exactly 92 rows
    df_val = pd.merge(
        df_comp,
        df_mcap_2024[
            [
                "company_id",
                "market_cap_crore",
                "pe_ratio",
                "pb_ratio",
                "ev_ebitda",
                "dividend_yield_pct",
            ]
        ],
        on="company_id",
        how="left",
    )

    df_val = pd.merge(df_val, df_rat, on="company_id", how="left")
    df_val = pd.merge(df_val, df_median_pe, on="company_id", how="left")

    # 5. Compute FCF yield: FCF / market_cap_crore * 100
    df_val["FCF_yield_pct"] = (
        df_val["free_cash_flow_cr"] / df_val["market_cap_crore"]
    ) * 100.0

    # 6. Compute sector median P/E for each broad_sector in the latest year (2024)
    # Filter positive PE ratios for sector median P/E calculation
    df_positive_pe = df_val[
        (df_val["pe_ratio"].notna()) & (df_val["pe_ratio"] > 0)
    ].copy()
    df_sect_median = df_positive_pe.groupby("sector")["pe_ratio"].median().reset_index()
    df_sect_median.columns = ["sector", "sector_median_PE"]

    # Merge sector median back
    df_val = pd.merge(df_val, df_sect_median, on="sector", how="left")

    # 7. Compute PE_vs_sector_median_pct and apply flags
    pe_vs_list = []
    flags = []

    for idx, row in df_val.iterrows():
        pe = row["pe_ratio"]
        sec_med = row["sector_median_PE"]

        # Calculate PE vs Sector Median %
        if pd.notna(pe) and pd.notna(sec_med) and sec_med > 0:
            pe_vs_pct = ((pe - sec_med) / sec_med) * 100.0
        else:
            pe_vs_pct = np.nan
        pe_vs_list.append(pe_vs_pct)

        # Apply Overvaluation flag logic
        # if P/E is null or negative, default to 'Fair' or check
        if pd.isna(pe) or pe <= 0 or pd.isna(sec_med) or sec_med <= 0:
            flags.append("Fair")
        elif pe > sec_med * 1.5:
            flags.append("Caution")
        elif pe < sec_med * 0.7:
            flags.append("Discount")
        else:
            flags.append("Fair")

    df_val["PE_vs_sector_median_pct"] = pe_vs_list
    df_val["flag"] = flags

    # 8. Create final summary output dataframe
    # Columns required: company_id, company_name, sector, P/E, P/B, EV/EBITDA, FCF_yield_pct, 5yr_median_PE, PE_vs_sector_median_pct, flag
    df_summary = df_val[
        [
            "company_id",
            "company_name",
            "sector",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ].copy()

    df_summary.columns = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    # 9. Save valuation_summary.xlsx
    summary_path = os.path.join(OUTPUT_DIR, "valuation_summary.xlsx")
    df_summary.to_excel(summary_path, index=False)
    print(f"  [OK] Saved {len(df_summary)} rows to {summary_path}")

    # 10. Filter and save valuation_flags.csv (only Caution and Discount flagged)
    df_flags = df_summary[df_summary["flag"].isin(["Caution", "Discount"])].copy()
    flags_path = os.path.join(OUTPUT_DIR, "valuation_flags.csv")
    df_flags.to_csv(flags_path, index=False)
    print(f"  [OK] Saved {len(df_flags)} rows of flagged companies to {flags_path}")

    print("\nValuation processing completed successfully!")


if __name__ == "__main__":
    main()
