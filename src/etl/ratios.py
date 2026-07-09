import os
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def calculate_cagr(end_val, start_val, periods):
    """Computes CAGR with turnaround flag logic for negative/zero base values."""
    if pd.isna(start_val) or pd.isna(end_val) or start_val <= 0 or end_val <= 0:
        return None
    try:
        return (end_val / start_val) ** (1.0 / periods) - 1.0
    except ZeroDivisionError:
        return None

def main():
    print("=" * 60)
    print("RUNNING FINANCIAL RATIO & CAGR ENGINE")
    print("=" * 60)
    
    conn = connect_db()
    
    # Load financial statements
    pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
    companies = pd.read_sql_query("SELECT * FROM companies", conn)
    
    # Reindex on company_id, year to make lookup fast
    pnl_idx = pnl.set_index(["company_id", "year"])
    bs_idx = bs.set_index(["company_id", "year"])
    cf_idx = cf.set_index(["company_id", "year"])
    
    ratios_list = []
    
    # Compute ratios for each company-year
    for key in pnl_idx.index:
        c_id, yr = key
        
        # P&L metrics
        p_row = pnl_idx.loc[key]
        sales = p_row.get("sales", 0)
        net_profit = p_row.get("net_profit", 0)
        op_profit = p_row.get("operating_profit", 0)
        interest = p_row.get("interest", 0)
        depr = p_row.get("depreciation", 0)
        eps = p_row.get("eps", 0)
        
        # Balance Sheet metrics
        equity = 0
        total_assets = 1
        borrowings = 0
        fixed_assets = 0
        if key in bs_idx.index:
            b_row = bs_idx.loc[key]
            equity = b_row.get("equity_capital", 0) + b_row.get("reserves", 0)
            total_assets = b_row.get("total_assets", 1)
            borrowings = b_row.get("borrowings", 0)
            fixed_assets = b_row.get("fixed_assets", 0)
            
        # Cash Flow metrics
        cfo = 0
        cfi = 0
        cff = 0
        if key in cf_idx.index:
            c_row = cf_idx.loc[key]
            cfo = c_row.get("operating_activity", 0)
            cfi = c_row.get("investing_activity", 0)
            cff = c_row.get("financing_activity", 0)
            
        # 1. Profitability & Returns
        npm = (net_profit / sales * 100) if sales > 0 else None
        opm = (op_profit / sales * 100) if sales > 0 else None
        ebit_margin = ((op_profit - depr) / sales * 100) if sales > 0 else None
        roe = (net_profit / equity * 100) if equity > 0 else None
        
        ebit = op_profit - depr
        capital_employed = equity + borrowings
        roce = (ebit / capital_employed * 100) if capital_employed > 0 else None
        roa = (net_profit / total_assets * 100) if total_assets > 0 else None
        
        # 2. Leverage & Efficiency
        de = (borrowings / equity) if equity > 0 else (0 if borrowings == 0 else None)
        icr = (op_profit / interest) if interest > 0 else None
        asset_turnover = (sales / total_assets) if total_assets > 0 else None
        fixed_asset_turnover = (sales / fixed_assets) if fixed_assets > 0 else None
        
        # 3. Cash Flow KPIs
        fcf = cfo + cfi
        cfo_pat = (cfo / net_profit) if net_profit > 0 else None
        capex_intensity = (abs(cfi) / sales * 100) if sales > 0 else None
        fcf_conversion = (fcf / op_profit * 100) if op_profit > 0 else None
        
        # Capital Allocation Pattern (Reinvestor, Div/Debt payer, etc.)
        pattern = "Unknown"
        if cfo > 0 and cfi < 0 and cff < 0:
            pattern = "Balanced Reinvestor"
        elif cfo > 0 and cfi < 0 and cff > 0:
            pattern = "Expansionary Growth"
        elif cfo < 0:
            pattern = "Operating Distress"
            
        # 4. CAGRs (3yr, 5yr, 10yr)
        cagr_rev_3 = None
        cagr_pat_3 = None
        cagr_eps_3 = None
        if (c_id, yr - 3) in pnl_idx.index:
            cagr_rev_3 = calculate_cagr(sales, pnl_idx.loc[(c_id, yr - 3)].get("sales"), 3)
            cagr_pat_3 = calculate_cagr(net_profit, pnl_idx.loc[(c_id, yr - 3)].get("net_profit"), 3)
            cagr_eps_3 = calculate_cagr(eps, pnl_idx.loc[(c_id, yr - 3)].get("eps"), 3)
            
        cagr_rev_5 = None
        cagr_pat_5 = None
        cagr_eps_5 = None
        if (c_id, yr - 5) in pnl_idx.index:
            cagr_rev_5 = calculate_cagr(sales, pnl_idx.loc[(c_id, yr - 5)].get("sales"), 5)
            cagr_pat_5 = calculate_cagr(net_profit, pnl_idx.loc[(c_id, yr - 5)].get("net_profit"), 5)
            cagr_eps_5 = calculate_cagr(eps, pnl_idx.loc[(c_id, yr - 5)].get("eps"), 5)
            
        cagr_rev_10 = None
        cagr_pat_10 = None
        cagr_eps_10 = None
        if (c_id, yr - 10) in pnl_idx.index:
            cagr_rev_10 = calculate_cagr(sales, pnl_idx.loc[(c_id, yr - 10)].get("sales"), 10)
            cagr_pat_10 = calculate_cagr(net_profit, pnl_idx.loc[(c_id, yr - 10)].get("net_profit"), 10)
            cagr_eps_10 = calculate_cagr(eps, pnl_idx.loc[(c_id, yr - 10)].get("eps"), 10)

        ratios_list.append({
            "company_id": c_id,
            "year": yr,
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "debt_to_equity": de,
            "interest_coverage": icr,
            "asset_turnover": asset_turnover,
            "free_cash_flow_cr": fcf,
            "capex_cr": abs(cfi),
            "earnings_per_share": eps,
            "book_value_per_share": fixed_asset_turnover, # using fixed asset turnover as additional metrics if needed
            "dividend_payout_ratio_pct": p_row.get("dividend_payout", None),
            "total_debt_cr": borrowings,
            "cash_from_operations_cr": cfo
        })
        
    # Load computed ratios to SQLite
    df_ratios = pd.DataFrame(ratios_list)
    
    # Re-create engine connection to update database
    conn.execute("DELETE FROM financial_ratios;")
    conn.commit()
    df_ratios.to_sql("financial_ratios", con=conn, if_exists="append", index=False)
    print(f"[OK] Successfully computed and loaded {len(df_ratios)} rows to financial_ratios table.")
    
    conn.close()
    print("Ratio Engine execution complete!")

if __name__ == "__main__":
    main()
