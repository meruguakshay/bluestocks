import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()

cursor.execute("SELECT year FROM profitandloss WHERE company_id='RELIANCE' ORDER BY year DESC")
pnl_years = [r[0] for r in cursor.fetchall()]
print("PnL Years for RELIANCE:", pnl_years)

cursor.execute("SELECT year FROM balancesheet WHERE company_id='RELIANCE' ORDER BY year DESC")
bs_years = [r[0] for r in cursor.fetchall()]
print("BS Years for RELIANCE:", bs_years)

conn.close()
