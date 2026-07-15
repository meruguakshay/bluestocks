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

outliers = []
for i, row in merged.iterrows():
    c_id = row['company_id']
    broad_sector = row['broad_sector']
    comp_roce = row['roce_percentage']
    comp_roe = row['roe_percentage']
    
    # Handle TCS anomaly for printing
    tcs_adjusted_roe = comp_roe
    if c_id == 'TCS' and comp_roe == 0.52:
        tcs_adjusted_roe = 52.0
        
    op_profit = row['operating_profit']
    depr = row['depreciation']
    pbt = row['profit_before_tax']
    interest = row['interest']
    other_inc = row['other_income']
    net_profit = row['net_profit']
    
    equity = row['equity_capital'] + row['reserves']
    borrowings = row['borrowings']
    cap_employed = equity + borrowings
    
    roe = (net_profit / equity * 100) if (pd.notna(equity) and equity > 0) else None
    
    # Let's check ROCE 2 (EBIT = OP - Depr) and ROCE 3 (EBIT = PBT + Interest)
    roce_2 = ((op_profit - depr) / cap_employed * 100) if (pd.notna(cap_employed) and cap_employed > 0) else None
    roce_3 = ((pbt + interest) / cap_employed * 100) if (pd.notna(cap_employed) and cap_employed > 0) else None
    
    diff_roe = abs(roe - tcs_adjusted_roe) if (roe is not None and pd.notna(tcs_adjusted_roe)) else 0
    diff_roce_3 = abs(roce_3 - comp_roce) if (roce_3 is not None and pd.notna(comp_roce)) else 0
    diff_roce_2 = abs(roce_2 - comp_roce) if (roce_2 is not None and pd.notna(comp_roce)) else 0
    
    if diff_roe > 5 or diff_roce_3 > 5 or diff_roce_2 > 5:
        outliers.append({
            "company_id": c_id,
            "sector": broad_sector,
            "excel_roe": comp_roe,
            "computed_roe": roe,
            "excel_roce": comp_roce,
            "roce_2": roce_2,
            "roce_3": roce_3,
            "diff_roe": diff_roe,
            "diff_roce_3": diff_roce_3,
            "diff_roce_2": diff_roce_2,
            "equity": equity,
            "borrowings": borrowings,
            "net_profit": net_profit,
            "op_profit": op_profit,
            "pbt": pbt,
            "interest": interest,
            "depr": depr
        })

print(f"Found {len(outliers)} companies with difference > 5% in ROCE or ROE:")
out_df = pd.DataFrame(outliers)
print(out_df[['company_id', 'sector', 'excel_roe', 'computed_roe', 'excel_roce', 'roce_2', 'roce_3', 'diff_roe', 'diff_roce_3', 'diff_roce_2']].head(30).to_string())

conn.close()
