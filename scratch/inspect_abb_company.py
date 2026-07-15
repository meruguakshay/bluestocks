import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
res = pd.read_sql_query("SELECT * FROM companies WHERE company_id = 'ABB'", conn)
print(res.to_string())
conn.close()
