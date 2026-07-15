import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

# Find the latest year for each company in financial_ratios
query_latest = """
SELECT r.*, c.company_name, s.broad_sector 
FROM financial_ratios r
JOIN companies c ON r.company_id = c.company_id
JOIN sectors s ON c.sector_id = s.sector_id
JOIN (
    SELECT company_id, MAX(year) as max_year 
    FROM financial_ratios 
    WHERE return_on_equity_pct IS NOT NULL
    GROUP BY company_id
) m ON r.company_id = m.company_id AND r.year = m.max_year
"""
df_latest = pd.read_sql_query(query_latest, conn)

print("Total conformed companies in latest year:", len(df_latest))

# Apply filter ROE > 15% and D/E < 1
filtered = df_latest[(df_latest['return_on_equity_pct'] > 15.0) & (df_latest['debt_to_equity'] < 1.0)]

print(f"\nFiltered companies (count = {len(filtered)}):")
print(filtered[['company_id', 'company_name', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity']].to_string(index=False))

# Check if count is between 15 and 50
count = len(filtered)
if 15 <= count <= 50:
    print(f"\n[OK] Screener preview count ({count}) is between 15 and 50.")
else:
    print(f"\n[FAIL] Screener preview count ({count}) is NOT between 15 and 50.")

conn.close()
