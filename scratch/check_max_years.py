import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

df_all = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

print("Distribution of max years in financial_ratios:")
max_years = df_all.groupby("company_id")["year"].max()
print(max_years.value_counts())

print("\nHow many records have non-Null return_on_equity_pct in 2024-03?")
df_2024_03 = df_all[df_all['year'] == '2024-03']
print(f"Total rows in 2024-03: {len(df_2024_03)}")
print(f"Non-Null ROE in 2024-03: {df_2024_03['return_on_equity_pct'].notna().sum()}")

# Apply filter on 2024-03
filtered_2024_03 = df_2024_03[(df_2024_03['return_on_equity_pct'] > 15.0) & (df_2024_03['debt_to_equity'] < 1.0)]
print(f"\nFiltered count in 2024-03 (count = {len(filtered_2024_03)}):")
print(filtered_2024_03[['company_id', 'return_on_equity_pct', 'debt_to_equity']].head(30).to_string(index=False))

# Let's also check for each company the latest year that has a non-Null return_on_equity_pct
print("\nIf we find the latest year with non-Null ROE for each company:")
df_non_null = df_all.dropna(subset=['return_on_equity_pct', 'debt_to_equity'])
idx_latest = df_non_null.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
print(f"Total companies with some valid ROE: {len(idx_latest)}")
filtered_latest = idx_latest[(idx_latest['return_on_equity_pct'] > 15.0) & (idx_latest['debt_to_equity'] < 1.0)]
print(f"Filtered count using latest valid year (count = {len(filtered_latest)}):")
print(filtered_latest[['company_id', 'year', 'return_on_equity_pct', 'debt_to_equity']].head(30).to_string(index=False))

conn.close()
