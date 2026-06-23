"""
Day 1 — Data Ingestion
Tasks: Load CSVs, Explore fund_master, Validate AMFI codes
"""

import pandas as pd
import os

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

# ─────────────────────────────────────────────
# TASK 3 — Load all 10 CSV datasets
# ─────────────────────────────────────────────

CSV_FILES = [
    "fund_master.csv",
    "nav_history.csv",
    "portfolio_holdings.csv",
    "amc_details.csv",
    "scheme_details.csv",
    "returns_data.csv",
    "benchmark_data.csv",
    "risk_metrics.csv",
    "sip_data.csv",
    "investor_data.csv",
]

def load_all_csvs():
    dataframes = {}
    anomalies = []

    print("=" * 60)
    print("TASK 3 — Loading CSV Datasets")
    print("=" * 60)

    for file in CSV_FILES:
        path = os.path.join(RAW_DIR, file)
        if not os.path.exists(path):
            print(f"[SKIP] {file} — not found at {path}")
            continue

        df = pd.read_csv(path)
        name = file.replace(".csv", "")
        dataframes[name] = df

        print(f"\n{'─'*50}")
        print(f"File     : {file}")
        print(f"Shape    : {df.shape}  ({df.shape[0]} rows × {df.shape[1]} cols)")
        print(f"Dtypes:\n{df.dtypes}")
        print(f"Head:\n{df.head()}")

        # Anomaly checks
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if not null_cols.empty:
            anomalies.append(f"{file}: Nulls in → {null_cols.to_dict()}")

        dupes = df.duplicated().sum()
        if dupes > 0:
            anomalies.append(f"{file}: {dupes} duplicate rows")

    print("\n" + "=" * 60)
    print("ANOMALY SUMMARY")
    print("=" * 60)
    if anomalies:
        for a in anomalies:
            print(f"  ⚠  {a}")
    else:
        print("  ✓ No anomalies detected")

    return dataframes


# ─────────────────────────────────────────────
# TASK 6 — Explore Fund Master
# ─────────────────────────────────────────────

def explore_fund_master(dataframes):
    print("\n" + "=" * 60)
    print("TASK 6 — Fund Master Exploration")
    print("=" * 60)

    if "fund_master" not in dataframes:
        print("[SKIP] fund_master.csv not loaded")
        return

    df = dataframes["fund_master"]

    print(f"\nUnique Fund Houses  : {df['fund_house'].nunique()}")
    print(df['fund_house'].value_counts().to_string())

    print(f"\nCategories          : {df['category'].unique()}")
    print(f"Sub-categories      : {df['sub_category'].unique()}")
    print(f"Risk Grades         : {df['risk_grade'].unique()}")

    print(f"\nScheme code range   : {df['scheme_code'].min()} → {df['scheme_code'].max()}")
    print(f"Total schemes       : {df['scheme_code'].nunique()}")


# ─────────────────────────────────────────────
# TASK 7 — Validate AMFI Codes
# ─────────────────────────────────────────────

def validate_amfi_codes(dataframes):
    print("\n" + "=" * 60)
    print("TASK 7 — AMFI Code Validation")
    print("=" * 60)

    if "fund_master" not in dataframes or "nav_history" not in dataframes:
        print("[SKIP] fund_master or nav_history not loaded")
        return

    master_codes = set(dataframes["fund_master"]["scheme_code"].unique())
    nav_codes    = set(dataframes["nav_history"]["scheme_code"].unique())

    missing_in_nav  = master_codes - nav_codes
    extra_in_nav    = nav_codes - master_codes
    matched         = master_codes & nav_codes

    print(f"\nTotal codes in fund_master  : {len(master_codes)}")
    print(f"Total codes in nav_history  : {len(nav_codes)}")
    print(f"Matched codes               : {len(matched)}")
    print(f"In master, missing in NAV   : {len(missing_in_nav)}")
    print(f"In NAV, missing in master   : {len(extra_in_nav)}")

    summary = f"""
DATA QUALITY SUMMARY — AMFI Code Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total schemes in fund_master  : {len(master_codes)}
Matched with nav_history      : {len(matched)}
Missing NAV records           : {len(missing_in_nav)} (possibly inactive/new funds)
Orphan NAV codes              : {len(extra_in_nav)} (no master entry — possible feed gap)
Match rate                    : {round(len(matched)/len(master_codes)*100, 2)}%
"""
    print(summary)

    # Save summary to reports/
    os.makedirs("reports", exist_ok=True)
    with open("reports/data_quality_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    print("  ✓ Summary saved to reports/data_quality_summary.txt")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    dfs = load_all_csvs()
    explore_fund_master(dfs)
    validate_amfi_codes(dfs)
    print("\n✅ data_ingestion.py complete")
