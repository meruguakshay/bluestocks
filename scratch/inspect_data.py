import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()

print("--- SECTORS ---")
cur.execute("SELECT * FROM sectors")
for r in cur.fetchall():
    print(r)

print("\n--- SAMPLE COMPANIES ---")
cur.execute("SELECT company_id, company_name, roce_percentage, roe_percentage, sector_id FROM companies LIMIT 5")
for r in cur.fetchall():
    print(r)

print("\n--- UNIQUE YEARS IN P&L ---")
cur.execute("SELECT DISTINCT year FROM profitandloss ORDER BY year")
print([r[0] for r in cur.fetchall()])

print("\n--- SAMPLE P&L ROWS ---")
cur.execute("SELECT * FROM profitandloss LIMIT 3")
for r in cur.fetchall():
    print(r)

conn.close()
