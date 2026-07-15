import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

# Companies to spot-check
companies = ["ABB", "INFY", "RELIANCE"]

print("=== SPRINT 2 MANUAL SPOT-CHECK ===")

for ticker in companies:
    print(f"\n--- Spot Check for: {ticker} ---")
    
    # 1. Spot-check ROE for the latest matching year
    # Find latest year that has both P&L and BS conformed records
    query_years = f"""
    SELECT p.year FROM profitandloss p 
    JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year 
    WHERE p.company_id = '{ticker}'
    ORDER BY p.year DESC LIMIT 1
    """
    latest_year = pd.read_sql_query(query_years, conn).iloc[0]["year"]
    
    # Retrieve conformed values
    query_vals = f"""
    SELECT p.net_profit, b.equity_capital, b.reserves 
    FROM profitandloss p
    JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
    WHERE p.company_id = '{ticker}' AND p.year = '{latest_year}'
    """
    vals = pd.read_sql_query(query_vals, conn).iloc[0]
    net_profit = vals["net_profit"]
    equity_capital = vals["equity_capital"]
    reserves = vals["reserves"]
    
    # Manual ROE
    manual_roe = (net_profit / (equity_capital + reserves)) * 100.0
    
    # Database ratio ROE
    query_db_roe = f"""
    SELECT return_on_equity_pct FROM financial_ratios 
    WHERE company_id = '{ticker}' AND year = '{latest_year}'
    """
    db_roe = pd.read_sql_query(query_db_roe, conn).iloc[0]["return_on_equity_pct"]
    
    diff_roe = abs(manual_roe - db_roe)
    
    print(f"ROE Year: {latest_year}")
    print(f"  Inputs: Net Profit={net_profit}, Equity Capital={equity_capital}, Reserves={reserves}")
    print(f"  Manual ROE calculation = {manual_roe:.6f}%")
    print(f"  Database ROE loaded    = {db_roe:.6f}%")
    print(f"  Difference             = {diff_roe:.6f}%")
    
    # 2. Spot-check 5-year Revenue CAGR
    # Get latest sales and sales from 5 years ago
    year_num = int(latest_year.split("-")[0])
    month_str = latest_year.split("-")[1]
    prev_5yr_str = f"{year_num - 5}-{month_str}"
    
    query_sales = f"""
    SELECT 
        (SELECT sales FROM profitandloss WHERE company_id = '{ticker}' AND year = '{latest_year}') AS sales_latest,
        (SELECT sales FROM profitandloss WHERE company_id = '{ticker}' AND year = '{prev_5yr_str}') AS sales_prev
    """
    sales_data = pd.read_sql_query(query_sales, conn).iloc[0]
    sales_latest = sales_data["sales_latest"]
    sales_prev = sales_data["sales_prev"]
    
    # Manual Revenue CAGR
    manual_cagr = ((sales_latest / sales_prev) ** (1.0 / 5.0) - 1.0) * 100.0
    
    # Database Revenue CAGR loaded
    query_db_cagr = f"""
    SELECT revenue_cagr_5yr FROM financial_ratios 
    WHERE company_id = '{ticker}' AND year = '{latest_year}'
    """
    db_cagr = pd.read_sql_query(query_db_cagr, conn).iloc[0]["revenue_cagr_5yr"]
    
    diff_cagr = abs(manual_cagr - db_cagr)
    
    print(f"Revenue CAGR Window: {prev_5yr_str} to {latest_year}")
    print(f"  Inputs: Sales Latest={sales_latest}, Sales 5Yr Ago={sales_prev}")
    print(f"  Manual CAGR calculation = {manual_cagr:.6f}%")
    print(f"  Database CAGR loaded    = {db_cagr:.6f}%")
    print(f"  Difference              = {diff_cagr:.6f}%")
    
    assert diff_roe < 0.1, "ROE mismatch is greater than 0.1%"
    assert diff_cagr < 0.1, "Revenue CAGR mismatch is greater than 0.1%"

conn.close()
print("\nSpot check complete. All manual calculations match database ratios within 0.1%.")
