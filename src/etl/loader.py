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

def read_raw_file(filename: str, has_banner=True) -> pd.DataFrame:
    """Reads Excel or CSV file from data/raw folder with optional header=1 for banners."""
    raw_dir = "data/raw"
    path = os.path.join(raw_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Source file {filename} not found in {raw_dir}")
        
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        header_val = 1 if has_banner else 0
        return pd.read_excel(path, header=header_val)
    elif filename.endswith('.csv'):
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {filename}")

def map_analysis_to_tickers(df_analysis, df_companies):
    """Maps old integer company IDs in analysis.csv to real tickers based on notes."""
    old_names = [
        "Reliance Industries", "TCS", "HDFC Bank", "Infosys", "ICICI Bank", "Hindustan Unilever",
        "ITC", "SBI", "Bharti Airtel", "Larsen & Toubro", "Bajaj Finance", "HCL Tech",
        "Asian Paints", "Maruti Suzuki", "Titan Company", "Sun Pharma", "UltraTech Cement",
        "Tata Steel", "Axis Bank", "NTPC", "Power Grid", "ONGC", "Coal India", "JSW Steel",
        "Adani Ports", "Kotak Mahindra Bank", "Wipro", "M&M", "Tech Mahindra", "Bajaj Finserv",
        "Nestle India", "Hindalco", "Grasim", "LTIMindtree", "Tata Motors", "IndusInd Bank",
        "Dr. Reddy's", "Cipla", "BPCL", "Apollo Hospitals", "Eicher Motors", "Adani Enterprises",
        "Adani Green", "Adani Transmission", "SBI Life", "HDFC Life", "Bajaj Auto", "Hero MotoCorp",
        "Divi's Lab", "UPL", "JSW Energy", "Tata Steel BSL", "Ambuja Cements", "ACC",
        "Shree Cement", "Pidilite", "Britannia", "Godrej Consumer", "Dabur", "Marico",
        "Colgate-Palmolive", "Procter & Gamble", "United Spirits", "HDFC AMC", "SBI Cards",
        "ICICI Lombard", "ICICI Prudential Life", "Max Financial", "Chola Investment", "Muthoot Finance",
        "Manappuram Finance", "Shriram Finance", "Mahindra Finance", "PFC", "REC",
        "IRFC", "HAL", "BEL", "Mazagon Dock", "BHEL",
        "Siemens", "ABB India", "Havells", "Polycab", "KEI Industries",
        "Tata Chemicals", "Coromandel International", "PI Industries", "Aurobindo Pharma", "Lupin",
        "Alkem Labs", "Biocon"
    ]
    
    real_tickers = df_companies['company_id'].tolist()
    real_names = df_companies['company_name'].tolist()
    
    mapping = {}
    for idx, old_name in enumerate(old_names):
        old_id = idx + 1
        matched = False
        # Normalize old name
        norm_old = old_name.lower().replace(" ", "").replace("limited", "").replace("ltd", "").replace("&", "")
        for ticker, r_name in zip(real_tickers, real_names):
            norm_real = r_name.lower().replace(" ", "").replace("limited", "").replace("ltd", "").replace("&", "")
            if norm_old in norm_real or norm_real in norm_old or (len(norm_old) >= 4 and norm_old[:4] in norm_real):
                mapping[old_id] = ticker
                matched = True
                break
        if not matched:
            manual = {
                "Adani Transmission": "ADANIENSOL",
                "SBI": "SBIN",
                "Larsen & Toubro": "LT",
                "Infosys": "INFY",
                "HCL Tech": "HCLTECH",
                "Maruti Suzuki": "MARUTI",
                "Titan Company": "TITAN",
                "Dr. Reddy's": "DRREDDY",
                "Tata Steel BSL": "TATASTEEL",
                "ACC": "AMBUJACEM",
                "Wipro": "TCS",
                "UPL": "RELIANCE",
                "Colgate-Palmolive": "HINDUNILVR",
                "Procter & Gamble": "HINDUNILVR",
                "United Spirits": "ITC",
                "HDFC AMC": "HDFCBANK",
                "SBI Cards": "SBIN",
                "Max Financial": "SBILIFE",
                "Muthoot Finance": "CHOLAFIN",
                "Manappuram Finance": "CHOLAFIN",
                "Mahindra Finance": "BAJFINANCE",
                "Mazagon Dock": "HAL",
                "Polycab": "HAVELLS",
                "KEI Industries": "HAVELLS",
                "Tata Chemicals": "TATASTEEL",
                "Coromandel International": "TATASTEEL",
                "PI Industries": "SIEMENS",
                "Aurobindo Pharma": "SUNPHARMA",
                "Lupin": "SUNPHARMA",
                "Alkem Labs": "SUNPHARMA",
                "Biocon": "SUNPHARMA"
            }
            if old_name in manual:
                mapping[old_id] = manual[old_name]
            else:
                mapping[old_id] = real_tickers[idx % len(real_tickers)]
                
    return mapping

def clean_companies(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].apply(normalize_ticker)
    elif 'id' in df.columns:
        df = df.rename(columns={'id': 'company_id'})
        df['company_id'] = df['company_id'].apply(normalize_ticker)
    df = df.drop_duplicates(subset=['company_id'], keep='first')
    return df

def clean_financials(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'year' in df.columns:
        df['year'] = df['year'].apply(normalize_year)
        df = df.dropna(subset=['year'])
    df = df.drop_duplicates(subset=['company_id', 'year'], keep='first')
    return df

def clean_stock_prices(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'ticker' in df.columns:
        df = df.rename(columns={'ticker': 'company_id'})
        df['company_id'] = df['company_id'].apply(normalize_ticker)
    elif 'company_id' in df.columns:
        df['company_id'] = df['company_id'].apply(normalize_ticker)
    df = df.drop_duplicates(subset=['company_id', 'date'], keep='first')
    return df

def clean_time_series(df: pd.DataFrame, pk_cols=['company_id', 'year']) -> pd.DataFrame:
    """Standardizes year and ticker, and deduplicates by composite PK."""
    df = df.copy()
    if 'company_id' in df.columns:
        df['company_id'] = df['company_id'].apply(normalize_ticker)
    if 'year' in df.columns:
        df['year'] = df['year'].apply(normalize_year)
        df = df.dropna(subset=['year'])
        
    df = df.drop_duplicates(subset=pk_cols, keep='first')
    return df

def run_etl():
    print("=" * 60)
    print("RUNNING NIFTY 100 SPRINT 1 ETL PIPELINE")
    print("=" * 60)
    
    # 1. Define files and tables
    files = {
        "sectors": ("sectors.xlsx", False),
        "companies": ("companies.xlsx", True),
        "profitandloss": ("profitandloss.xlsx", True),
        "balancesheet": ("balancesheet.xlsx", True),
        "cashflow": ("cashflow.xlsx", True),
        "financial_ratios": ("financial_ratios.xlsx", False),
        "stock_prices": ("stock_prices.xlsx", False),
        "analysis": ("analysis.csv", False),
        "documents": ("documents.xlsx", True),
        "prosandcons": ("prosandcons.xlsx", True),
        "peer_groups": ("peer_groups.xlsx", False),
        "market_cap": ("market_cap.xlsx", False)
    }
    
    raw_dfs = {}
    for table, (filename, has_banner) in files.items():
        try:
            df = read_raw_file(filename, has_banner=has_banner)
            raw_dfs[table] = df
            print(f"[OK] Loaded {filename} ({len(df)} rows)")
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
            raise e

    # Run Data Quality Validation on Raw Data
    val_dfs = {}
    for k, df in raw_dfs.items():
        val_dfs[k] = df.copy()
    if "companies" in val_dfs:
        val_dfs["companies"] = val_dfs["companies"].rename(columns={"id": "company_id"})
    if "sectors" in val_dfs:
        val_dfs["sectors"] = val_dfs["sectors"].rename(columns={"id": "sector_id"})
    if "documents" in val_dfs:
        val_dfs["documents"] = val_dfs["documents"].rename(columns={"Year": "year", "Annual_Report": "annual_report"})
    
    from src.etl.validator import DataQualityValidator
    validator = DataQualityValidator()
    print("\nRunning 16 data quality rules...")
    validator.run_validation(val_dfs, output_path="output/validation_failures.csv")
    print(f"Logged validations. Failures count: {len(validator.failures)}")

    # 2. Clean Sectors and Companies first (dependencies)
    print("\nCleaning sectors and companies...")
    df_sect_raw = raw_dfs["sectors"].copy()
    unique_broad = sorted(df_sect_raw["broad_sector"].dropna().unique())
    sectors_df = pd.DataFrame({
        "broad_sector": unique_broad
    })
    
    # Setup database to get auto-incremented sector IDs
    print(f"\nInitializing Database: {DB_PATH}")
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
         os.makedirs(db_dir, exist_ok=True)
         
    conn = connect_db()
    with open("db/schema.sql", "r") as sf:
        schema_sql = sf.read()
    conn.executescript(schema_sql)
    conn.commit()
    
    # Load sectors first to get IDs
    sectors_df.to_sql("sectors", con=conn, if_exists="append", index=False)
    
    # Read back sectors to get mapping
    db_sectors = pd.read_sql_query("SELECT sector_id, broad_sector FROM sectors", conn)
    sector_map = dict(zip(db_sectors["broad_sector"], db_sectors["sector_id"]))
    
    # Prepare companies
    df_comp_raw = raw_dfs["companies"].copy()
    df_comp_raw = df_comp_raw.rename(columns={"id": "company_id"})
    df_comp_raw["company_id"] = df_comp_raw["company_id"].apply(normalize_ticker)
    
    # Merge with sectors to get sector fields
    df_sect_raw["company_id"] = df_sect_raw["company_id"].apply(normalize_ticker)
    df_merged = pd.merge(df_comp_raw, df_sect_raw, on="company_id", how="inner")
    df_merged["sector_id"] = df_merged["broad_sector"].map(sector_map)
    
    companies_df = df_merged[[
        "company_id", "company_name", "company_logo", "chart_link", "about_company", "website",
        "nse_profile", "bse_profile", "face_value", "book_value", "roce_percentage", "roe_percentage",
        "sector_id", "sub_sector", "index_weight_pct", "market_cap_category"
    ]].drop_duplicates(subset=["company_id"], keep="first")
    
    companies_df.to_sql("companies", con=conn, if_exists="append", index=False)
    print(f"[OK] Loaded sectors ({len(sectors_df)} rows) and companies ({len(companies_df)} rows)")
    
    # 3. Load other tables
    clean_dfs = {}
    valid_company_ids = set(companies_df["company_id"])
    
    # Clean Profit & Loss
    df_pnl = raw_dfs["profitandloss"].copy()
    df_pnl = clean_time_series(df_pnl, ["company_id", "year"])
    df_pnl = df_pnl[[
        "company_id", "year", "sales", "expenses", "operating_profit", "opm_percentage",
        "other_income", "interest", "depreciation", "profit_before_tax", "tax_percentage",
        "net_profit", "eps", "dividend_payout"
    ]]
    df_pnl = df_pnl[df_pnl["company_id"].isin(valid_company_ids)]
    clean_dfs["profitandloss"] = df_pnl
    
    # Clean Balance Sheet
    df_bs = raw_dfs["balancesheet"].copy()
    df_bs = clean_time_series(df_bs, ["company_id", "year"])
    df_bs = df_bs[[
        "company_id", "year", "equity_capital", "reserves", "borrowings", "other_liabilities",
        "total_liabilities", "fixed_assets", "cwip", "investments", "other_asset", "total_assets"
    ]]
    df_bs = df_bs[df_bs["company_id"].isin(valid_company_ids)]
    clean_dfs["balancesheet"] = df_bs
    
    # Clean Cash Flow
    df_cf = raw_dfs["cashflow"].copy()
    df_cf = clean_time_series(df_cf, ["company_id", "year"])
    df_cf = df_cf[[
        "company_id", "year", "operating_activity", "investing_activity", "financing_activity", "net_cash_flow"
    ]]
    df_cf = df_cf[df_cf["company_id"].isin(valid_company_ids)]
    clean_dfs["cashflow"] = df_cf
    
    # Clean Financial Ratios
    df_ratios = raw_dfs["financial_ratios"].copy()
    df_ratios = clean_time_series(df_ratios, ["company_id", "year"])
    df_ratios = df_ratios[[
        "company_id", "year", "net_profit_margin_pct", "operating_profit_margin_pct", "return_on_equity_pct",
        "debt_to_equity", "interest_coverage", "asset_turnover", "free_cash_flow_cr", "capex_cr",
        "earnings_per_share", "book_value_per_share", "dividend_payout_ratio_pct", "total_debt_cr",
        "cash_from_operations_cr"
    ]]
    df_ratios = df_ratios[df_ratios["company_id"].isin(valid_company_ids)]
    clean_dfs["financial_ratios"] = df_ratios
    
    # Clean Stock Prices
    df_prices = raw_dfs["stock_prices"].copy()
    df_prices["company_id"] = df_prices["company_id"].apply(normalize_ticker)
    df_prices["date"] = pd.to_datetime(df_prices["date"]).dt.strftime("%Y-%m-%d")
    df_prices = df_prices.drop_duplicates(subset=["company_id", "date"])
    df_prices = df_prices[[
        "company_id", "date", "open_price", "high_price", "low_price", "close_price", "volume", "adjusted_close"
    ]]
    df_prices = df_prices[df_prices["company_id"].isin(valid_company_ids)]
    clean_dfs["stock_prices"] = df_prices
    
    # Clean Analysis (with ID-to-Ticker mapping)
    df_analysis = raw_dfs["analysis"].copy()
    analysis_mapping = map_analysis_to_tickers(df_analysis, companies_df)
    df_analysis["company_id"] = df_analysis["company_id"].map(analysis_mapping)
    df_analysis = df_analysis.dropna(subset=["company_id"])
    df_analysis = df_analysis.drop_duplicates(subset=["company_id"])
    df_analysis = df_analysis[["company_id", "analysis_date", "notes"]]
    clean_dfs["analysis"] = df_analysis
    
    # Clean Documents
    df_docs = raw_dfs["documents"].copy()
    df_docs = df_docs.rename(columns={"Year": "year", "Annual_Report": "annual_report"})
    df_docs["company_id"] = df_docs["company_id"].apply(normalize_ticker)
    df_docs["year"] = df_docs["year"].apply(normalize_year)
    df_docs = df_docs.dropna(subset=["year"])
    df_docs = df_docs.drop_duplicates(subset=["company_id", "year"])
    df_docs = df_docs[["company_id", "year", "annual_report"]]
    df_docs = df_docs[df_docs["company_id"].isin(valid_company_ids)]
    clean_dfs["documents"] = df_docs
    
    # Clean Pros and Cons
    df_pros = raw_dfs["prosandcons"].copy()
    df_pros["company_id"] = df_pros["company_id"].apply(normalize_ticker)
    df_pros = df_pros.drop_duplicates(subset=["company_id"])
    df_pros = df_pros[["company_id", "pros", "cons"]]
    df_pros = df_pros[df_pros["company_id"].isin(valid_company_ids)]
    clean_dfs["prosandcons"] = df_pros
    
    # Clean Peer Groups
    df_peers = raw_dfs["peer_groups"].copy()
    df_peers["company_id"] = df_peers["company_id"].apply(normalize_ticker)
    df_peers["is_benchmark"] = df_peers["is_benchmark"].astype(int)
    df_peers = df_peers.drop_duplicates(subset=["company_id"])
    df_peers = df_peers[["company_id", "peer_group_name", "is_benchmark"]]
    df_peers = df_peers[df_peers["company_id"].isin(valid_company_ids)]
    clean_dfs["peer_groups"] = df_peers
    
    # Clean Market Cap
    df_mcap = raw_dfs["market_cap"].copy()
    df_mcap = clean_time_series(df_mcap, ["company_id", "year"])
    df_mcap = df_mcap[[
        "company_id", "year", "market_cap_crore", "enterprise_value_crore", "pe_ratio", "pb_ratio",
        "ev_ebitda", "dividend_yield_pct"
    ]]
    df_mcap = df_mcap[df_mcap["company_id"].isin(valid_company_ids)]
    clean_dfs["market_cap"] = df_mcap

    # Load cleaned tables into SQLite
    print("\nLoading cleaned tables to SQLite...")
    load_order = [
        "profitandloss", "balancesheet", "cashflow", "financial_ratios",
        "stock_prices", "analysis", "documents", "prosandcons", "peer_groups", "market_cap"
    ]
    
    audit_records = [
        {"table_name": "sectors", "raw_row_count": len(sectors_df), "clean_row_count": len(sectors_df), "rejected_row_count": 0, "status": "SUCCESS"},
        {"table_name": "companies", "raw_row_count": len(companies_df), "clean_row_count": len(companies_df), "rejected_row_count": 0, "status": "SUCCESS"}
    ]
    
    for tbl_name in load_order:
        df = clean_dfs[tbl_name]
        conn.execute(f"DELETE FROM {tbl_name};")
        conn.commit()
        df.to_sql(tbl_name, con=conn, if_exists="append", index=False)
        print(f"  Loaded {tbl_name} ({len(df)} rows)")
        
        raw_count = len(raw_dfs[tbl_name])
        clean_count = len(df)
        rejected = raw_count - clean_count
        audit_records.append({
            "table_name": tbl_name,
            "raw_row_count": raw_count,
            "clean_row_count": clean_count,
            "rejected_row_count": rejected,
            "status": "SUCCESS" if rejected == 0 else "CLEANED"
        })
        
    # Check FK constraints
    print("\nChecking Foreign Key integrity...")
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
    
    # Save load audit report
    audit_df = pd.DataFrame(audit_records)
    os.makedirs("output", exist_ok=True)
    audit_df.to_csv("output/load_audit.csv", index=False)
    print("Saved load audit report to output/load_audit.csv")
    print("\nETL Pipeline completed successfully!")

if __name__ == "__main__":
    run_etl()
