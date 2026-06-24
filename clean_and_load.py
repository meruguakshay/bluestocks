"""
Day 2 — Clean Data + Load into SQLite DB
This script cleans raw CSVs, saves them to data/processed/, creates the SQLite database, and loads them.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

RAW_DIR = r"C:\Users\user\OneDrive\Desktop\project\data\raw"
PROCESSED_DIR = r"C:\Users\user\OneDrive\Desktop\project\data\processed"
DB_PATH = r"C:\Users\user\OneDrive\Desktop\project\bluestock_mf.db"
SCHEMA_PATH = r"C:\Users\user\OneDrive\Desktop\project\sql\schema.sql"

os.makedirs(PROCESSED_DIR, exist_ok=True)

# ────────────────────────────────────────────────────────
# CLEANING FUNCTIONS
# ────────────────────────────────────────────────────────

def clean_nav_history():
    print("Cleaning nav_history.csv...")
    path = os.path.join(RAW_DIR, "nav_history.csv")
    df = pd.read_csv(path)
    
    # 1. Parse dates to datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # 2. Remove duplicates
    df = df.drop_duplicates(subset=["scheme_code", "date"])
    
    # 3. Validate NAV > 0
    df = df[df["nav"] > 0]
    
    # 4. Sort and Forward fill missing NAV for holidays/weekends
    cleaned_groups = []
    for scheme_code, group in df.groupby("scheme_code"):
        group = group.sort_values("date")
        min_dt = group["date"].min()
        max_dt = group["date"].max()
        
        # Reindex to full daily range
        all_dates = pd.date_range(start=min_dt, end=max_dt, freq="D")
        group = group.set_index("date").reindex(all_dates)
        
        # Forward fill scheme_code and nav
        group["scheme_code"] = scheme_code
        group["nav"] = group["nav"].ffill()
        
        group = group.reset_index().rename(columns={"index": "date"})
        cleaned_groups.append(group)
        
    cleaned_df = pd.concat(cleaned_groups, ignore_index=True)
    cleaned_df["date"] = cleaned_df["date"].dt.strftime("%Y-%m-%d")
    return cleaned_df

def clean_investor_transactions():
    print("Cleaning investor_transactions.csv...")
    path = os.path.join(RAW_DIR, "investor_transactions.csv")
    df = pd.read_csv(path)
    
    # 1. Fix date formats
    df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True, errors="coerce")
    
    # 2. Standardize transaction_type (SIP/Lumpsum/Redemption)
    type_map = {
        "sip": "SIP",
        "lumpsum": "Lumpsum",
        "redemption": "Redemption"
    }
    df["transaction_type"] = (
        df["transaction_type"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(type_map)
        .fillna("Lumpsum")
    )
    
    # 3. Validate amount > 0
    df = df[df["amount"] > 0]
    
    # 4. Check KYC status enum values (Verified/Pending/Failed)
    def standardize_kyc(val):
        if pd.isna(val):
            return "Pending"
        v = str(val).strip().lower()
        if v in ("verified", "y", "yes", "true"):
            return "Verified"
        elif v in ("failed", "n", "no", "false"):
            return "Failed"
        elif v in ("pending",):
            return "Pending"
        return "Pending"
    
    df["kyc_status"] = df["kyc_status"].apply(standardize_kyc)
    
    # format date to string
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df.drop_duplicates()

def clean_scheme_performance():
    print("Cleaning scheme_performance.csv...")
    path = os.path.join(RAW_DIR, "scheme_performance.csv")
    df = pd.read_csv(path)
    
    # 1. Validate returns are numeric and standardize percentages
    for col in ["return_1yr", "return_3yr", "return_5yr"]:
        # strip % and convert to float
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("%", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
        # Impute missing values with median return of the column
        df[col] = df[col].fillna(df[col].median())
        
    # 2. Clean and standardize expense_ratio (should be numeric and between 0.1% and 2.5%)
    def parse_expense_ratio(val):
        if pd.isna(val):
            return 1.0 # default to 1.0%
        val_str = str(val).replace("%", "").strip()
        try:
            num = float(val_str)
            # If formatted as decimal (e.g. 0.015 instead of 1.5)
            if num <= 0.03: 
                num = num * 100
            return num
        except ValueError:
            return 1.0
            
    df["expense_ratio"] = df["expense_ratio"].apply(parse_expense_ratio)
    
    # Validate expense_ratio is in range 0.1% to 2.5%, clip values out of range
    df["expense_ratio"] = df["expense_ratio"].clip(0.1, 2.5)
    
    # 3. Flag anomalies (returns > 100% or < -50%)
    df["anomaly_flag"] = 0
    anomaly_cond = (
        (df["return_1yr"] > 100) | (df["return_1yr"] < -50) |
        (df["return_3yr"] > 100) | (df["return_3yr"] < -50) |
        (df["return_5yr"] > 100) | (df["return_5yr"] < -50)
    )
    df.loc[anomaly_cond, "anomaly_flag"] = 1
    
    # Report anomalies
    anomalies = df[df["anomaly_flag"] == 1]
    if len(anomalies) > 0:
        print(f"  [WARN] Found {len(anomalies)} performance anomalies:")
        print(anomalies[["scheme_code", "return_1yr", "return_3yr", "return_5yr"]])
        
    return df.drop_duplicates()

def clean_generic(filename):
    print(f"Standard cleaning for {filename}...")
    path = os.path.join(RAW_DIR, filename)
    df = pd.read_csv(path)
    return df.drop_duplicates().dropna(how="all")

# ────────────────────────────────────────────────────────
# MAIN PROCESSING AND LOADING
# ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("STARTING DATA CLEANING PROCESS")
    print("=" * 60)
    
    # Clean datasets
    cleaned_dfs = {}
    
    # Clean specific ones
    cleaned_dfs["nav_history"] = clean_nav_history()
    cleaned_dfs["investor_transactions"] = clean_investor_transactions()
    cleaned_dfs["scheme_performance"] = clean_scheme_performance()
    
    # Generic cleaning for others
    other_files = [
        "fund_master.csv",
        "portfolio_holdings.csv",
        "amc_details.csv",
        "scheme_details.csv",
        "returns_data.csv",
        "benchmark_data.csv",
        "risk_metrics.csv",
        "sip_data.csv",
        "investor_data.csv"
    ]
    
    for f in other_files:
        name = f.replace(".csv", "")
        cleaned_dfs[name] = clean_generic(f)
        
    # Save cleaned CSVs
    print("\nSaving cleaned CSVs to data/processed/...")
    for name, df in cleaned_dfs.items():
        processed_path = os.path.join(PROCESSED_DIR, f"{name}.csv")
        df.to_csv(processed_path, index=False)
        print(f"  [OK] Saved {name}.csv ({len(df)} rows)")
        
    # Generate dim_fund and dim_date for Star Schema
    print("\nGenerating Star Schema dimensions...")
    
    # Merge fund master and scheme details to get full fund info
    master_df = cleaned_dfs["fund_master"]
    details_df = cleaned_dfs["scheme_details"]
    dim_fund = pd.merge(master_df, details_df, on="scheme_code", how="inner").drop_duplicates()
    dim_fund = dim_fund[["scheme_code", "isin", "scheme_name", "fund_house", "category", "sub_category", "risk_grade"]]
    
    # Generate dim_date from NAV history and Transaction dates
    nav_dates = pd.to_datetime(cleaned_dfs["nav_history"]["date"])
    tx_dates = pd.to_datetime(cleaned_dfs["investor_transactions"]["date"])
    unique_dates = pd.concat([nav_dates, tx_dates]).drop_duplicates().dropna()
    
    dim_date = pd.DataFrame({"date": unique_dates})
    dim_date = dim_date.sort_values("date").reset_index(drop=True)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["day_of_week"] = dim_date["date"].dt.dayofweek + 1
    dim_date["is_weekend"] = dim_date["day_of_week"].isin([6, 7]).astype(int)
    dim_date["date"] = dim_date["date"].dt.strftime("%Y-%m-%d")
    
    # Save generated dimensions
    dim_fund.to_csv(os.path.join(PROCESSED_DIR, "dim_fund.csv"), index=False)
    dim_date.to_csv(os.path.join(PROCESSED_DIR, "dim_date.csv"), index=False)
    print("  [OK] Saved dim_fund.csv")
    print("  [OK] Saved dim_date.csv")

    # ────────────────────────────────────────────────────────
    # DATABASE SETUP AND LOADING
    # ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("INITIALIZING SQLITE DATABASE")
    print("=" * 60)
    
    # Run Schema SQL DDL statements
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(SCHEMA_PATH, "r") as sf:
        schema_sql = sf.read()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("  [OK] Database schema executed successfully from schema.sql.")
    
    # Create SQLAlchemy Engine
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # Map cleaned dataframes to tables
    load_mappings = {
        "dim_fund": dim_fund,
        "dim_date": dim_date,
        "fact_nav": cleaned_dfs["nav_history"][["scheme_code", "date", "nav"]],
        "fact_transactions": cleaned_dfs["investor_transactions"][["transaction_id", "investor_id", "scheme_code", "date", "transaction_type", "amount", "kyc_status", "state"]],
        "fact_performance": cleaned_dfs["scheme_performance"][["scheme_code", "return_1yr", "return_3yr", "return_5yr", "expense_ratio"]],
        "fact_aum": cleaned_dfs["amc_details"][["amc_id", "amc_name", "aum_crores"]],
        "portfolio_holdings": cleaned_dfs["portfolio_holdings"],
        "benchmark_data": cleaned_dfs["benchmark_data"],
        "risk_metrics": cleaned_dfs["risk_metrics"],
        "sip_data": cleaned_dfs["sip_data"],
        "investor_data": cleaned_dfs["investor_data"]
    }
    
    print("\nLoading tables into SQLite via SQLAlchemy...")
    verification_counts = []
    
    for tbl_name, df in load_mappings.items():
        # Load data (using append as schema is already created)
        df.to_sql(tbl_name, con=engine, if_exists="append", index=False)
        
        # Verify row counts
        with engine.connect() as con:
            res = con.execute(text(f"SELECT COUNT(*) FROM {tbl_name}"))
            db_count = res.scalar()
            
        csv_count = len(df)
        status = "MATCH" if csv_count == db_count else "MISMATCH"
        verification_counts.append({
            "Table": tbl_name,
            "CSV Row Count": csv_count,
            "DB Row Count": db_count,
            "Verification": status
        })
        print(f"  [{status}] Table: {tbl_name:<18} | CSV: {csv_count:<5} | DB: {db_count:<5}")
        
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    verify_df = pd.DataFrame(verification_counts)
    print(verify_df.to_string(index=False))
    
    print("\nSuccess: Data cleaning and database loading completed successfully!")

if __name__ == "__main__":
    main()
