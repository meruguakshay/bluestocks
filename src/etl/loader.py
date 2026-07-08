import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from src.etl.normaliser import normalize_year, normalize_ticker

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def read_raw_file(filename: str) -> pd.DataFrame:
    """Reads Excel or CSV file from data/raw folder."""
    raw_dir = "data/raw"
    path = os.path.join(raw_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Source file {filename} not found in {raw_dir}")
        
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(path)
    elif filename.endswith('.csv'):
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {filename}")

def clean_companies(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes and deduplicates companies dataset."""
    df = df.copy()
    
    # Standardize ticker and NSE/BSE codes
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].apply(normalize_ticker)
    if 'nse_code' in df.columns:
        df['nse_code'] = df['nse_code'].apply(normalize_ticker)
    if 'bse_code' in df.columns:
        # BSE codes can be numeric or string, keep as string after cleaning
        df['bse_code'] = df['bse_code'].astype(str).str.strip().str.upper()
        
    # Deduplicate by company_id (DQ-01 PK uniqueness)
    initial_len = len(df)
    df = df.drop_duplicates(subset=['company_id'], keep='first')
    dedup_len = len(df)
    if initial_len > dedup_len:
         print(f"  [Loader] Deduplicated companies: removed {initial_len - dedup_len} duplicate PK rows.")
         
    return df

def clean_financials(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes year and deduplicates by composite PK (company_id, year)."""
    df = df.copy()
    
    # Normalize year column
    if 'year' in df.columns:
        df['year'] = df['year'].apply(normalize_year)
        # Drop rows where year could not be normalized
        df = df.dropna(subset=['year'])
        df['year'] = df['year'].astype(int)
        
    # Deduplicate by composite PK (company_id, year) (DQ-02 composite PK)
    initial_len = len(df)
    df = df.drop_duplicates(subset=['company_id', 'year'], keep='first')
    dedup_len = len(df)
    if initial_len > dedup_len:
         print(f"  [Loader] Deduplicated financials: removed {initial_len - dedup_len} duplicate PK rows.")
         
    return df

def clean_stock_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes stock prices by ticker."""
    df = df.copy()
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].apply(normalize_ticker)
    # Deduplicate by composite key (ticker, date)
    df = df.drop_duplicates(subset=['ticker', 'date'], keep='first')
    return df

def clean_generic(df: pd.DataFrame, pk_cols) -> pd.DataFrame:
    """Generic deduplication."""
    df = df.copy()
    if pk_cols:
         df = df.drop_duplicates(subset=pk_cols, keep='first')
    return df

def run_etl():
    print("=" * 60)
    print("RUNNING NIFTY 100 ETL PIPELINE")
    print("=" * 60)
    
    # 1. Load raw files
    files = {
        "sectors": "sectors.xlsx",
        "companies": "companies.xlsx",
        "profitandloss": "profitandloss.xlsx",
        "balancesheet": "balancesheet.xlsx",
        "cashflow": "cashflow.xlsx",
        "financial_ratios": "financial_ratios.xlsx",
        "stock_prices": "stock_prices.xlsx",
        "analysis": "analysis.csv",
        "documents": "documents.csv",
        "prosandcons": "prosandcons.csv",
        "peer_groups": "peer_groups.csv",
        "ticker_mapping": "ticker_mapping.csv"
    }
    
    raw_dfs = {}
    audit_records = []
    
    for table, filename in files.items():
        try:
            df = read_raw_file(filename)
            raw_dfs[table] = df
            print(f"[OK] Loaded {filename} ({len(df)} rows)")
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
            raise e

    # 2. Run Data Quality Rules (Validator) on raw data
    from src.etl.validator import DataQualityValidator
    validator = DataQualityValidator()
    print("\nRunning 16 data quality rules...")
    validator.run_validation(raw_dfs)
    print(f"Logged validations. Failures count: {len(validator.failures)}")

    # 3. Clean and deduplicate data to resolve CRITICAL errors
    print("\nCleaning and deduplicating data...")
    clean_dfs = {}
    
    clean_dfs["sectors"] = clean_generic(raw_dfs["sectors"], ["sector_id"])
    clean_dfs["companies"] = clean_companies(raw_dfs["companies"])
    clean_dfs["profitandloss"] = clean_financials(raw_dfs["profitandloss"])
    clean_dfs["balancesheet"] = clean_financials(raw_dfs["balancesheet"])
    clean_dfs["cashflow"] = clean_financials(raw_dfs["cashflow"])
    clean_dfs["financial_ratios"] = clean_financials(raw_dfs["financial_ratios"])
    clean_dfs["stock_prices"] = clean_stock_prices(raw_dfs["stock_prices"])
    clean_dfs["analysis"] = clean_generic(raw_dfs["analysis"], ["company_id"])
    clean_dfs["documents"] = clean_generic(raw_dfs["documents"], ["company_id", "doc_name"])
    clean_dfs["prosandcons"] = clean_generic(raw_dfs["prosandcons"], ["company_id"])
    clean_dfs["peer_groups"] = clean_generic(raw_dfs["peer_groups"], ["company_id", "peer_company_id"])
    clean_dfs["ticker_mapping"] = clean_generic(raw_dfs["ticker_mapping"], ["company_id"])

    # 4. Resolve FK orphans to satisfy constraints (CRITICAL failures)
    print("\nResolving Foreign Key orphans...")
    valid_sector_ids = set(clean_dfs["sectors"]["sector_id"].unique())
    
    # Filter companies to valid sectors
    clean_dfs["companies"] = clean_dfs["companies"][clean_dfs["companies"]["sector_id"].isin(valid_sector_ids)]
    
    # Update valid companies and tickers sets
    valid_company_ids = set(clean_dfs["companies"]["company_id"].unique())
    valid_tickers = set(clean_dfs["companies"]["ticker"].unique())

    # Filter all children tables to ensure FK integrity (DQ-03)
    clean_dfs["profitandloss"] = clean_dfs["profitandloss"][clean_dfs["profitandloss"]["company_id"].isin(valid_company_ids)]
    clean_dfs["balancesheet"] = clean_dfs["balancesheet"][clean_dfs["balancesheet"]["company_id"].isin(valid_company_ids)]
    clean_dfs["cashflow"] = clean_dfs["cashflow"][clean_dfs["cashflow"]["company_id"].isin(valid_company_ids)]
    clean_dfs["financial_ratios"] = clean_dfs["financial_ratios"][clean_dfs["financial_ratios"]["company_id"].isin(valid_company_ids)]
    clean_dfs["analysis"] = clean_dfs["analysis"][clean_dfs["analysis"]["company_id"].isin(valid_company_ids)]
    clean_dfs["documents"] = clean_dfs["documents"][clean_dfs["documents"]["company_id"].isin(valid_company_ids)]
    clean_dfs["prosandcons"] = clean_dfs["prosandcons"][clean_dfs["prosandcons"]["company_id"].isin(valid_company_ids)]
    clean_dfs["peer_groups"] = clean_dfs["peer_groups"][
        clean_dfs["peer_groups"]["company_id"].isin(valid_company_ids) & 
        clean_dfs["peer_groups"]["peer_company_id"].isin(valid_company_ids)
    ]
    clean_dfs["ticker_mapping"] = clean_dfs["ticker_mapping"][clean_dfs["ticker_mapping"]["company_id"].isin(valid_company_ids)]
    clean_dfs["stock_prices"] = clean_dfs["stock_prices"][clean_dfs["stock_prices"]["ticker"].isin(valid_tickers)]

    # Compute audit logs
    for table in files.keys():
        raw_count = len(raw_dfs[table])
        clean_count = len(clean_dfs[table])
        rejected = raw_count - clean_count
        audit_records.append({
            "table_name": table,
            "raw_row_count": raw_count,
            "clean_row_count": clean_count,
            "rejected_row_count": rejected,
            "status": "SUCCESS" if rejected == 0 else "CLEANED"
        })
        
    audit_df = pd.DataFrame(audit_records)
    os.makedirs("output", exist_ok=True)
    audit_df.to_csv("output/load_audit.csv", index=False)
    print("Saved load audit report to output/load_audit.csv")

    # 5. Initialize SQLite Database Schema
    print(f"\nInitializing Database: {DB_PATH}")
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
         os.makedirs(db_dir, exist_ok=True)
         
    conn = connect_db()
    with open("db/schema.sql", "r") as sf:
        schema_sql = sf.read()
    conn.executescript(schema_sql)
    conn.commit()
    print("Database schema loaded successfully.")

    # 6. Load data into SQLite
    print("\nLoading data to SQLite tables...")
    # Load in correct order to respect FK constraints
    load_order = [
        "sectors",
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "stock_prices",
        "analysis",
        "documents",
        "prosandcons",
        "peer_groups"
    ]
    
    for tbl_name in load_order:
         df = clean_dfs[tbl_name]
         # Clear old records first to avoid unique constraint issues if re-run
         conn.execute(f"DELETE FROM {tbl_name};")
         conn.commit()
         df.to_sql(tbl_name, con=conn, if_exists="append", index=False)
         print(f"  Loaded {tbl_name} ({len(df)} rows)")

    # 7. Check Foreign Keys
    print("\nRunning Foreign Key integrity check...")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    if violations:
        print(f"[CRITICAL] Foreign Key Violations Found: {violations}")
        conn.close()
        raise ValueError("Database load failed due to Foreign Key integrity violations.")
    else:
        print("[OK] Foreign Key checks passed with 0 violations.")
        
    conn.close()
    print("\nETL Pipeline completed successfully!")

if __name__ == "__main__":
    run_etl()
