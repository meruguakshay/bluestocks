import sqlite3
import pandas as pd
import re

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
QUERIES_PATH = os.path.join(BASE_DIR, "sql", "queries.sql")


def run_queries():
    conn = sqlite3.connect(DB_PATH)
    
    with open(QUERIES_PATH, "r") as qf:
        sql_content = qf.read()
        
    # Split queries by double dashes indicating comments
    # We will split on a regex that matches the query headers (e.g. "-- 1.", "-- 2.")
    query_blocks = re.split(r'-- (\d+)\.', sql_content)
    
    # The first element is before any query
    queries = []
    i = 1
    while i < len(query_blocks):
        num = query_blocks[i]
        content = query_blocks[i+1]
        
        # Extract title and SQL
        lines = content.strip().split("\n")
        title = lines[0].replace("-- Description:", "").replace("--", "").strip()
        
        # Combine rest of lines as SQL
        sql = "\n".join([line for line in lines[1:] if not line.strip().startswith("--")])
        sql = sql.strip()
        
        if sql:
            queries.append((num, title, sql))
        i += 2
        
    print("=" * 60)
    print("RUNNING ANALYTICAL QUERIES ON BLUESTOCK_MF.DB")
    print("=" * 60)
    
    for num, title, sql in queries:
        print(f"\nQuery {num}: {title}")
        print("-" * 50)
        try:
            df = pd.read_sql_query(sql, conn)
            print(df.to_string(index=False))
            print(f"(Rows returned: {len(df)})\n")
        except Exception as e:
            print(f"Error running query {num}: {e}")
            
    conn.close()

if __name__ == "__main__":
    run_queries()
