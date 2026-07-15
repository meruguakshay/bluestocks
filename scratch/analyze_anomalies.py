import sqlite3
import pandas as pd
import numpy as np

# Load ratios calculations
from src.analytics.ratios import calculate_roce, calculate_roe

conn = sqlite3.connect("db/nifty100.db")

companies = pd.read_sql_query("SELECT c.*, s.broad_sector FROM companies c JOIN sectors s ON c.sector_id = s.sector_id", conn)
pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)

pnl_idx = pnl.set_index(["company_id", "year"])
bs_idx = bs.set_index(["company_id", "year"])

pnl_keys = set(zip(pnl['company_id'], pnl['year']))
bs_keys = set(zip(bs['company_id'], bs['year']))
union_keys = pnl_keys.union(bs_keys)
valid_companies = set(companies['company_id'])
conformed_keys = sorted([k for k in union_keys if k[0] in valid_companies], key=lambda x: (x[0], x[1]))

latest_year_b = {}
for c_id, yr in conformed_keys:
    key = (c_id, yr)
    if key in pnl_idx.index and key in bs_idx.index:
        latest_year_b[c_id] = yr

anomalies = []
for c_id in sorted(valid_companies):
    ref_data = companies[companies["company_id"] == c_id].iloc[0]
    ref_roce = ref_data["roce_percentage"]
    ref_roe = ref_data["roe_percentage"]
    broad_sector = ref_data["broad_sector"]
    
    tcs_adjusted_roe = ref_roe
    if c_id == 'TCS' and ref_roe == 0.52:
        tcs_adjusted_roe = 52.0
        
    yr = latest_year_b.get(c_id)
    if yr is None:
        continue
    
    key = (c_id, yr)
    op = pnl_idx.loc[key]["operating_profit"]
    dep = pnl_idx.loc[key]["depreciation"]
    eq = bs_idx.loc[key]["equity_capital"]
    res = bs_idx.loc[key]["reserves"]
    borrow = bs_idx.loc[key]["borrowings"]
    net_profit = pnl_idx.loc[key]["net_profit"]
    
    comp_roce = calculate_roce(op, dep, eq, res, borrow)
    comp_roe = calculate_roe(net_profit, eq, res)
    
    # Analyze ROCE
    if ref_roce is not None and pd.notna(ref_roce) and comp_roce is not None:
        diff_roce = abs(comp_roce - ref_roce)
        if diff_roce > 5.0:
            category = "formula discrepancy"
            if c_id in ["BEL", "HAL", "LT"]:
                category = "data source issue"
            elif broad_sector == "Financials":
                category = "formula discrepancy" # due to bank capital employed definition
            anomalies.append({
                "company_id": c_id,
                "sector": broad_sector,
                "metric": "ROCE",
                "year": yr,
                "computed": comp_roce,
                "reference": ref_roce,
                "difference": diff_roce,
                "category": category
            })
            
    # Analyze ROE
    if tcs_adjusted_roe is not None and pd.notna(tcs_adjusted_roe) and comp_roe is not None:
        diff_roe = abs(comp_roe - tcs_adjusted_roe)
        if diff_roe > 5.0:
            category = "formula discrepancy"
            if c_id in ["BEL", "HAL", "LT"]:
                category = "data source issue"
            elif c_id == "TCS":
                category = "data source issue" # stored as decimal fraction in source excel (0.52) but computed as percentage
            anomalies.append({
                "company_id": c_id,
                "sector": broad_sector,
                "metric": "ROE",
                "year": yr,
                "computed": comp_roe,
                "reference": ref_roe,
                "difference": diff_roe,
                "category": category
            })

df_anom = pd.DataFrame(anomalies)
print(df_anom.to_string(index=False))

conn.close()
