import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

query = """
SELECT c.company_id, c.company_name, c.sub_sector, c.roce_percentage, c.roe_percentage, s.broad_sector
FROM companies c
JOIN sectors s ON c.sector_id = s.sector_id
WHERE s.broad_sector = 'Financials'
"""
df = pd.read_sql(query, conn)
print("Financial companies (count = {}):".format(len(df)))
print(df.to_string())

conn.close()
