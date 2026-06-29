import sqlite3
import pandas as pd
import numpy as np
import os
from scipy.stats import linregress

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    dim_fund = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    conn.close()
    
    np.random.seed(42)
    
    # Re-generate 40 schemes
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

    df_fund_40 = pd.DataFrame(all_schemes)
    
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
    print("df_fund_40 shape:", df_fund_40.shape)
    print("df_nav_40 shape:", df_nav_40.shape)
    
    # Let's pivot NAV to get wide format and compute daily returns
    df_nav_pivot = df_nav_40.pivot(index='date', columns='scheme_code', values='nav')
    df_returns = df_nav_pivot.pct_change().dropna()
    print("df_returns shape:", df_returns.shape)
    
    # Check returns statistics for a few funds
    print("\nReturns statistics for 3 funds:")
    print(df_returns.iloc[:, :3].describe())
    
    # Now let's try creating a proxy for Nifty 100 and Nifty 50
    # Let's see how many Equity funds we have
    equity_codes = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].tolist()
    large_cap_codes = df_fund_40[(df_fund_40['category'] == 'Equity') & (df_fund_40['sub_category'] == 'Large Cap')]['scheme_code'].tolist()
    print(f"\nEquity funds count: {len(equity_codes)}")
    print(f"Large Cap funds count: {len(large_cap_codes)}")
    
    # Nifty 100 proxy: average return of all Equity funds
    nifty_100_returns = df_returns[equity_codes].mean(axis=1)
    # Nifty 50 proxy: average return of Large Cap Equity funds
    nifty_50_returns = df_returns[large_cap_codes].mean(axis=1)
    
    # Let's test regression for one Equity fund
    test_code = equity_codes[0]
    slope, intercept, r_value, p_value, std_err = linregress(nifty_100_returns, df_returns[test_code])
    beta = slope
    alpha = intercept * 252
    print(f"\nTest fund {test_code} regression against Nifty 100:")
    print(f"  Beta: {beta:.4f}")
    print(f"  Alpha (annualized): {alpha:.4f}")
    print(f"  R-squared: {r_value**2:.4f}")

    # Let's test regression for a Debt fund
    debt_codes = df_fund_40[df_fund_40['category'] == 'Debt']['scheme_code'].tolist()
    if debt_codes:
        test_debt_code = debt_codes[0]
        slope_d, intercept_d, r_d, p_d, std_err_d = linregress(nifty_100_returns, df_returns[test_debt_code])
        print(f"\nTest Debt fund {test_debt_code} regression against Nifty 100:")
        print(f"  Beta: {slope_d:.4f}")
        print(f"  Alpha (annualized): {intercept_d * 252:.4f}")
        print(f"  R-squared: {r_d**2:.4f}")

if __name__ == "__main__":
    main()
