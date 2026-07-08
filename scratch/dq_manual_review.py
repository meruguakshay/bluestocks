import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"

def manual_review():
    print("=" * 60)
    print("DATA QUALITY MANUAL REVIEW")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Select 5 random companies
    query_5_companies = """
    SELECT company_id, ticker, company_name 
    FROM companies 
    ORDER BY RANDOM() 
    LIMIT 5;
    """
    df_5 = pd.read_sql_query(query_5_companies, conn)
    print("5 Random Companies selected for manual review:")
    print(df_5.to_string(index=False))
    print("-" * 60)
    
    # 2. Check year coverage for these 5 companies in P&L
    for idx, r in df_5.iterrows():
         c_id = r["company_id"]
         c_name = r["company_name"]
         q_years = f"""
         SELECT year, sales, net_profit 
         FROM profitandloss 
         WHERE company_id = {c_id} 
         ORDER BY year;
         """
         df_years = pd.read_sql_query(q_years, conn)
         print(f"Year coverage for {c_name} (ID: {c_id}):")
         print(f"  Years Count: {len(df_years)}")
         print(f"  Years: {df_years['year'].tolist()}")
         print("-" * 60)
         
    # 3. Find any companies with <5 years of historical financial statements in P&L
    q_low_coverage = """
    SELECT c.company_id, c.company_name, COUNT(p.year) as year_count
    FROM companies c
    LEFT JOIN profitandloss p ON c.company_id = p.company_id
    GROUP BY c.company_id, c.company_name
    HAVING year_count < 5;
    """
    df_low = pd.read_sql_query(q_low_coverage, conn)
    print("Companies with <5 years of coverage:")
    if df_low.empty:
         print("  None. All companies have at least 5 years of P&L coverage.")
    else:
         print(df_low.to_string(index=False))
         
    conn.close()

if __name__ == "__main__":
    manual_review()
