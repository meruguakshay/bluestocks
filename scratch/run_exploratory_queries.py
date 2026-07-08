import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"
SQL_FILE = "notebooks/exploratory_queries.sql"

def run_queries():
    print("=" * 60)
    print("RUNNING EXPLORATORY SQL QUERIES")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    with open(SQL_FILE, "r") as f:
         sql_content = f.read()
         
    # Split queries by double dash comments followed by query description
    queries = sql_content.split("\n\n")
    for q in queries:
         q = q.strip()
         if not q:
              continue
         # Extract comment header
         lines = q.split("\n")
         header = lines[0] if lines[0].startswith("--") else "Query"
         sql_query = "\n".join([line for line in lines if not line.startswith("--")]).strip()
         
         if sql_query:
              print(header)
              try:
                  res = pd.read_sql_query(sql_query, conn)
                  print(res.to_string(index=False))
              except Exception as e:
                  print(f"Error running query: {e}")
              print("-" * 60)
              
    conn.close()

if __name__ == "__main__":
    run_queries()
