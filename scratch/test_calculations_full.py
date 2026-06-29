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
    fact_performance = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    conn.close()
    
    np.random.seed(42)
    
    # 1. Re-generate 40 schemes (same as EDA notebook)
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
    
    # Generate daily NAVs (same as EDA notebook)
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
    
    # 2. Extract Expense Ratios and assign to the 14 simulated funds
    # Let's map existing expense ratios from DB
    db_expense = dict(zip(fact_performance['scheme_code'], fact_performance['expense_ratio']))
    
    # Calculate category wise mean expense ratios for imputation
    merged_perf = pd.merge(fact_performance, dim_fund, on="scheme_code")
    cat_expense = merged_perf.groupby('category')['expense_ratio'].mean().to_dict()
    print("Category mean expense ratios from DB:", cat_expense)
    
    expense_ratios = []
    for s in all_schemes:
        code = s['scheme_code']
        cat = s['category']
        if code in db_expense:
            expense_ratios.append(db_expense[code])
        else:
            # Assign category mean + small random variation
            val = cat_expense.get(cat, 1.0) + np.random.uniform(-0.1, 0.1)
            expense_ratios.append(round(clip_expense(val), 2))
            
    df_fund_40['expense_ratio'] = expense_ratios
    
    # Let's pivot NAV to get wide format and compute daily returns
    df_nav_pivot = df_nav_40.pivot(index='date', columns='scheme_code', values='nav')
    df_returns = df_nav_pivot.pct_change() # Keep NaN on first row or fill it? Keep it for daily return checks.
    
    # Validate distribution of daily returns
    # Check returns skewness and kurtosis
    print("\n--- Daily Returns Validation ---")
    skew = df_returns.skew()
    kurt = df_returns.kurtosis()
    print(f"Mean skewness: {skew.mean():.4f}, Mean kurtosis: {kurt.mean():.4f}")
    
    # Nifty 100 proxy: average return of all Equity funds
    equity_codes = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].tolist()
    large_cap_codes = df_fund_40[(df_fund_40['category'] == 'Equity') & (df_fund_40['sub_category'] == 'Large Cap')]['scheme_code'].tolist()
    
    nifty_100_returns = df_returns[equity_codes].mean(axis=1)
    nifty_50_returns = df_returns[large_cap_codes].mean(axis=1)
    
    # Let's calculate 1yr, 3yr, 5yr CAGRs
    # End date: 2026-06-22
    # Start dates:
    end_date = "2026-06-22"
    start_1yr = "2025-06-22"
    start_3yr = "2023-06-22"
    start_5yr = "2022-01-01"
    
    # Let's double check if these dates are weekends/holidays and if they exist
    print(f"End date NAV exists: {end_date in df_nav_pivot.index}")
    print(f"1Yr start date NAV exists: {start_1yr in df_nav_pivot.index}")
    print(f"3Yr start date NAV exists: {start_3yr in df_nav_pivot.index}")
    print(f"5Yr start date NAV exists: {start_5yr in df_nav_pivot.index}")
    
    # Standard period n:
    n_1yr = 1.0
    n_3yr = 3.0
    days_5 = (pd.to_datetime(end_date) - pd.to_datetime(start_5yr)).days
    n_5yr = days_5 / 365.25
    
    cagr_dict = {}
    for code in df_nav_pivot.columns:
        nav_end = df_nav_pivot.loc[end_date, code]
        nav_1 = df_nav_pivot.loc[start_1yr, code]
        nav_3 = df_nav_pivot.loc[start_3yr, code]
        nav_5 = df_nav_pivot.loc[start_5yr, code]
        
        cagr_1 = (nav_end / nav_1) ** (1 / n_1yr) - 1
        cagr_3 = (nav_end / nav_3) ** (1 / n_3yr) - 1
        cagr_5 = (nav_end / nav_5) ** (1 / n_5yr) - 1
        
        cagr_dict[code] = {
            "cagr_1yr": cagr_1,
            "cagr_3yr": cagr_3,
            "cagr_5yr": cagr_5
        }
        
    # Let's check Sharpe and Sortino Ratios (Rf = 6.5% = 0.065)
    # We will compute them using daily returns.
    # Note: daily risk free rate Rf_daily = 0.065 / 252.
    # Mean of daily returns * 252 gives annualized Rp, and Std(Rp_daily) * sqrt(252) gives annualized Std(Rp).
    # Then Sharpe = (Rp_annualized - Rf) / (Std(Rp_daily) * sqrt(252))
    # Let's verify:
    # Sortino denominator: downside standard deviation.
    # Downside standard deviation is computed from negative return days.
    # Let's see: if we only use negative return days, do we compute std(R_daily[R_daily < 0]) * sqrt(252)?
    # Yes! That is what the prompt specifies.
    
    rf = 0.065
    metrics_list = []
    
    # 3-year slice of returns for OLS, tracking error, etc.
    df_returns_3yr = df_returns.loc[start_3yr:end_date]
    nifty_100_returns_3yr = nifty_100_returns.loc[start_3yr:end_date]
    nifty_50_returns_3yr = nifty_50_returns.loc[start_3yr:end_date]
    
    for code in df_nav_pivot.columns:
        # Returns over the entire period (or 3-year? Let's check: typically metrics are computed over the full history,
        # but scorecard uses 3yr return rank. Let's compute ratios over the entire period first, and then check).
        # Wait, let's use the full period returns for standard deviation and Sharpe/Sortino.
        rets_full = df_returns[code].dropna()
        rets_3yr = df_returns_3yr[code].dropna()
        
        # Annualized return from daily mean:
        # Rp = mean(rets_full) * 252
        # Or do we use the CAGR?
        # CAGR is a more accurate measure of actual growth.
        # Let's use the full period CAGR as Rp (or 3yr CAGR for 3yr metrics, let's use full CAGR for full Sharpe).
        # Let's calculate Sharpe based on daily returns directly:
        # Sharpe = (mean(rets_full) * 252 - rf) / (std(rets_full) * np.sqrt(252))
        # This is the standard practice. Let's calculate Sharpe and Sortino based on daily returns.
        mean_ret = rets_full.mean()
        std_ret = rets_full.std()
        
        sharpe = (mean_ret * 252 - rf) / (std_ret * np.sqrt(252)) if std_ret > 0 else 0
        
        # Downside standard deviation (negative return days only)
        neg_rets = rets_full[rets_full < 0]
        std_downside = neg_rets.std()
        sortino = (mean_ret * 252 - rf) / (std_downside * np.sqrt(252)) if std_downside > 0 else 0
        
        # Regression against Nifty 100 (entire period)
        # scipy.stats.linregress
        # Align returns
        aligned = pd.concat([rets_full, nifty_100_returns], axis=1).dropna()
        slope, intercept, r_val, p_val, std_err = linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])
        beta = slope
        alpha = intercept * 252
        
        # Max Drawdown and Date Range (entire period)
        nav_series = df_nav_pivot[code]
        running_max = nav_series.cummax()
        drawdowns = nav_series / running_max - 1
        max_dd = drawdowns.min()
        
        # Worst drawdown date range:
        trough_idx = drawdowns.idxmin()
        # Find the peak before the trough
        peak_idx = nav_series.loc[:trough_idx].idxmax()
        # Find recovery date
        post_trough = nav_series.loc[trough_idx:]
        recovery_days = post_trough[post_trough >= nav_series.loc[peak_idx]]
        if not recovery_days.empty:
            recovery_idx = recovery_days.index[0]
        else:
            recovery_idx = "Not Recovered Yet"
            
        metrics_list.append({
            "scheme_code": code,
            "cagr_1yr": cagr_dict[code]["cagr_1yr"],
            "cagr_3yr": cagr_dict[code]["cagr_3yr"],
            "cagr_5yr": cagr_dict[code]["cagr_5yr"],
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "alpha": alpha,
            "beta": beta,
            "max_dd": max_dd,
            "drawdown_peak_date": peak_idx,
            "drawdown_trough_date": trough_idx,
            "drawdown_recovery_date": recovery_idx
        })
        
    df_metrics = pd.DataFrame(metrics_list)
    print("\nMetrics sample:")
    print(df_metrics.head(5))

def clip_expense(val):
    return max(0.1, min(2.5, val))

if __name__ == "__main__":
    main()
