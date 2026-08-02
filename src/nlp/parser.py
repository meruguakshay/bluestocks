import os
import re
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "db/nifty100.db"
RAW_FILE = "data/raw/analysis.xlsx"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_text(text, pattern):
    if pd.isna(text) or not isinstance(text, str):
        return None
    match = re.search(pattern, text)
    if match:
        period = int(match.group(1))
        val = float(match.group(2))
        return period, val
    return None

def main():
    print("=" * 60)
    print("RUNNING ANALYSIS TEXT PARSER (DAY 29)")
    print("=" * 60)
    
    if not os.path.exists(RAW_FILE):
        raise FileNotFoundError(f"Source file {RAW_FILE} not found.")
        
    df_raw = pd.read_excel(RAW_FILE)
    print(f"Loaded {len(df_raw)} rows from {RAW_FILE}.")
    
    # Target columns
    target_cols = [
        "compounded_sales_growth", 
        "compounded_profit_growth", 
        "stock_price_cagr", 
        "roe"
    ]
    
    regex_pattern = r"(\d+)\s*Years?:?\s*([\d.]+)%"
    
    parsed_records = []
    failure_records = []
    
    for _, row in df_raw.iterrows():
        comp_id = row["company_id"]
        for col in target_cols:
            val = row[col]
            if pd.isna(val):
                continue
            
            parsed = parse_text(str(val).strip(), regex_pattern)
            if parsed:
                period_years, value_pct = parsed
                parsed_records.append({
                    "company_id": comp_id,
                    "metric_type": col,
                    "period_years": period_years,
                    "value_pct": value_pct
                })
            else:
                failure_records.append({
                    "company_id": comp_id,
                    "column_name": col,
                    "raw_value": val
                })
                
    # Save parsed records to output/analysis_parsed.csv
    df_parsed = pd.DataFrame(parsed_records)
    if not df_parsed.empty:
        df_parsed.to_csv(os.path.join(OUTPUT_DIR, "analysis_parsed.csv"), index=False)
        print(f"Saved {len(df_parsed)} parsed rows to output/analysis_parsed.csv")
    else:
        # Create empty CSV with columns
        df_empty = pd.DataFrame(columns=["company_id", "metric_type", "period_years", "value_pct"])
        df_empty.to_csv(os.path.join(OUTPUT_DIR, "analysis_parsed.csv"), index=False)
        print("No parsed rows. Saved empty output/analysis_parsed.csv")
        
    # Save failure records to output/parse_failures.csv
    df_failures = pd.DataFrame(failure_records)
    df_failures.to_csv(os.path.join(OUTPUT_DIR, "parse_failures.csv"), index=False)
    print(f"Saved {len(df_failures)} parsing failures to output/parse_failures.csv")
    
    # ────────────────────────────────────────────────────────
    # CROSS-VALIDATION
    # ────────────────────────────────────────────────────────
    print("\nRunning cross-validation against Ratio Engine...")
    conn = sqlite3.connect(DB_PATH)
    
    # Query latest conformed ratios per company
    # We find the latest year for each company from financial_ratios table
    query_latest = """
    with latest_years as (
        select company_id, max(year) as max_yr
        from financial_ratios
        group by company_id
    )
    select fr.company_id, fr.year, fr.revenue_cagr_5yr, fr.pat_cagr_5yr, fr.return_on_equity_pct
    from financial_ratios fr
    join latest_years ly on fr.company_id = ly.company_id and fr.year = ly.max_yr
    """
    df_db_ratios = pd.read_sql(query_latest, conn)
    conn.close()
    
    db_ratios_dict = df_db_ratios.set_index("company_id").to_dict(orient="index")
    
    cross_val_records = []
    
    # Perform comparison for 5-year period for sales growth and profit growth
    for record in parsed_records:
        comp_id = record["company_id"]
        metric = record["metric_type"]
        period = record["period_years"]
        parsed_val = record["value_pct"]
        
        # We only compare 5-year metrics (since database has revenue_cagr_5yr, pat_cagr_5yr)
        if period != 5:
            continue
            
        computed_val = None
        db_data = db_ratios_dict.get(comp_id)
        if not db_data:
            continue
            
        if metric == "compounded_sales_growth":
            computed_val = db_data.get("revenue_cagr_5yr")
        elif metric == "compounded_profit_growth":
            computed_val = db_data.get("pat_cagr_5yr")
            
        if computed_val is not None and pd.notna(computed_val):
            divergence = abs(parsed_val - computed_val)
            diverged_gt_5 = 1 if divergence > 5.0 else 0
            cross_val_records.append({
                "company_id": comp_id,
                "metric_type": metric,
                "period_years": period,
                "parsed_value_pct": parsed_val,
                "computed_value_pct": round(computed_val, 4),
                "divergence_pct": round(divergence, 4),
                "diverged_gt_5": diverged_gt_5
            })
            
    df_cross_val = pd.DataFrame(cross_val_records)
    if not df_cross_val.empty:
        df_cross_val.to_csv(os.path.join(OUTPUT_DIR, "cross_validation.csv"), index=False)
        print(f"Saved {len(df_cross_val)} cross-validation rows to output/cross_validation.csv")
        diverged_count = df_cross_val["diverged_gt_5"].sum()
        print(f"  Flagged {diverged_count} records with divergence > 5%")
        if diverged_count > 0:
            print("  Divergent entries:")
            print(df_cross_val[df_cross_val["diverged_gt_5"] == 1][["company_id", "metric_type", "parsed_value_pct", "computed_value_pct", "divergence_pct"]])
    else:
        df_empty_cv = pd.DataFrame(columns=["company_id", "metric_type", "period_years", "parsed_value_pct", "computed_value_pct", "divergence_pct", "diverged_gt_5"])
        df_empty_cv.to_csv(os.path.join(OUTPUT_DIR, "cross_validation.csv"), index=False)
        print("No conformed 5-year growth values to cross-validate. Saved empty output/cross_validation.csv")
        
    print("\nAnalysis text parser completed successfully!")

if __name__ == "__main__":
    main()
