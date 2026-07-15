import os
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Import growth (CAGR) and cash flow KPI calculations from siblings
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    calculate_fcf,
    calculate_cfo_quality,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation
)

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")

def to_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

# ────────────────────────────────────────────────────────
# FINANCIAL RATIOS FUNCTIONS
# ────────────────────────────────────────────────────────

def calculate_npm(net_profit, sales):
    """Net Profit Margin: net_profit / sales x 100"""
    s = to_float(sales, None)
    np = to_float(net_profit, None)
    if s is None or np is None or s == 0.0:
        return None
    return (np / s) * 100.0

def calculate_opm(operating_profit, sales):
    """Operating Profit Margin: operating_profit / sales x 100"""
    s = to_float(sales, None)
    op = to_float(operating_profit, None)
    if s is None or op is None or s == 0.0:
        return None
    return (op / s) * 100.0

def calculate_roe(net_profit, equity_capital, reserves):
    """Return on Equity (ROE): net_profit / (equity_capital + reserves) x 100"""
    np = to_float(net_profit, None)
    eq = to_float(equity_capital, 0.0)
    res = to_float(reserves, 0.0)
    total_eq = eq + res
    if np is None or total_eq <= 0.0:
        return None
    return (np / total_eq) * 100.0

def calculate_roce(operating_profit, depreciation, equity_capital, reserves, borrowings):
    """Return on Capital Employed (ROCE): EBIT / (equity + reserves + borrowings) x 100"""
    op = to_float(operating_profit, None)
    if op is None:
        return None
    dep = to_float(depreciation, 0.0)
    ebit = op - dep
    
    eq = to_float(equity_capital, 0.0)
    res = to_float(reserves, 0.0)
    borrow = to_float(borrowings, 0.0)
    capital_employed = eq + res + borrow
    
    if capital_employed <= 0.0:
        return None
    return (ebit / capital_employed) * 100.0


def calculate_roa(net_profit, total_assets):
    """Return on Assets (ROA): net_profit / total_assets x 100"""
    np = to_float(net_profit, None)
    ta = to_float(total_assets, None)
    if np is None or ta is None or ta == 0.0:
        return None
    return (np / ta) * 100.0

def calculate_de(borrowings, equity_capital, reserves):
    """Debt-to-Equity: borrowings / (equity_capital + reserves)"""
    borrow = to_float(borrowings, 0.0)
    eq = to_float(equity_capital, 0.0)
    res = to_float(reserves, 0.0)
    total_eq = eq + res
    
    if borrow == 0.0:
        return 0.0
    if total_eq <= 0.0:
        return None
    return borrow / total_eq

def calculate_icr(operating_profit, other_income, interest):
    """Interest Coverage Ratio: (operating_profit + other_income) / interest"""
    op = to_float(operating_profit, 0.0)
    oi = to_float(other_income, 0.0)
    earnings = op + oi
    intr = to_float(interest, None)
    
    if intr is None or intr == 0.0:
        return None
    return earnings / intr

def calculate_asset_turnover(sales, total_assets):
    """Asset Turnover: sales / total_assets"""
    s = to_float(sales, None)
    ta = to_float(total_assets, None)
    if s is None or ta is None or ta == 0.0:
        return None
    return s / ta

def calculate_book_value_per_share(equity_capital, reserves, face_value):
    """Book Value Per Share: (equity + reserves) / (equity_cap / face_value)"""
    eq = to_float(equity_capital, 0.0)
    res = to_float(reserves, 0.0)
    total_eq = eq + res
    fv = to_float(face_value, None)
    eq_cap = to_float(equity_capital, None)
    
    if fv is None or eq_cap is None or fv <= 0.0 or eq_cap <= 0.0:
        return None
    return (total_eq / eq_cap) * fv

# ────────────────────────────────────────────────────────
# MAIN ENGINE ORCHESTRATION
# ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("STARTING SPRINT 2 FINANCIAL RATIO ENGINE")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load data
    companies = pd.read_sql_query("SELECT * FROM companies", conn)
    pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
    sectors = pd.read_sql_query("SELECT * FROM sectors", conn)
    
    comp_sect = pd.merge(companies, sectors, on="sector_id")
    comp_sect_dict = comp_sect.set_index("company_id")["broad_sector"].to_dict()
    comp_face_value = companies.set_index("company_id")["face_value"].to_dict()
    
    # Fast lookups
    pnl_idx = pnl.set_index(["company_id", "year"])
    bs_idx = bs.set_index(["company_id", "year"])
    cf_idx = cf.set_index(["company_id", "year"])
    
    # Find conformed company-year union
    pnl_keys = set(zip(pnl['company_id'], pnl['year']))
    bs_keys = set(zip(bs['company_id'], bs['year']))
    cf_keys = set(zip(cf['company_id'], cf['year']))
    
    union_keys = pnl_keys.union(bs_keys).union(cf_keys)
    
    # Filter to conformed 92 companies
    valid_companies = set(companies['company_id'])
    conformed_keys = sorted([k for k in union_keys if k[0] in valid_companies], key=lambda x: (x[0], x[1]))
    
    print(f"Loaded {len(valid_companies)} companies.")
    print(f"Total conformed company-year records to process: {len(conformed_keys)}")
    
    ratios_list = []
    capital_alloc_list = []
    
    # Pre-build lookup matrices for historical time series (CAGRs & CFO Quality)
    pnl_series = pnl.sort_values(["company_id", "year"])
    bs_series = bs.sort_values(["company_id", "year"])
    cf_series = cf.sort_values(["company_id", "year"])
    
    # Compute loop
    for c_id, yr_str in conformed_keys:
        key = (c_id, yr_str)
        broad_sector = comp_sect_dict.get(c_id, "Unknown")
        face_val = comp_face_value.get(c_id, 10.0)
        
        # P&L Metrics
        sales = pnl_idx.loc[key]["sales"] if key in pnl_idx.index else None
        expenses = pnl_idx.loc[key]["expenses"] if key in pnl_idx.index else None
        operating_profit = pnl_idx.loc[key]["operating_profit"] if key in pnl_idx.index else None
        opm_percentage = pnl_idx.loc[key]["opm_percentage"] if key in pnl_idx.index else None
        other_income = pnl_idx.loc[key]["other_income"] if key in pnl_idx.index else None
        interest = pnl_idx.loc[key]["interest"] if key in pnl_idx.index else None
        depreciation = pnl_idx.loc[key]["depreciation"] if key in pnl_idx.index else None
        pbt = pnl_idx.loc[key]["profit_before_tax"] if key in pnl_idx.index else None
        net_profit = pnl_idx.loc[key]["net_profit"] if key in pnl_idx.index else None
        eps = pnl_idx.loc[key]["eps"] if key in pnl_idx.index else None
        dividend_payout = pnl_idx.loc[key]["dividend_payout"] if key in pnl_idx.index else None
        
        # Balance Sheet Metrics
        equity_capital = bs_idx.loc[key]["equity_capital"] if key in bs_idx.index else None
        reserves = bs_idx.loc[key]["reserves"] if key in bs_idx.index else None
        borrowings = bs_idx.loc[key]["borrowings"] if key in bs_idx.index else None
        total_assets = bs_idx.loc[key]["total_assets"] if key in bs_idx.index else None
        investments = bs_idx.loc[key]["investments"] if key in bs_idx.index else None
        
        # Cash Flow Metrics
        cfo = cf_idx.loc[key]["operating_activity"] if key in cf_idx.index else None
        cfi = cf_idx.loc[key]["investing_activity"] if key in cf_idx.index else None
        cff = cf_idx.loc[key]["financing_activity"] if key in cf_idx.index else None
        
        # 1. Profitability & returns
        npm = calculate_npm(net_profit, sales)
        opm = calculate_opm(operating_profit, sales)
        roe = calculate_roe(net_profit, equity_capital, reserves)
        roce = calculate_roce(operating_profit, depreciation, equity_capital, reserves, borrowings)
        roa = calculate_roa(net_profit, total_assets)
        
        # 2. Leverage & Efficiency
        de = calculate_de(borrowings, equity_capital, reserves)
        icr = calculate_icr(operating_profit, other_income, interest)
        asset_turnover = calculate_asset_turnover(sales, total_assets)
        book_value_per_share = calculate_book_value_per_share(equity_capital, reserves, face_val)
        
        # Additional fields
        net_debt = to_float(borrowings) - to_float(investments)
        
        # D/E flag
        high_leverage_flag = 0
        if de is not None and de > 5.0 and broad_sector != "Financials":
            high_leverage_flag = 1
            
        # ICR label and warning
        icr_label = None
        icr_warning_flag = 0
        if interest == 0.0 or interest is None:
            icr_label = "Debt Free"
        else:
            if icr is not None and icr < 1.5:
                icr_warning_flag = 1
                
        # 3. Growth Metrics (CAGRs)
        # Parse year string (e.g. '2023-03' -> year=2023, month='03')
        year_num = int(yr_str.split("-")[0])
        month_str = yr_str.split("-")[1]
        
        def get_historical_val(c_id_val, target_year, col_name):
            target_yr_str = f"{target_year}-{month_str}"
            target_key = (c_id_val, target_yr_str)
            if target_key in pnl_idx.index:
                return pnl_idx.loc[target_key][col_name]
            return None
            
        # Compute CAGRs for 3yr, 5yr, 10yr windows
        # 5-year calculations for storage
        start_sales_5 = get_historical_val(c_id, year_num - 5, "sales")
        rev_cagr_5yr, rev_cagr_5yr_flag = calculate_cagr(sales, start_sales_5, 5)
        
        start_pat_5 = get_historical_val(c_id, year_num - 5, "net_profit")
        pat_cagr_5yr, pat_cagr_5yr_flag = calculate_cagr(net_profit, start_pat_5, 5)
        
        start_eps_5 = get_historical_val(c_id, year_num - 5, "eps")
        eps_cagr_5yr, eps_cagr_5yr_flag = calculate_cagr(eps, start_eps_5, 5)
        
        # Also compute 3yr and 10yr CAGRs (e.g. for complete capability coverage)
        start_sales_3 = get_historical_val(c_id, year_num - 3, "sales")
        rev_cagr_3yr, _ = calculate_cagr(sales, start_sales_3, 3)
        start_sales_10 = get_historical_val(c_id, year_num - 10, "sales")
        rev_cagr_10yr, _ = calculate_cagr(sales, start_sales_10, 10)
        
        start_pat_3 = get_historical_val(c_id, year_num - 3, "net_profit")
        pat_cagr_3yr, _ = calculate_cagr(net_profit, start_pat_3, 3)
        start_pat_10 = get_historical_val(c_id, year_num - 10, "net_profit")
        pat_cagr_10yr, _ = calculate_cagr(net_profit, start_pat_10, 10)
        
        start_eps_3 = get_historical_val(c_id, year_num - 3, "eps")
        eps_cagr_3yr, _ = calculate_cagr(eps, start_eps_3, 3)
        start_eps_10 = get_historical_val(c_id, year_num - 10, "eps")
        eps_cagr_10yr, _ = calculate_cagr(eps, start_eps_10, 10)

        # 4. Cash Flow metrics
        fcf = calculate_fcf(cfo, cfi)
        capex_intensity, capex_label = calculate_capex_intensity(cfi, sales)
        fcf_conversion = calculate_fcf_conversion(fcf, operating_profit)
        
        # Retrieve 5 years CFO and PAT list for CFO Quality Score
        cfo_list = []
        pat_list = []
        for i in range(5):
            y_offset = year_num - 4 + i
            offset_key = (c_id, f"{y_offset}-{month_str}")
            cfo_list.append(cf_idx.loc[offset_key]["operating_activity"] if offset_key in cf_idx.index else None)
            pat_list.append(pnl_idx.loc[offset_key]["net_profit"] if offset_key in pnl_idx.index else None)
            
        cfo_qual_score, cfo_qual_label = calculate_cfo_quality(cfo_list, pat_list)
        
        # Capital Allocation pattern classifier
        cfo_s, cfi_s, cff_s, alloc_pattern = classify_capital_allocation(cfo, cfi, cff, net_profit)
        
        capital_alloc_list.append({
            "company_id": c_id,
            "year": yr_str,
            "cfo_sign": cfo_s,
            "cfi_sign": cfi_s,
            "cff_sign": cff_s,
            "pattern_label": alloc_pattern
        })
        
        ratios_list.append({
            "company_id": c_id,
            "year": yr_str,
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "debt_to_equity": de,
            "interest_coverage": icr,
            "asset_turnover": asset_turnover,
            "free_cash_flow_cr": fcf,
            "capex_cr": abs(to_float(cfi)),
            "earnings_per_share": eps,
            "book_value_per_share": book_value_per_share,
            "dividend_payout_ratio_pct": dividend_payout,
            "total_debt_cr": borrowings,
            "cash_from_operations_cr": cfo,
            "revenue_cagr_5yr": rev_cagr_5yr,
            "pat_cagr_5yr": pat_cagr_5yr,
            "eps_cagr_5yr": eps_cagr_5yr,
            "high_leverage_flag": high_leverage_flag,
            "icr_label": icr_label,
            "icr_warning_flag": icr_warning_flag,
            "revenue_cagr_5yr_flag": rev_cagr_5yr_flag,
            "pat_cagr_5yr_flag": pat_cagr_5yr_flag,
            "eps_cagr_5yr_flag": eps_cagr_5yr_flag,
            # Placeholder for quality score calculation in the next step
            "composite_quality_score": 0.0,
            "roce_computed": roce  # keep temporarily for quality score winsorization
        })

    # 5. Composite Quality Score Calculations (Grouped by Year-Month)
    df_ratios = pd.DataFrame(ratios_list)
    df_ratios["composite_quality_score"] = 0.0
    
    # Piecewise interpolation for D/E score
    # D/E: 0=100, 0.5=85, 1=70, 2=50, >5=0
    xp_de = [0.0, 0.5, 1.0, 2.0, 5.0]
    fp_de = [100.0, 85.0, 70.0, 50.0, 0.0]
    
    def get_winsorized_scaled_score(series):
        # Drop nulls, calculate P10 and P90
        clean_series = series.dropna()
        if len(clean_series) < 2:
            return pd.Series(100.0, index=series.index)
        p10 = clean_series.quantile(0.10)
        p90 = clean_series.quantile(0.90)
        
        # Winsorize and scale
        winsorized = series.clip(p10, p90)
        if p90 == p10:
            return pd.Series(100.0, index=series.index)
        return (winsorized - p10) / (p90 - p10) * 100.0

    print("Computing Winsorized Composite Quality Scores per year...")
    # Group by year-month and compute
    for yr_grp, group in df_ratios.groupby("year"):
        # ROE score
        roe_score = get_winsorized_scaled_score(group["return_on_equity_pct"])
        # ROCE score
        roce_score = get_winsorized_scaled_score(group["roce_computed"])
        # FCF score
        fcf_score = get_winsorized_scaled_score(group["free_cash_flow_cr"])
        
        # D/E score using piecewise linear interpolation
        de_vals = group["debt_to_equity"].fillna(0.0).values
        de_score = np.interp(de_vals, xp_de, fp_de)
        de_score_series = pd.Series(de_score, index=group.index)
        
        # Composite score
        comp_score = 0.30 * roe_score + 0.25 * fcf_score + 0.25 * roce_score + 0.20 * de_score_series
        df_ratios.loc[group.index, "composite_quality_score"] = comp_score

    # Drop temporary column roce_computed
    df_ratios = df_ratios.drop(columns=["roce_computed"])
    
    # Fill remaining NaNs with None for SQLite insertion
    df_ratios = df_ratios.replace({np.nan: None})
    
    # 6. Recreate SQLite Table and Insert
    print("Re-initializing financial_ratios table in SQLite...")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS financial_ratios;")
    
    create_table_sql = """
    CREATE TABLE financial_ratios (
        company_id TEXT,
        year TEXT,
        net_profit_margin_pct REAL,
        operating_profit_margin_pct REAL,
        return_on_equity_pct REAL,
        debt_to_equity REAL,
        interest_coverage REAL,
        asset_turnover REAL,
        free_cash_flow_cr REAL,
        capex_cr REAL,
        earnings_per_share REAL,
        book_value_per_share REAL,
        dividend_payout_ratio_pct REAL,
        total_debt_cr REAL,
        cash_from_operations_cr REAL,
        revenue_cagr_5yr REAL,
        pat_cagr_5yr REAL,
        eps_cagr_5yr REAL,
        composite_quality_score REAL,
        high_leverage_flag INTEGER,
        icr_label TEXT,
        icr_warning_flag INTEGER,
        revenue_cagr_5yr_flag TEXT,
        pat_cagr_5yr_flag TEXT,
        eps_cagr_5yr_flag TEXT,
        PRIMARY KEY (company_id, year),
        FOREIGN KEY(company_id) REFERENCES companies(company_id) ON DELETE CASCADE
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    
    # Load conformed rows
    df_ratios.to_sql("financial_ratios", con=conn, if_exists="append", index=False)
    print(f"[OK] Re-created and loaded {len(df_ratios)} rows to financial_ratios table.")
    
    # 7. Generate output/capital_allocation.csv
    print("\nGenerating output/capital_allocation.csv...")
    os.makedirs("output", exist_ok=True)
    df_alloc = pd.DataFrame(capital_alloc_list)
    # Filter out records where signs are null
    df_alloc = df_alloc.dropna(subset=["cfo_sign", "cfi_sign", "cff_sign"])
    df_alloc.to_csv("output/capital_allocation.csv", index=False)
    print(f"  [OK] Saved capital_allocation.csv ({len(df_alloc)} rows)")
    
    # 8. Cross-check anomalies & write output/ratio_edge_cases.log
    print("\nPerforming ROCE, ROE, and OPM cross-checks...")
    log_entries = []
    
    # Retrieve pre-computed values from companies table
    comp_ref = pd.read_sql_query(
        "SELECT c.company_id, c.roce_percentage, c.roe_percentage, s.broad_sector "
        "FROM companies c "
        "JOIN sectors s ON c.sector_id = s.sector_id", conn
    )
    comp_ref_dict = comp_ref.set_index("company_id").to_dict(orient="index")
    
    # Strategy B: Find latest conformed year with both PnL and BS data present
    latest_matching_year = {}
    for c_id, yr_str in conformed_keys:
        key = (c_id, yr_str)
        if key in pnl_idx.index and key in bs_idx.index:
            latest_matching_year[c_id] = yr_str

    roce_latest_dict = {}
    roe_latest_dict = {}
    latest_year_dict = {}
    
    for c_id in valid_companies:
        lat_yr = latest_matching_year.get(c_id)
        if lat_yr is None:
            continue
        latest_year_dict[c_id] = lat_yr
        key = (c_id, lat_yr)
        
        # Calculate ROCE
        operating_profit = pnl_idx.loc[key]["operating_profit"] if key in pnl_idx.index else None
        depreciation = pnl_idx.loc[key]["depreciation"] if key in pnl_idx.index else None
        equity_capital = bs_idx.loc[key]["equity_capital"] if key in bs_idx.index else None
        reserves = bs_idx.loc[key]["reserves"] if key in bs_idx.index else None
        borrowings = bs_idx.loc[key]["borrowings"] if key in bs_idx.index else None
        
        roce_val = calculate_roce(operating_profit, depreciation, equity_capital, reserves, borrowings)
        roce_latest_dict[c_id] = roce_val
        
        # Calculate ROE
        net_profit = pnl_idx.loc[key]["net_profit"] if key in pnl_idx.index else None
        roe_val = calculate_roe(net_profit, equity_capital, reserves)
        roe_latest_dict[c_id] = roe_val
        
    # A. Check ROCE & ROE vs Companies table for latest conformed year
    for c_id in sorted(valid_companies):
        ref_data = comp_ref_dict.get(c_id, {})
        ref_roce = ref_data.get("roce_percentage")
        ref_roe = ref_data.get("roe_percentage")
        broad_sector = ref_data.get("broad_sector", "Unknown")
        
        comp_roce = roce_latest_dict.get(c_id)
        comp_roe = roe_latest_dict.get(c_id)
        lat_yr = latest_year_dict.get(c_id, "N/A")
        
        # Categorize ROCE anomalies
        if ref_roce is not None and pd.notna(ref_roce) and comp_roce is not None:
            diff_roce = abs(comp_roce - ref_roce)
            if diff_roce > 5.0:
                if c_id in ["BEL", "HAL", "LT"]:
                    cat = "data source issue"
                    expl = "Balance Sheet values in raw Excel are scaled down by 100x/1000x compared to P&L"
                elif broad_sector == "Financials":
                    cat = "formula discrepancy"
                    expl = "financial company ROCE calculations are structurally mismatched with standard industrial formulas"
                else:
                    cat = "formula discrepancy"
                    expl = "discrepancy due to different definition of EBIT or Capital Employed in source calculation"
                log_entries.append(
                    f"[{c_id}] ROCE anomaly at latest conformed year {lat_yr}: "
                    f"Computed={comp_roce:.2f}%, Source Excel={ref_roce:.2f}%, Diff={diff_roce:.2f}%. "
                    f"Category: {cat} ({expl})."
                )
                
        # Handle TCS ROE anomaly where source is 0.52 instead of 52%
        adjusted_ref_roe = ref_roe
        if c_id == "TCS" and ref_roe == 0.52:
            adjusted_ref_roe = 52.0
            
        # Categorize ROE anomalies
        if ref_roe is not None and pd.notna(ref_roe) and comp_roe is not None:
            diff_roe = abs(comp_roe - adjusted_ref_roe)
            if diff_roe > 5.0:
                if c_id == "TCS" and ref_roe == 0.52:
                    cat = "data source issue"
                    expl = "TCS ROE is formatted as 0.52 decimal in source Excel instead of 52.0%"
                elif c_id in ["BEL", "HAL", "LT"]:
                    cat = "data source issue"
                    expl = "Balance Sheet values in raw Excel are scaled down by 100x/1000x compared to P&L"
                else:
                    cat = "formula discrepancy"
                    expl = "discrepancy due to different definition of reserves/equity in source calculation"
                log_entries.append(
                    f"[{c_id}] ROE anomaly at latest conformed year {lat_yr}: "
                    f"Computed={comp_roe:.2f}%, Source Excel={ref_roe:.2f}%, Diff={diff_roe:.2f}%. "
                    f"Category: {cat} ({expl})."
                )

    # B. OPM cross-check for all conformed company-years
    for c_id, yr_str in conformed_keys:
        key = (c_id, yr_str)
        if key in pnl_idx.index:
            stored_opm = pnl_idx.loc[key]["opm_percentage"]
            sales = pnl_idx.loc[key]["sales"]
            operating_profit = pnl_idx.loc[key]["operating_profit"]
            comp_opm = calculate_opm(operating_profit, sales)
            
            if stored_opm is not None and pd.notna(stored_opm) and comp_opm is not None:
                diff_opm = abs(comp_opm - stored_opm)
                if diff_opm > 1.0:
                    expl = "stored opm_percentage is calculated differently or is anomalous in source data"
                    log_entries.append(
                        f"[{c_id}] [{yr_str}] OPM mismatch: Computed OPM={comp_opm:.2f}%, "
                        f"Stored opm_percentage={stored_opm:.2f}%, Diff={diff_opm:.2f}%. "
                        f"Category: formula discrepancy ({expl})."
                    )
                    
    # Write to output/ratio_edge_cases.log
    log_path = "output/ratio_edge_cases.log"
    with open(log_path, "w") as lf:
        if log_entries:
            lf.write("\n".join(log_entries) + "\n")
        else:
            lf.write("No ratio or margin discrepancies found.\n")
            
    print(f"  [OK] Saved {len(log_entries)} anomalies to {log_path}")
    
    conn.close()
    print("\nRatio Engine finished successfully!")

if __name__ == "__main__":
    main()

