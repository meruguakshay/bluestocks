import os
import sqlite3

import pandas as pd

DB_PATH = "db/nifty100.db"
ALLOC_FILE = "output/capital_allocation.csv"
CHANGES_FILE = "output/pattern_changes.csv"
os.makedirs("output", exist_ok=True)


def main():
    print("=" * 60)
    print("RUNNING CAPITAL ALLOCATION REPORT (DAY 32)")
    print("=" * 60)

    # 1. Verify existence of capital_allocation.csv
    if not os.path.exists(ALLOC_FILE):
        print(f"File {ALLOC_FILE} not found. Running ratios.py to generate it...")
        # Run src/analytics/ratios.py
        from src.analytics import ratios

        ratios.main()

    if not os.path.exists(ALLOC_FILE):
        raise FileNotFoundError(f"Failed to generate {ALLOC_FILE}")

    df_alloc = pd.read_csv(ALLOC_FILE)
    print(f"Loaded {len(df_alloc)} rows from {ALLOC_FILE}.")

    # Verify completeness: check unique companies
    conn = sqlite3.connect(DB_PATH)
    df_companies = pd.read_sql("SELECT company_id FROM companies", conn)
    conn.close()

    db_tickers = set(df_companies["company_id"])
    csv_tickers = set(df_alloc["company_id"])

    missing_tickers = db_tickers - csv_tickers
    print("Verification Check:")
    print(f"  Unique companies in SQLite: {len(db_tickers)}")
    print(f"  Unique companies in capital_allocation.csv: {len(csv_tickers)}")
    if len(missing_tickers) == 0:
        print("  [OK] All 92 companies are present in capital_allocation.csv.")
    else:
        print(f"  [WARNING] Missing companies in CSV: {missing_tickers}")

    # 2. Distribution summary for the latest year
    # Find the latest year for each company with complete data if available
    latest_records = []
    for comp_id, grp in df_alloc.groupby("company_id"):
        grp_sorted = grp.sort_values("year")
        grp_valid = grp_sorted[grp_sorted["pattern_label"] != "Unknown"]
        if not grp_valid.empty:
            latest_records.append(grp_valid.iloc[-1])
        else:
            latest_records.append(grp_sorted.iloc[-1])

    df_latest = pd.DataFrame(latest_records)
    dist_summary = df_latest["pattern_label"].value_counts()

    print("\nCapital Allocation Pattern Distribution (Latest Year):")
    for pattern, count in dist_summary.items():
        print(f"  - {pattern}: {count} companies")

    # 3. Build YoY pattern changes report
    pattern_changes = []
    for comp_id, grp in df_alloc.groupby("company_id"):
        grp_sorted = grp.sort_values("year")
        for i in range(1, len(grp_sorted)):
            prev_row = grp_sorted.iloc[i - 1]
            curr_row = grp_sorted.iloc[i]

            prev_pattern = prev_row["pattern_label"]
            curr_pattern = curr_row["pattern_label"]

            if prev_pattern != curr_pattern:
                pattern_changes.append(
                    {
                        "company_id": comp_id,
                        "previous_year": prev_row["year"],
                        "previous_pattern": prev_pattern,
                        "latest_year": curr_row["year"],
                        "latest_pattern": curr_pattern,
                    }
                )

    df_changes = pd.DataFrame(pattern_changes)
    df_changes.to_csv(CHANGES_FILE, index=False)
    print(
        f"\nSaved {len(df_changes)} year-over-year pattern changes to {CHANGES_FILE}."
    )
    if not df_changes.empty:
        print("Sample pattern changes:")
        print(df_changes.head(10).to_string(index=False))

    print("\nCapital Allocation Report finished successfully!")


if __name__ == "__main__":
    main()
