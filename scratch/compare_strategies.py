import sqlite3
import pandas as pd
import numpy as np

# Load ratios calculations
from src.analytics.ratios import calculate_roce, calculate_roe, calculate_opm

conn = sqlite3.connect("db/nifty100.db")

companies = pd.read_sql_query("SELECT c.*, s.broad_sector FROM companies c JOIN sectors s ON c.sector_id = s.sector_id", conn)
pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)

pnl_idx = pnl.set_index(["company_id", "year"])
bs_idx = bs.set_index(["company_id", "year"])

# Conformed keys
pnl_keys = set(zip(pnl['company_id'], pnl['year']))
bs_keys = set(zip(bs['company_id'], bs['year']))
union_keys = pnl_keys.union(bs_keys)
valid_companies = set(companies['company_id'])
conformed_keys = sorted([k for k in union_keys if k[0] in valid_companies], key=lambda x: (x[0], x[1]))

print(f"Total valid conformed keys: {len(conformed_keys)}")

# Strategy A: Latest conformed year
latest_year_a = {}
for c_id, yr in conformed_keys:
    latest_year_a[c_id] = yr

# Strategy B: Latest conformed year with both PnL and BS data present
latest_year_b = {}
for c_id, yr in conformed_keys:
    key = (c_id, yr)
    if key in pnl_idx.index and key in bs_idx.index:
        latest_year_b[c_id] = yr

# Let's count how many latest conformed years differ between Strategy A and Strategy B
diff_count = 0
for c_id in valid_companies:
    yr_a = latest_year_a.get(c_id)
    yr_b = latest_year_b.get(c_id)
    if yr_a != yr_b:
        diff_count += 1

print(f"Number of companies where latest conformed year differs: {diff_count}")

# Let's compute anomalies for Strategy B and print them
anomalies_b = []
for c_id in sorted(valid_companies):
    ref_data = companies[companies["company_id"] == c_id].iloc[0]
    ref_roce = ref_data["roce_percentage"]
    ref_roe = ref_data["roe_percentage"]
    
    tcs_adjusted_roe = ref_roe
    if c_id == 'TCS' and ref_roe == 0.52:
        tcs_adjusted_roe = 52.0
        
    yr = latest_year_b.get(c_id)
    if yr is None:
        continue
    
    key = (c_id, yr)
    op = pnl_idx.loc[key]["operating_profit"] if key in pnl_idx.index else None
    dep = pnl_idx.loc[key]["depreciation"] if key in pnl_idx.index else None
    eq = bs_idx.loc[key]["equity_capital"] if key in bs_idx.index else None
    res = bs_idx.loc[key]["reserves"] if key in bs_idx.index else None
    borrow = bs_idx.loc[key]["borrowings"] if key in bs_idx.index else None
    net_profit = pnl_idx.loc[key]["net_profit"] if key in pnl_idx.index else None
    
    comp_roce = calculate_roce(op, dep, eq, res, borrow)
    comp_roe = calculate_roe(net_profit, eq, res)
    
    if ref_roce is not None and pd.notna(ref_roce) and comp_roce is not None:
        diff_roce = abs(comp_roce - ref_roce)
        if diff_roce > 5.0:
            anomalies_b.append(f"[{c_id}] ROCE anomaly at {yr}: Computed={comp_roce:.2f}%, Ref={ref_roce:.2f}%, Diff={diff_roce:.2f}%")
            
    if tcs_adjusted_roe is not None and pd.notna(tcs_adjusted_roe) and comp_roe is not None:
        diff_roe = abs(comp_roe - tcs_adjusted_roe)
        if diff_roe > 5.0:
            anomalies_b.append(f"[{c_id}] ROE anomaly at {yr}: Computed={comp_roe:.2f}%, Ref={ref_roe:.2f}%, Diff={diff_roe:.2f}%")

print(f"\nTotal anomalies under Strategy B: {len(anomalies_b)}")
for anom in anomalies_b[:20]:
    print("  ", anom)
if len(anomalies_b) > 20:
    print(f"   ... and {len(anomalies_b) - 20} more.")

conn.close()
