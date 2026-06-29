import sqlite3
import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    dim_fund = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    fact_perf = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    conn.close()
    
    np.random.seed(42)
    existing_schemes = dim_fund.to_dict('records')
    missing_count = 40 - len(existing_schemes)
    fund_houses = ["SBI Mutual Fund", "HDFC Mutual Fund", "ICICI Prudential Mutual Fund", "Nippon India Mutual Fund", "Axis Mutual Fund", "Kotak Mahindra Mutual Fund"]
    categories = ["Equity", "Debt", "Hybrid"]
    sub_categories_map = {
        "Equity": ["Large Cap", "Mid Cap", "Small Cap"],
        "Debt": ["Liquid", "Corporate Bond", "Gilt"],
        "Hybrid": ["Balanced", "Arbitrage", "Dynamic Asset Allocation"]
    }
    risk_grades_map = {
        "Equity": "Very High",
        "Debt": "Low to Moderate",
        "Hybrid": "Moderate to High"
    }

    all_schemes = list(existing_schemes)
    for i in range(missing_count):
        code = 140000 + i + 1
        cat = np.random.choice(categories)
        sub_cat = np.random.choice(sub_categories_map[cat])
        fh = np.random.choice(fund_houses)
        risk = risk_grades_map[cat]
        isin = f"INF{code}D01012"
        name = f"{fh.split()[0]} {sub_cat} Fund - Direct Growth"
        all_schemes.append({
            "scheme_code": code,
            "isin": isin,
            "scheme_name": name,
            "fund_house": fh,
            "category": cat,
            "sub_category": sub_cat,
            "risk_grade": risk
        })

    dates_daily = pd.date_range(start="2022-01-01", end="2026-06-22", freq="D")
    nav_records = []
    for scheme in all_schemes:
        code = scheme["scheme_code"]
        cat = scheme["category"]
        base_nav = np.random.uniform(20.0, 150.0)
        
        if cat == "Equity":
            sigma = 0.012
        elif cat == "Hybrid":
            sigma = 0.008
        else:
            sigma = 0.001
            
        returns = []
        for dt in dates_daily:
            if pd.Timestamp("2023-04-01") <= dt <= pd.Timestamp("2023-12-31"):
                drift = 0.00125 if cat == "Equity" else (0.0007 if cat == "Hybrid" else 0.0002)
            elif dt == pd.Timestamp("2024-06-04"):
                drift = -0.078 if cat == "Equity" else (-0.038 if cat == "Hybrid" else -0.002)
            elif pd.Timestamp("2024-06-05") <= dt <= pd.Timestamp("2024-06-22"):
                drift = 0.0048 if cat == "Equity" else (0.0026 if cat == "Hybrid" else 0.0003)
            else:
                drift = 0.00035 if cat == "Equity" else (0.00022 if cat == "Hybrid" else 0.0001)
                
            ret = np.random.normal(drift, sigma)
            returns.append(ret)
            
        returns = np.array(returns)
        nav_values = base_nav * np.cumprod(1 + returns)
        
        for dt, val in zip(dates_daily, nav_values):
            nav_records.append({
                "scheme_code": code,
                "date": dt.strftime("%Y-%m-%d"),
                "nav": round(val, 4)
            })

    df_nav_40 = pd.DataFrame(nav_records)
    df_nav_pivot = df_nav_40.pivot(index='date', columns='scheme_code', values='nav')
    
    # Calculate CAGRs
    # End date: 2026-06-22
    # Start date 1yr: 2025-06-22
    # Start date 3yr: 2023-06-22
    # Start date 5yr: 2022-01-01 (since it starts on 2022-01-01, we use n = 4.47 years)
    
    end_date = "2026-06-22"
    start_1yr = "2025-06-22"
    start_3yr = "2023-06-22"
    start_5yr = "2022-01-01"
    
    cagr_results = []
    for code in df_nav_pivot.columns:
        nav_end = df_nav_pivot.loc[end_date, code]
        nav_1yr = df_nav_pivot.loc[start_1yr, code]
        nav_3yr = df_nav_pivot.loc[start_3yr, code]
        nav_5yr = df_nav_pivot.loc[start_5yr, code]
        
        cagr_1 = (nav_end / nav_1yr) ** 1.0 - 1
        cagr_3 = (nav_end / nav_3yr) ** (1/3.0) - 1
        
        # for 5yr, let's use the actual period of 4.47 years
        days = (pd.to_datetime(end_date) - pd.to_datetime(start_5yr)).days
        n_5 = days / 365.25
        cagr_5 = (nav_end / nav_5yr) ** (1/n_5) - 1
        
        cagr_results.append({
            "scheme_code": code,
            "calc_return_1yr": round(cagr_1 * 100, 2),
            "calc_return_3yr": round(cagr_3 * 100, 2),
            "calc_return_5yr": round(cagr_5 * 100, 2)
        })
        
    df_calc = pd.DataFrame(cagr_results)
    
    # Merge with fact_perf for comparison
    df_compare = pd.merge(fact_perf, df_calc, on="scheme_code")
    print(df_compare.head(10))

if __name__ == "__main__":
    main()
