import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect("db/nifty100.db")

# Load companies
comp_df = pd.read_sql_query("SELECT c.*, s.broad_sector FROM companies c JOIN sectors s ON c.sector_id = s.sector_id", conn)
pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)

# Group PNL and BS by company and get the latest year row
# To do this safely, sort by year descending and take first
pnl_latest = pnl_df.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
bs_latest = bs_df.sort_values("year", ascending=False).groupby("company_id").first().reset_index()

merged = pd.merge(comp_df, pnl_latest, on="company_id", suffixes=('', '_pnl'))
merged = pd.merge(merged, bs_latest, on="company_id", suffixes=('', '_bs'))

print(f"Merged latest data for {len(merged)} companies.")

# Let's test different EBIT formulations
# 1. EBIT = operating_profit
# 2. EBIT = operating_profit - depreciation
# 3. EBIT = profit_before_tax + interest
# 4. EBIT = operating_profit + other_income - depreciation

for i, row in merged.head(10).iterrows():
    c_id = row['company_id']
    broad_sector = row['broad_sector']
    comp_roce = row['roce_percentage']
    comp_roe = row['roe_percentage']
    
    op_profit = row['operating_profit']
    depr = row['depreciation']
    pbt = row['profit_before_tax']
    interest = row['interest']
    other_inc = row['other_income']
    net_profit = row['net_profit']
    sales = row['sales']
    
    equity = row['equity_capital'] + row['reserves']
    borrowings = row['borrowings']
    cap_employed = equity + borrowings
    
    # Ratios
    roe = (net_profit / equity * 100) if equity > 0 else None
    
    # ROCE options
    roce_1 = (op_profit / cap_employed * 100) if cap_employed > 0 else None
    roce_2 = ((op_profit - depr) / cap_employed * 100) if cap_employed > 0 else None
    roce_3 = ((pbt + interest) / cap_employed * 100) if cap_employed > 0 else None
    roce_4 = ((op_profit + other_inc - depr) / cap_employed * 100) if cap_employed > 0 else None
    
    print(f"Company: {c_id} ({broad_sector}) | Excel ROCE: {comp_roce} | Excel ROE: {comp_roe}")
    print(f"  ROE: {roe:.2f}%" if roe is not None else "  ROE: None")
    print(f"  ROCE 1 (EBIT=OP): {roce_1:.2f}%" if roce_1 is not None else "  ROCE 1: None")
    print(f"  ROCE 2 (EBIT=OP-Depr): {roce_2:.2f}%" if roce_2 is not None else "  ROCE 2: None")
    print(f"  ROCE 3 (EBIT=PBT+Int): {roce_3:.2f}%" if roce_3 is not None else "  ROCE 3: None")
    print(f"  ROCE 4 (EBIT=OP+OI-Depr): {roce_4:.2f}%" if roce_4 is not None else "  ROCE 4: None")

# Let's count average absolute errors across all 92 companies for each formulation
errors_roe = []
errors_roce_1 = []
errors_roce_2 = []
errors_roce_3 = []
errors_roce_4 = []

for i, row in merged.iterrows():
    comp_roce = row['roce_percentage']
    comp_roe = row['roe_percentage']
    
    op_profit = row['operating_profit']
    depr = row['depreciation']
    pbt = row['profit_before_tax']
    interest = row['interest']
    other_inc = row['other_income']
    net_profit = row['net_profit']
    
    equity = row['equity_capital'] + row['reserves']
    borrowings = row['borrowings']
    cap_employed = equity + borrowings
    
    roe = (net_profit / equity * 100) if equity > 0 else None
    roce_1 = (op_profit / cap_employed * 100) if cap_employed > 0 else None
    roce_2 = ((op_profit - depr) / cap_employed * 100) if cap_employed > 0 else None
    roce_3 = ((pbt + interest) / cap_employed * 100) if cap_employed > 0 else None
    roce_4 = ((op_profit + other_inc - depr) / cap_employed * 100) if cap_employed > 0 else None
    
    if comp_roe is not None and roe is not None:
        errors_roe.append(abs(roe - comp_roe))
    if comp_roce is not None:
        if roce_1 is not None: errors_roce_1.append(abs(roce_1 - comp_roce))
        if roce_2 is not None: errors_roce_2.append(abs(roce_2 - comp_roce))
        if roce_3 is not None: errors_roce_3.append(abs(roce_3 - comp_roce))
        if roce_4 is not None: errors_roce_4.append(abs(roce_4 - comp_roce))

print("\nMean Absolute Errors vs Excel:")
print(f"ROE: {np.mean(errors_roe):.2f}%")
print(f"ROCE 1 (EBIT=OP): {np.mean(errors_roce_1):.2f}%")
print(f"ROCE 2 (EBIT=OP-Depr): {np.mean(errors_roce_2):.2f}%")
print(f"ROCE 3 (EBIT=PBT+Int): {np.mean(errors_roce_3):.2f}%")
print(f"ROCE 4 (EBIT=OP+OI-Depr): {np.mean(errors_roce_4):.2f}%")

conn.close()
