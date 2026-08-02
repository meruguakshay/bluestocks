import os
import sqlite3
import pandas as pd
from src.reports.tearsheet import generate_tearsheet
from src.reports.sector_report import generate_sector_report

DB_PATH = "db/nifty100.db"
SKIPPED_FILE = "output/skipped_tearsheets.csv"
os.makedirs("output", exist_ok=True)
os.makedirs("reports/tearsheets", exist_ok=True)
os.makedirs("reports/sector", exist_ok=True)

def main():
    print("=" * 60)
    print("STARTING BATCH REPORT GENERATION (DAY 34)")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    df_companies = pd.read_sql("SELECT company_id FROM companies", conn)
    df_sectors = pd.read_sql("SELECT sector_id, broad_sector FROM sectors", conn)
    conn.close()
    
    tickers = df_companies["company_id"].tolist()
    print(f"Total companies to process: {len(tickers)}")
    
    skipped_list = []
    generated_count = 0
    
    # 1. Batch Tearsheets
    for idx, ticker in enumerate(tickers):
        dest_path = f"reports/tearsheets/{ticker}_tearsheet.pdf"
        try:
            success = generate_tearsheet(ticker, dest_path)
            if success:
                generated_count += 1
                if generated_count % 10 == 0 or idx == len(tickers) - 1:
                    print(f"  [{idx+1}/{len(tickers)}] Generated tearsheet for {ticker}...")
            else:
                skipped_list.append({
                    "company_id": ticker,
                    "reason": "Less than 3 years of financial data"
                })
        except Exception as e:
            print(f"  [ERROR] Failed for {ticker}: {e}")
            skipped_list.append({
                "company_id": ticker,
                "reason": f"Exception: {str(e)}"
            })
            
    # Save skipped list to output/skipped_tearsheets.csv
    df_skipped = pd.DataFrame(skipped_list)
    df_skipped.to_csv(SKIPPED_FILE, index=False)
    print(f"\nGenerated {generated_count} tearsheet reports.")
    print(f"Skipped {len(skipped_list)} companies. Skipped list saved to {SKIPPED_FILE}.")
    if not df_skipped.empty:
        print("Skipped tickers:")
        print(df_skipped.to_string(index=False))
        
    # 2. Batch Sector Reports
    print("\nGenerating sector reports...")
    for idx, row in df_sectors.iterrows():
        sector_id = row["sector_id"]
        sector_name = row["broad_sector"]
        # Clean sector name for safe filename
        safe_name = sector_name.replace("/", "_").replace("&", "_")
        dest_path = f"reports/sector/{safe_name}_report.pdf"
        try:
            success = generate_sector_report(sector_id, sector_name, dest_path)
            if success:
                print(f"  Sector [{idx+1}/{len(df_sectors)}] Generated report for {sector_name} -> {dest_path}")
            else:
                print(f"  Sector [{idx+1}/{len(df_sectors)}] Skipped empty sector: {sector_name}")
        except Exception as e:
            print(f"  [ERROR] Failed for sector {sector_name}: {e}")
            
    print("\nBatch generation completed successfully!")

if __name__ == "__main__":
    main()
