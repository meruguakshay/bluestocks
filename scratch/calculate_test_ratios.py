import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

# Let's query profit and loss for ABB
pnl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = 'ABB' ORDER BY year DESC", conn)
bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id = 'ABB' ORDER BY year DESC", conn)

print("=== PNL for ABB ===")
print(pnl.to_string())

print("\n=== BS for ABB ===")
print(bs.to_string())

# Let's try to compute ROCE and ROE for ABB across years
print("\n=== Computations for ABB ===")
for year in pnl['year'].unique():
    p_row = pnl[pnl['year'] == year].iloc[0]
    b_rows = bs[bs['year'] == year]
    if len(b_rows) == 0:
        continue
    b_row = b_rows.iloc[0]
    
    sales = p_row['sales']
    net_profit = p_row['net_profit']
    op_profit = p_row['operating_profit']
    interest = p_row['interest']
    depr = p_row['depreciation']
    pbt = p_row['profit_before_tax']
    
    equity = b_row['equity_capital'] + b_row['reserves']
    borrowings = b_row['borrowings']
    total_assets = b_row['total_assets']
    
    # Candidates for EBIT:
    # 1. op_profit
    # 2. op_profit - depr
    # 3. pbt + interest
    # 4. op_profit + other_income - depr
    ebit_1 = op_profit
    ebit_2 = op_profit - depr
    ebit_3 = pbt + interest
    ebit_4 = op_profit + p_row['other_income'] - depr
    
    capital_employed = equity + borrowings
    
    roe = (net_profit / equity * 100) if equity != 0 else None
    roce_1 = (ebit_1 / capital_employed * 100) if capital_employed != 0 else None
    roce_2 = (ebit_2 / capital_employed * 100) if capital_employed != 0 else None
    roce_3 = (ebit_3 / capital_employed * 100) if capital_employed != 0 else None
    roce_4 = (ebit_4 / capital_employed * 100) if capital_employed != 0 else None
    
    print(f"Year {year}:")
    print(f"  Equity: {equity}, Borrowings: {borrowings}, CapEmployed: {capital_employed}")
    print(f"  Sales: {sales}, NetProfit: {net_profit}, OPProfit: {op_profit}, Interest: {interest}, Depr: {depr}, PBT: {pbt}")
    print(f"  ROE: {roe:.2f}% if equity else None")
    print(f"  ROCE (EBIT=op_profit): {roce_1:.2f}%")
    print(f"  ROCE (EBIT=op_profit-depr): {roce_2:.2f}%")
    print(f"  ROCE (EBIT=pbt+interest): {roce_3:.2f}%")
    print(f"  ROCE (EBIT=op_profit+other_income-depr): {roce_4:.2f}%")

conn.close()
