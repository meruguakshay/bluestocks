import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()
cur.execute("PRAGMA table_info(financial_ratios)")
cols = cur.fetchall()
print("financial_ratios columns:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")

cur.execute("SELECT * FROM financial_ratios LIMIT 1")
row = cur.fetchone()
print("\nSample row in financial_ratios:")
print(row)

cur.execute("SELECT COUNT(*) FROM financial_ratios")
print(f"\nTotal rows in financial_ratios: {cur.fetchone()[0]}")

conn.close()
