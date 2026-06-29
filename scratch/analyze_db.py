import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    
    print("--- Database Tables ---")
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print(tables)
    
    for tbl in tables['name']:
        count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {tbl}", conn)['count'].iloc[0]
        print(f"Table: {tbl}, Row count: {count}")
        
    print("\n--- Scheme Details ---")
    dim_fund = pd.read_sql_query("SELECT * FROM dim_fund LIMIT 5", conn)
    print(dim_fund)
    
    print("\n--- NAV History Sample and Ranges ---")
    nav_range = pd.read_sql_query("SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(DISTINCT scheme_code) as num_schemes FROM fact_nav", conn)
    print(nav_range)
    
    print("\n--- Benchmark Data Sample ---")
    bench = pd.read_sql_query("SELECT * FROM benchmark_data LIMIT 10", conn)
    print(bench)
    
    print("\n--- Performance Data Sample ---")
    perf = pd.read_sql_query("SELECT * FROM fact_performance LIMIT 5", conn)
    print(perf)

    conn.close()

if __name__ == "__main__":
    main()
