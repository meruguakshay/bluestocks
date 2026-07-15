import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()

cursor.execute("SELECT company_id FROM profitandloss WHERE year='2024-09'")
pnl_cos = set(r[0] for r in cursor.fetchall())

cursor.execute("SELECT company_id FROM balancesheet WHERE year='2024-09'")
bs_cos = set(r[0] for r in cursor.fetchall())

print("Number of companies with PnL for 2024-09:", len(pnl_cos))
print("Number of companies with BS for 2024-09:", len(bs_cos))
print("Overlap (both PnL and BS):", len(pnl_cos.intersection(bs_cos)))
print("PnL but no BS:", pnl_cos - bs_cos)
print("BS but no PnL:", bs_cos - pnl_cos)

conn.close()
