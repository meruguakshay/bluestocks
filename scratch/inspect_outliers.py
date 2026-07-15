import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

for c_id in ["BEL", "HAL", "LT"]:
    print("="*40)
    print("Company:", c_id)
    # PnL
    pnl_df = pd.read_sql_query(f"SELECT * FROM profitandloss WHERE company_id='{c_id}' AND year='2024-03'", conn)
    print("PnL 2024-03:")
    print(pnl_df.to_string(index=False))
    
    # BS
    bs_df = pd.read_sql_query(f"SELECT * FROM balancesheet WHERE company_id='{c_id}' AND year='2024-03'", conn)
    print("BS 2024-03:")
    print(bs_df.to_string(index=False))

conn.close()
