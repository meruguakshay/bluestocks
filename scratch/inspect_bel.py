import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
pnl_bel = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = 'BEL' ORDER BY year DESC", conn)
bs_bel = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id = 'BEL' ORDER BY year DESC", conn)
print("=== PNL for BEL ===")
print(pnl_bel.to_string())
print("\n=== BS for BEL ===")
print(bs_bel.to_string())
conn.close()
