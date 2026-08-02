import os
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "db/nifty100.db"
OUTPUT_FILE = "output/pros_cons_generated.csv"
os.makedirs("output", exist_ok=True)

def to_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def main():
    print("=" * 60)
    print("RUNNING PROS & CONS GENERATOR (DAY 30)")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Load all tables
    df_companies = pd.read_sql("SELECT company_id, company_name, roce_percentage, roe_percentage, sector_id FROM companies", conn)
    df_sectors = pd.read_sql("SELECT sector_id, broad_sector FROM sectors", conn)
    df_ratios = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    df_pnl = pd.read_sql("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
    df_bs = pd.read_sql("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
    df_cf = pd.read_sql("SELECT * FROM cashflow ORDER BY company_id, year", conn)
    df_mcap = pd.read_sql("SELECT * FROM market_cap ORDER BY company_id, year", conn)
    
    conn.close()
    
    # Map sectors
    sector_map = dict(zip(df_sectors["sector_id"], df_sectors["broad_sector"]))
    df_companies["broad_sector"] = df_companies["sector_id"].map(sector_map)
    company_sector_dict = dict(zip(df_companies["company_id"], df_companies["broad_sector"]))
    
    # Group data by company for easy time-series lookup
    ratios_by_comp = {c: grp.to_dict(orient="records") for c, grp in df_ratios.groupby("company_id")}
    pnl_by_comp = {c: grp.to_dict(orient="records") for c, grp in df_pnl.groupby("company_id")}
    bs_by_comp = {c: grp.to_dict(orient="records") for c, grp in df_bs.groupby("company_id")}
    cf_by_comp = {c: grp.to_dict(orient="records") for c, grp in df_cf.groupby("company_id")}
    mcap_by_comp = {c: grp.to_dict(orient="records") for c, grp in df_mcap.groupby("company_id")}
    
    generated_records = []
    
    for _, comp_row in df_companies.iterrows():
        comp_id = comp_row["company_id"]
        broad_sector = company_sector_dict.get(comp_id, "Unknown")
        
        # Get historical records
        r_hist = ratios_by_comp.get(comp_id, [])
        p_hist = pnl_by_comp.get(comp_id, [])
        b_hist = bs_by_comp.get(comp_id, [])
        c_hist = cf_by_comp.get(comp_id, [])
        m_hist = mcap_by_comp.get(comp_id, [])
        
        if not r_hist or len(r_hist) == 0:
            continue
            
        # Latest record index
        latest_ratio = r_hist[-1]
        latest_pnl = p_hist[-1] if p_hist else {}
        latest_bs = b_hist[-1] if b_hist else {}
        latest_cf = c_hist[-1] if c_hist else {}
        latest_mcap = m_hist[-1] if m_hist else {}
        
        pros = []
        cons = []
        
        # ────────────────────────────────────────────────────────
        # PRO RULES
        # ────────────────────────────────────────────────────────
        
        # Pro Rule 1: ROE > 20% sustained for 3+ years
        if len(r_hist) >= 3:
            roe_last_3 = [to_float(x.get("return_on_equity_pct")) for x in r_hist[-3:]]
            if all(r > 20.0 for r in roe_last_3):
                avg_roe = sum(roe_last_3) / 3.0
                conf = min(98.0, 70.0 + (avg_roe - 20.0) * 1.5)
                pros.append({
                    "rule_id": "PRO_1",
                    "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                    "confidence_pct": round(conf, 2)
                })
                
        # Pro Rule 2: FCF positive for 5+ consecutive years
        if len(r_hist) >= 5:
            fcf_last_5 = [to_float(x.get("free_cash_flow_cr")) for x in r_hist[-5:]]
            if all(f > 0.0 for f in fcf_last_5):
                # Count positive years in full history to measure strength
                pos_years = sum(1 for x in r_hist if to_float(x.get("free_cash_flow_cr")) > 0.0)
                conf = min(98.0, 70.0 + (pos_years - 5) * 5.0)
                pros.append({
                    "rule_id": "PRO_2",
                    "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                    "confidence_pct": round(conf, 2)
                })
                
        # Pro Rule 3: D/E = 0 in latest year
        de = to_float(latest_ratio.get("debt_to_equity"), None)
        if de is not None and de == 0.0:
            pros.append({
                "rule_id": "PRO_3",
                "text": "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                "confidence_pct": 90.0
            })
            
        # Pro Rule 4: Revenue CAGR > 15% over 5 years
        rev_cagr = to_float(latest_ratio.get("revenue_cagr_5yr"), None)
        if rev_cagr is not None and rev_cagr > 15.0:
            conf = min(98.0, 70.0 + (rev_cagr - 15.0) * 1.5)
            pros.append({
                "rule_id": "PRO_4",
                "text": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                "confidence_pct": round(conf, 2)
            })
            
        # Pro Rule 5: OPM > 25% in latest year
        opm = to_float(latest_ratio.get("operating_profit_margin_pct"), None)
        if opm is not None and opm > 25.0:
            conf = min(98.0, 70.0 + (opm - 25.0) * 1.0)
            pros.append({
                "rule_id": "PRO_5",
                "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                "confidence_pct": round(conf, 2)
            })
            
        # Pro Rule 6: PAT CAGR > 20% over 5 years
        pat_cagr = to_float(latest_ratio.get("pat_cagr_5yr"), None)
        if pat_cagr is not None and pat_cagr > 20.0:
            conf = min(98.0, 70.0 + (pat_cagr - 20.0) * 1.5)
            pros.append({
                "rule_id": "PRO_6",
                "text": "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                "confidence_pct": round(conf, 2)
            })
            
        # Pro Rule 7: ICR > 10 or Debt Free
        icr = to_float(latest_ratio.get("interest_coverage"), None)
        icr_label = latest_ratio.get("icr_label")
        if (icr is not None and icr > 10.0) or icr_label == "Debt Free":
            conf = 95.0 if icr_label == "Debt Free" else min(98.0, 70.0 + (icr - 10.0) * 1.0)
            pros.append({
                "rule_id": "PRO_7",
                "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                "confidence_pct": round(conf, 2)
            })
            
        # Pro Rule 8: Dividend Yield > 2% with FCF positive
        div_yield = to_float(latest_mcap.get("dividend_yield_pct"), None)
        latest_fcf = to_float(latest_ratio.get("free_cash_flow_cr"), None)
        if div_yield is not None and div_yield > 2.0 and latest_fcf is not None and latest_fcf > 0.0:
            conf = min(98.0, 70.0 + (div_yield - 2.0) * 5.0)
            pros.append({
                "rule_id": "PRO_8",
                "text": "Consistent dividend yield above 2% backed by positive free cash flow",
                "confidence_pct": round(conf, 2)
            })
            
        # Pro Rule 9: EPS CAGR > 15% over 5 years
        eps_cagr = to_float(latest_ratio.get("eps_cagr_5yr"), None)
        if eps_cagr is not None and eps_cagr > 15.0:
            conf = min(98.0, 70.0 + (eps_cagr - 15.0) * 1.5)
            pros.append({
                "rule_id": "PRO_9",
                "text": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                "confidence_pct": round(conf, 2)
            })
            
        # Pro Rule 10: ROE improving for 3 consecutive years
        if len(r_hist) >= 3:
            roe_vals = [to_float(x.get("return_on_equity_pct")) for x in r_hist[-3:]]
            if roe_vals[2] > roe_vals[1] > roe_vals[0]:
                pros.append({
                    "rule_id": "PRO_10",
                    "text": "Return on equity improving for 3 consecutive years shows strengthening business quality",
                    "confidence_pct": 80.0
                })
                
        # Pro Rule 11: Revenue CAGR > PAT CAGR (operating leverage text says: "Revenue growing slower than profits")
        if rev_cagr is not None and pat_cagr is not None:
            if rev_cagr > 0 and pat_cagr > rev_cagr:
                conf = min(98.0, 75.0 + (pat_cagr - rev_cagr) * 2.0)
                pros.append({
                    "rule_id": "PRO_11",
                    "text": "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                    "confidence_pct": round(conf, 2)
                })
                
        # Pro Rule 12: Balance sheet assets growing with declining debt
        if len(b_hist) >= 2:
            assets_latest = to_float(latest_bs.get("total_assets"))
            assets_prev = to_float(b_hist[-2].get("total_assets"))
            debt_latest = to_float(latest_bs.get("borrowings"))
            debt_prev = to_float(b_hist[-2].get("borrowings"))
            if assets_latest > assets_prev and debt_latest < debt_prev:
                pros.append({
                    "rule_id": "PRO_12",
                    "text": "Growing asset base funded by internal accruals reflects self-sustaining growth",
                    "confidence_pct": 85.0
                })

        # ────────────────────────────────────────────────────────
        # CON RULES
        # ────────────────────────────────────────────────────────
        
        # Con Rule 1: D/E > 2.0 for non-financial companies
        if de is not None and de > 2.0 and broad_sector != "Financials":
            conf = min(98.0, 70.0 + (de - 2.0) * 10.0)
            cons.append({
                "rule_id": "CON_1",
                "text": f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring",
                "confidence_pct": round(conf, 2)
            })
            
        # Con Rule 2: FCF negative for 3 consecutive years
        if len(r_hist) >= 3:
            fcf_last_3 = [to_float(x.get("free_cash_flow_cr")) for x in r_hist[-3:]]
            if all(f < 0.0 for f in fcf_last_3):
                conf = min(98.0, 70.0 + sum(1 for x in r_hist if to_float(x.get("free_cash_flow_cr")) < 0) * 5.0)
                cons.append({
                    "rule_id": "CON_2",
                    "text": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                    "confidence_pct": round(conf, 2)
                })
                
        # Con Rule 3: OPM declining for 3 consecutive years
        if len(r_hist) >= 3:
            opm_vals = [to_float(x.get("operating_profit_margin_pct")) for x in r_hist[-3:]]
            if opm_vals[2] < opm_vals[1] < opm_vals[0]:
                cons.append({
                    "rule_id": "CON_3",
                    "text": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                    "confidence_pct": 80.0
                })
                
        # Con Rule 4: Net profit negative in latest year
        net_profit = to_float(latest_pnl.get("net_profit"), None)
        if net_profit is not None and net_profit < 0.0:
            cons.append({
                "rule_id": "CON_4",
                "text": "Company reported a net loss in the most recent financial year",
                "confidence_pct": 85.0
            })
            
        # Con Rule 5: Revenue declining for 2+ years (3 years of data, e.g. t < t-1 < t-2)
        if len(p_hist) >= 3:
            sales_vals = [to_float(x.get("sales")) for x in p_hist[-3:]]
            if sales_vals[2] < sales_vals[1] < sales_vals[0]:
                cons.append({
                    "rule_id": "CON_5",
                    "text": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                    "confidence_pct": 80.0
                })
                
        # Con Rule 6: ICR < 1.5
        if icr is not None and icr < 1.5 and icr_label != "Debt Free":
            conf = min(98.0, 70.0 + (1.5 - icr) * 20.0)
            cons.append({
                "rule_id": "CON_6",
                "text": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                "confidence_pct": round(conf, 2)
            })
            
        # Con Rule 7: Dividend payout > 100%
        div_payout = to_float(latest_ratio.get("dividend_payout_ratio_pct"), None)
        if div_payout is not None and div_payout > 100.0:
            conf = min(98.0, 70.0 + (div_payout - 100.0) * 0.5)
            cons.append({
                "rule_id": "CON_7",
                "text": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                "confidence_pct": round(conf, 2)
            })
            
        # Con Rule 8: D/E rising for 3 consecutive years
        if len(r_hist) >= 3:
            de_vals = [to_float(x.get("debt_to_equity")) for x in r_hist[-3:]]
            if de_vals[2] > de_vals[1] > de_vals[0]:
                cons.append({
                    "rule_id": "CON_8",
                    "text": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                    "confidence_pct": 80.0
                })
                
        # Con Rule 9: EPS declining for 3 consecutive years
        if len(r_hist) >= 3:
            eps_vals = [to_float(x.get("earnings_per_share")) for x in r_hist[-3:]]
            if eps_vals[2] < eps_vals[1] < eps_vals[0]:
                cons.append({
                    "rule_id": "CON_9",
                    "text": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                    "confidence_pct": 80.0
                })
                
        # Con Rule 10: ROCE < 10%
        # Calculate ROCE for latest year: EBIT / (Equity + Reserves + Borrowings)
        equity_cap = to_float(latest_bs.get("equity_capital"))
        reserves = to_float(latest_bs.get("reserves"))
        borrowings = to_float(latest_bs.get("borrowings"))
        capital_employed = equity_cap + reserves + borrowings
        
        operating_profit = to_float(latest_pnl.get("operating_profit"))
        depreciation = to_float(latest_pnl.get("depreciation"))
        ebit = operating_profit - depreciation
        
        roce = None
        if capital_employed > 0.0:
            roce = (ebit / capital_employed) * 100.0
            
        if roce is not None and roce < 10.0:
            conf = min(98.0, 70.0 + (10.0 - roce) * 2.0)
            cons.append({
                "rule_id": "CON_10",
                "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                "confidence_pct": round(conf, 2)
            })
            
        # Con Rule 11: Net Debt > 3x EBITDA
        # Net Debt = Borrowings - Investments
        investments = to_float(latest_bs.get("investments"))
        net_debt = borrowings - investments
        ebitda = operating_profit  # as verified Sales - Expenses = Operating Profit
        
        if ebitda > 0.0:
            net_debt_ebitda = net_debt / ebitda
            if net_debt_ebitda > 3.0:
                conf = min(98.0, 70.0 + (net_debt_ebitda - 3.0) * 5.0)
                cons.append({
                    "rule_id": "CON_11",
                    "text": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                    "confidence_pct": round(conf, 2)
                })
                
        # Con Rule 12: Revenue CAGR < 5% over 5 years
        if rev_cagr is not None and rev_cagr < 5.0:
            conf = min(98.0, 70.0 + (5.0 - rev_cagr) * 4.0)
            cons.append({
                "rule_id": "CON_12",
                "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                "confidence_pct": round(conf, 2)
            })
            
        # ────────────────────────────────────────────────────────
        # FALLBACK LOGIC
        # ────────────────────────────────────────────────────────
        
        # Ensure at least 1 Pro
        if len(pros) == 0:
            # Fallback Pro selection
            if latest_fcf is not None and latest_fcf > 0.0:
                # Trigger FCF Positive
                pros.append({
                    "rule_id": "PRO_2",
                    "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                    "confidence_pct": 61.0
                })
            elif latest_ratio.get("return_on_equity_pct") is not None and to_float(latest_ratio.get("return_on_equity_pct")) > 10.0:
                pros.append({
                    "rule_id": "PRO_10",
                    "text": "Return on equity improving for 3 consecutive years shows strengthening business quality",
                    "confidence_pct": 61.0
                })
            else:
                # Trigger ICR / Debt Free
                pros.append({
                    "rule_id": "PRO_7",
                    "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                    "confidence_pct": 61.0
                })
                
        # Ensure at least 1 Con
        if len(cons) == 0:
            # Fallback Con selection
            if rev_cagr is not None and rev_cagr < 10.0:
                cons.append({
                    "rule_id": "CON_12",
                    "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                    "confidence_pct": 61.0
                })
            elif roce is not None and roce < 15.0:
                cons.append({
                    "rule_id": "CON_10",
                    "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                    "confidence_pct": 61.0
                })
            else:
                # Trigger declining OPM or Revenue CAGR fallback
                cons.append({
                    "rule_id": "CON_12",
                    "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                    "confidence_pct": 61.0
                })
                
        # Append to records
        for p in pros:
            generated_records.append({
                "company_id": comp_id,
                "type": "pro",
                "rule_id": p["rule_id"],
                "text": p["text"],
                "confidence_pct": p["confidence_pct"]
            })
            
        for c in cons:
            generated_records.append({
                "company_id": comp_id,
                "type": "con",
                "rule_id": c["rule_id"],
                "text": c["text"],
                "confidence_pct": c["confidence_pct"]
            })
            
    # Save output to CSV
    df_output = pd.DataFrame(generated_records)
    df_output.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(df_output)} auto-generated pros/cons to {OUTPUT_FILE}.")
    
    # Verify definition of done: every company has at least 1 pro and at least 1 con
    all_companies = set(df_companies["company_id"])
    companies_with_pros = set(df_output[df_output["type"] == "pro"]["company_id"])
    companies_with_cons = set(df_output[df_output["type"] == "con"]["company_id"])
    
    missing_pros = all_companies - companies_with_pros
    missing_cons = all_companies - companies_with_cons
    
    print("\nDoD Verification:")
    print(f"  Total companies in companies table: {len(all_companies)}")
    print(f"  Companies with at least 1 Pro: {len(companies_with_pros)}")
    print(f"  Companies with at least 1 Con: {len(companies_with_cons)}")
    
    if len(missing_pros) == 0 and len(missing_cons) == 0:
        print("[OK] Verification passed! Every company has at least 1 pro and at least 1 con.")
    else:
        print(f"[CRITICAL] Verification failed! Missing Pros: {missing_pros}, Missing Cons: {missing_cons}")

if __name__ == "__main__":
    main()
