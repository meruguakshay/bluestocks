import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

print("ADANIGREEN Financials:")
pnl_df = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id='ADANIGREEN' AND year='2024-03'", conn)
print("PnL:")
print(pnl_df.to_string(index=False))

bs_df = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id='ADANIGREEN' AND year='2024-03'", conn)
print("BS:")
print(bs_df.to_string(index=False))

# Excel ref
cursor = conn.cursor()
cursor.execute("SELECT roce_percentage, roe_percentage FROM companies WHERE company_id='ADANIGREEN'")
print("Ref values:", cursor.fetchone())

conn.close()
