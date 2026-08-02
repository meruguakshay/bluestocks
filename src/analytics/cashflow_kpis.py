import os
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")

def to_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def calculate_fcf(cfo, cfi):
    """
    Free Cash Flow: CFO + CFI
    """
    if cfo is None or pd.isna(cfo) or cfi is None or pd.isna(cfi):
        return None
    return float(cfo) + float(cfi)

def calculate_cfo_quality(cfo_history, pat_history):
    """
    CFO Quality Score: CFO / PAT ratio averaged over 5 years.
    Returns (avg_ratio, label)
    
    Labels:
    - >1.0 = High Quality
    - 0.5-1.0 = Moderate
    - <0.5 = Accrual Risk
    - return None if PAT = 0 in current year
    """
    if not cfo_history or not pat_history:
        return None, None
    if len(cfo_history) < 5 or len(pat_history) < 5:
        return None, None
        
    current_pat = pat_history[-1]
    if current_pat is None or pd.isna(current_pat) or current_pat == 0.0:
        return None, None
        
    ratios = []
    for cfo, pat in zip(cfo_history[-5:], pat_history[-5:]):
        if cfo is None or pd.isna(cfo) or pat is None or pd.isna(pat) or pat == 0.0:
            continue
        ratios.append(float(cfo) / float(pat))
        
    if not ratios:
        return None, None
        
    avg_ratio = sum(ratios) / len(ratios)
    
    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
        
    return avg_ratio, label

def calculate_capex_intensity(cfi, sales):
    """
    CapEx Intensity: abs(investing_activity) / sales x 100
    Returns (capex_pct, label)
    
    Labels:
    - <3% = Asset Light
    - 3-8% = Moderate
    - >8% = Capital Intensive
    """
    if cfi is None or pd.isna(cfi) or sales is None or pd.isna(sales) or sales == 0.0:
        return None, None
        
    capex_pct = (abs(float(cfi)) / float(sales)) * 100.0
    
    if capex_pct < 3.0:
        label = "Asset Light"
    elif capex_pct <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"
        
    return capex_pct, label

def calculate_fcf_conversion(fcf, operating_profit):
    """
    FCF Conversion Rate: FCF / operating_profit x 100
    """
    if fcf is None or pd.isna(fcf) or operating_profit is None or pd.isna(operating_profit) or operating_profit == 0.0:
        return None
    return (float(fcf) / float(operating_profit)) * 100.0

def classify_capital_allocation(cfo, cfi, cff, net_profit):
    """
    Capital allocation 8-pattern classifier based on signs of (CFO, CFI, CFF)
    where >= 0 is '+' and < 0 is '-'
    
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label)
    """
    if cfo is None or pd.isna(cfo) or cfi is None or pd.isna(cfi) or cff is None or pd.isna(cff):
        return None, None, None, "Unknown"
        
    cfo_sign = "+" if float(cfo) >= 0.0 else "-"
    cfi_sign = "+" if float(cfi) >= 0.0 else "-"
    cff_sign = "+" if float(cff) >= 0.0 else "-"
    
    # Check high CFO/PAT
    is_high_cfo_pat = False
    if net_profit is not None and pd.notna(net_profit) and net_profit > 0.0:
        if (float(cfo) / float(net_profit)) > 1.0:
            is_high_cfo_pat = True
            
    # Classify pattern
    if cfo_sign == "+" and cfi_sign == "-" and cff_sign == "-":
        if is_high_cfo_pat:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif cfo_sign == "+" and cfi_sign == "+" and cff_sign == "-":
        label = "Liquidating Assets"
    elif cfo_sign == "-" and cfi_sign == "+" and cff_sign == "+":
        label = "Distress Signal"
    elif cfo_sign == "-" and cfi_sign == "-" and cff_sign == "+":
        label = "Growth Funded by Debt"
    elif cfo_sign == "+" and cfi_sign == "+" and cff_sign == "+":
        label = "Cash Accumulator"
    elif cfo_sign == "-" and cfi_sign == "-" and cff_sign == "-":
        label = "Pre-Revenue"
    elif cfo_sign == "+" and cfi_sign == "-" and cff_sign == "+":
        label = "Mixed"
    elif cfo_sign == "-" and cfi_sign == "+" and cff_sign == "-":
        label = "Distress Signal"  # CFO < 0 is a distress signal
    else:
        label = "Mixed"
        
    return cfo_sign, cfi_sign, cff_sign, label

# ────────────────────────────────────────────────────────
# CLI ORCHESTRATION BLOCK (DAY 31)
# ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("RUNNING CASH FLOW INTELLIGENCE ENGINE (DAY 31)")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load raw data
    df_companies = pd.read_sql("SELECT company_id, company_name, sector_id FROM companies", conn)
    df_sectors = pd.read_sql("SELECT sector_id, broad_sector FROM sectors", conn)
    df_pnl = pd.read_sql("SELECT company_id, year, sales, net_profit, operating_profit FROM profitandloss ORDER BY company_id, year", conn)
    df_bs = pd.read_sql("SELECT company_id, year, borrowings FROM balancesheet ORDER BY company_id, year", conn)
    df_cf = pd.read_sql("SELECT company_id, year, operating_activity, investing_activity, financing_activity FROM cashflow ORDER BY company_id, year", conn)
    
    conn.close()
    
    # Map sectors
    sector_map = dict(zip(df_sectors["sector_id"], df_sectors["broad_sector"]))
    df_companies["broad_sector"] = df_companies["sector_id"].map(sector_map)
    comp_sector_dict = dict(zip(df_companies["company_id"], df_companies["broad_sector"]))
    
    # Group data by company for easy historical lookups
    pnl_by_comp = {c: grp.set_index("year").to_dict(orient="index") for c, grp in df_pnl.groupby("company_id")}
    cf_by_comp = {c: grp.set_index("year").to_dict(orient="index") for c, grp in df_cf.groupby("company_id")}
    bs_by_comp = {c: grp.set_index("year").to_dict(orient="index") for c, grp in df_bs.groupby("company_id")}
    
    # We will import calculate_cagr here to prevent circular dependency
    from src.analytics.cagr import calculate_cagr
    
    results = []
    distress_alerts = []
    
    for _, comp_row in df_companies.iterrows():
        comp_id = comp_row["company_id"]
        sector = comp_row["broad_sector"]
        
        # Get conformed years (years present in cashflow, profitandloss, and balancesheet)
        cf_years = set(cf_by_comp.get(comp_id, {}).keys())
        pnl_years = set(pnl_by_comp.get(comp_id, {}).keys())
        bs_years = set(bs_by_comp.get(comp_id, {}).keys())
        
        union_years = cf_years.intersection(pnl_years).intersection(bs_years)
        if not union_years:
            results.append({
                "company_id": comp_id,
                "sector": sector,
                "cfo_quality_score": None,
                "cfo_quality_label": "Unknown",
                "capex_intensity_pct": None,
                "capex_label": "Unknown",
                "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None,
                "distress_flag": 0,
                "deleveraging_flag": 0,
                "capital_allocation_label": "Unknown"
            })
            continue
            
        sorted_years = sorted(list(union_years))
        latest_year = sorted_years[-1]
        
        # Latest data
        lat_cf = cf_by_comp[comp_id][latest_year]
        lat_pnl = pnl_by_comp[comp_id][latest_year]
        lat_bs = bs_by_comp[comp_id][latest_year]
        
        cfo_val = to_float(lat_cf.get("operating_activity"))
        cfi_val = to_float(lat_cf.get("investing_activity"))
        cff_val = to_float(lat_cf.get("financing_activity"))
        sales_val = to_float(lat_pnl.get("sales"))
        net_profit_val = to_float(lat_pnl.get("net_profit"))
        operating_profit_val = to_float(lat_pnl.get("operating_profit"))
        borrowings_val = to_float(lat_bs.get("borrowings"))
        
        # 1. CFO Quality Score
        # Average CFO/PAT over 5 years (latest and 4 previous conformed years)
        cfo_history = []
        pat_history = []
        for yr in sorted_years[-5:]:
            yr_cf = cf_by_comp[comp_id].get(yr, {})
            yr_pnl = pnl_by_comp[comp_id].get(yr, {})
            cfo_history.append(to_float(yr_cf.get("operating_activity")))
            pat_history.append(to_float(yr_pnl.get("net_profit")))
            
        cfo_qual_score, cfo_qual_label = calculate_cfo_quality(cfo_history, pat_history)
        
        # 2. CapEx Intensity
        capex_intensity_pct, capex_label = calculate_capex_intensity(cfi_val, sales_val)
        
        # 3. FCF CAGR 5yr
        # FCF = CFO + CFI. Calculate for last 5 conformed years.
        fcf_history = []
        for yr in sorted_years[-5:]:
            yr_cf = cf_by_comp[comp_id].get(yr, {})
            y_cfo = to_float(yr_cf.get("operating_activity"))
            y_cfi = to_float(yr_cf.get("investing_activity"))
            fcf_history.append(calculate_fcf(y_cfo, y_cfi))
            
        fcf_cagr_5yr = None
        if len(fcf_history) >= 5 and fcf_history[0] is not None and fcf_history[-1] is not None:
            fcf_cagr_5yr, _ = calculate_cagr(fcf_history[-1], fcf_history[0], 4) # 5 years contains 4 intervals
            
        # 4. FCF Conversion Rate
        latest_fcf = calculate_fcf(cfo_val, cfi_val)
        fcf_conversion_pct = calculate_fcf_conversion(latest_fcf, operating_profit_val)
        
        # 5. Distress Signal
        # CFO < 0 AND CFF > 0 in latest year
        distress_flag = 1 if (cfo_val < 0.0 and cff_val > 0.0) else 0
        if distress_flag == 1:
            distress_alerts.append({
                "company_id": comp_id,
                "cfo_value": cfo_val,
                "cff_value": cff_val,
                "latest_net_profit": net_profit_val
            })
            
        # 6. Deleveraging Flag
        # CFF < 0 AND borrowings declining year-over-year
        deleveraging_flag = 0
        if len(sorted_years) >= 2:
            prev_year = sorted_years[-2]
            prev_bs = bs_by_comp[comp_id].get(prev_year, {})
            prev_borrowings = to_float(prev_bs.get("borrowings"))
            if cff_val < 0.0 and borrowings_val < prev_borrowings:
                deleveraging_flag = 1
                
        # 7. Capital Allocation pattern classifier
        _, _, _, alloc_pattern = classify_capital_allocation(cfo_val, cfi_val, cff_val, net_profit_val)
        
        results.append({
            "company_id": comp_id,
            "sector": sector,
            "cfo_quality_score": round(cfo_qual_score, 4) if cfo_qual_score is not None else None,
            "cfo_quality_label": cfo_qual_label,
            "capex_intensity_pct": round(capex_intensity_pct, 4) if capex_intensity_pct is not None else None,
            "capex_label": capex_label,
            "fcf_cagr_5yr": round(fcf_cagr_5yr, 4) if fcf_cagr_5yr is not None else None,
            "fcf_conversion_pct": round(fcf_conversion_pct, 4) if fcf_conversion_pct is not None else None,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": alloc_pattern
        })
        
    # Write output/cashflow_intelligence.xlsx
    df_results = pd.DataFrame(results)
    df_results.to_excel("output/cashflow_intelligence.xlsx", index=False)
    print(f"Saved {len(df_results)} rows to output/cashflow_intelligence.xlsx")
    
    # Write output/distress_alerts.csv
    df_alerts = pd.DataFrame(distress_alerts)
    if not df_alerts.empty:
        df_alerts.to_csv("output/distress_alerts.csv", index=False)
        print(f"Saved {len(df_alerts)} distressed companies to output/distress_alerts.csv")
    else:
        df_empty_alerts = pd.DataFrame(columns=["company_id", "cfo_value", "cff_value", "latest_net_profit"])
        df_empty_alerts.to_csv("output/distress_alerts.csv", index=False)
        print("No companies flagged with distress signal. Saved empty output/distress_alerts.csv")
        
    print("\nCash Flow Intelligence Engine completed successfully!")

if __name__ == "__main__":
    main()
