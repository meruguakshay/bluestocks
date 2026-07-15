import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect("db/nifty100.db")

comp_df = pd.read_sql_query("SELECT c.*, s.broad_sector FROM companies c JOIN sectors s ON c.sector_id = s.sector_id", conn)
pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)

merged_all = pd.merge(pnl_df, bs_df, on=["company_id", "year"])
latest_matching = merged_all.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
merged = pd.merge(comp_df, latest_matching, on="company_id", suffixes=('', '_financials'))

errors_roe = []
errors_roce_1 = []
errors_roce_2 = []
errors_roce_3 = []
errors_roce_4 = []

results = []

for i, row in merged.iterrows():
    c_id = row['company_id']
    broad_sector = row['broad_sector']
    comp_roce = row['roce_percentage']
    comp_roe = row['roe_percentage']
    
    # Handle TCS anomaly where roe_percentage = 0.52 (52%)
    if c_id == 'TCS' and comp_roe == 0.52:
        comp_roe = 52.0 # convert fraction to percentage for comparison
        
    op_profit = row['operating_profit']
    depr = row['depreciation']
    pbt = row['profit_before_tax']
    interest = row['interest']
    other_inc = row['other_income']
    net_profit = row['net_profit']
    
    equity = row['equity_capital'] + row['reserves']
    borrowings = row['borrowings']
    cap_employed = equity + borrowings
    
    # Calculate
    roe = (net_profit / equity * 100) if (pd.notna(equity) and equity > 0) else None
    
    roce_1 = (op_profit / cap_employed * 100) if (pd.notna(cap_employed) and cap_employed > 0) else None
    roce_2 = ((op_profit - depr) / cap_employed * 100) if (pd.notna(cap_employed) and cap_employed > 0) else None
    roce_3 = ((pbt + interest) / cap_employed * 100) if (pd.notna(cap_employed) and cap_employed > 0) else None
    roce_4 = ((op_profit + other_inc - depr) / cap_employed * 100) if (pd.notna(cap_employed) and cap_employed > 0) else None
    
    def get_err(val, target):
        if val is None or pd.isna(val) or target is None or pd.isna(target):
            return None
        return abs(val - target)

    e_roe = get_err(roe, comp_roe)
    e_roce_1 = get_err(roce_1, comp_roce)
    e_roce_2 = get_err(roce_2, comp_roce)
    e_roce_3 = get_err(roce_3, comp_roce)
    e_roce_4 = get_err(roce_4, comp_roce)
    
    if e_roe is not None: errors_roe.append(e_roe)
    if e_roce_1 is not None: errors_roce_1.append(e_roce_1)
    if e_roce_2 is not None: errors_roce_2.append(e_roce_2)
    if e_roce_3 is not None: errors_roce_3.append(e_roce_3)
    if e_roce_4 is not None: errors_roce_4.append(e_roce_4)

print("\nMean Absolute Errors vs Excel:")
print(f"ROE: {np.mean(errors_roe):.2f}% (n={len(errors_roe)})")
print(f"ROCE 1 (EBIT=OP): {np.mean(errors_roce_1):.2f}% (n={len(errors_roce_1)})")
print(f"ROCE 2 (EBIT=OP-Depr): {np.mean(errors_roce_2):.2f}% (n={len(errors_roce_2)})")
print(f"ROCE 3 (EBIT=PBT+Int): {np.mean(errors_roce_3):.2f}% (n={len(errors_roce_3)})")
print(f"ROCE 4 (EBIT=OP+OI-Depr): {np.mean(errors_roce_4):.2f}% (n={len(errors_roce_4)})")

# Let's count how many companies are within 5% for ROCE 3 and ROCE 4
print("\nNumber of companies with difference <= 5%:")
print(f"ROCE 1: {sum(1 for e in errors_roce_1 if e <= 5)} / {len(errors_roce_1)}")
print(f"ROCE 2: {sum(1 for e in errors_roce_2 if e <= 5)} / {len(errors_roce_2)}")
print(f"ROCE 3: {sum(1 for e in errors_roce_3 if e <= 5)} / {len(errors_roce_3)}")
print(f"ROCE 4: {sum(1 for e in errors_roce_4 if e <= 5)} / {len(errors_roce_4)}")

conn.close()
