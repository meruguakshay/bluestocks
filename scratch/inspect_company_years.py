import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

pl_years = pd.read_sql("SELECT company_id, year FROM profitandloss", conn)
bs_years = pd.read_sql("SELECT company_id, year FROM balancesheet", conn)
cf_years = pd.read_sql("SELECT company_id, year FROM cashflow", conn)
ratio_years = pd.read_sql("SELECT company_id, year FROM financial_ratios", conn)

pl_set = set(zip(pl_years['company_id'], pl_years['year']))
bs_set = set(zip(bs_years['company_id'], bs_years['year']))
cf_set = set(zip(cf_years['company_id'], cf_years['year']))
ratio_set = set(zip(ratio_years['company_id'], ratio_years['year']))

union_all = pl_set.union(bs_set).union(cf_set)
intersection_all = pl_set.intersection(bs_set).intersection(cf_set)

print(f"Profit & Loss pairs: {len(pl_set)}")
print(f"Balance Sheet pairs: {len(bs_set)}")
print(f"Cash Flow pairs: {len(cf_set)}")
print(f"Financial Ratios in DB: {len(ratio_set)}")
print(f"Union of PL, BS, CF: {len(union_all)}")
print(f"Intersection of PL, BS, CF: {len(intersection_all)}")

# Let's see if companies are in broad_sector
comp_df = pd.read_sql("SELECT company_id, sector_id FROM companies", conn)
sect_df = pd.read_sql("SELECT sector_id, broad_sector FROM sectors", conn)
comp_sect = pd.merge(comp_df, sect_df, on='sector_id')
print("\nNumber of companies per sector:")
print(comp_sect['broad_sector'].value_counts())

conn.close()
