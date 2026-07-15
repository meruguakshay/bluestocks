import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql_query("SELECT company_id, company_name, roce_percentage, roe_percentage FROM companies", conn)

print("Columns types:")
print(df.dtypes)

print("\nCompanies with roe_percentage < 1.0 (sample of fractions?):")
print(df[df['roe_percentage'] < 1.0].head(15))

print("\nNull or weird values in roe_percentage:")
print(df[df['roe_percentage'].isna()])

print("\nNull or weird values in roce_percentage:")
print(df[df['roce_percentage'].isna()])

conn.close()
