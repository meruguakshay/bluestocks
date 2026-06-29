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
    
    # Re-generate 40 schemes (same as EDA notebook)
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
    
    # Map expense ratios
    db_expense = dict(zip(fact_performance['scheme_code'], fact_performance['expense_ratio']))
    merged_perf = pd.merge(fact_performance, dim_fund, on="scheme_code")
    cat_expense = merged_perf.groupby('category')['expense_ratio'].mean().to_dict()
    
    expense_ratios = []
    for s in all_schemes:
        code = s['scheme_code']
        cat = s['category']
        if code in db_expense:
            expense_ratios.append(db_expense[code])
        else:
            val = cat_expense.get(cat, 1.0) + np.random.uniform(-0.1, 0.1)
            expense_ratios.append(round(max(0.1, min(2.5, val)), 2))
            
    df_fund_40['expense_ratio'] = expense_ratios
    
    # Compute returns
    df_nav_pivot = df_nav_40.pivot(index='date', columns='scheme_code', values='nav')
    df_returns = df_nav_pivot.pct_change()
    
    # Nifty 100 proxy
    equity_codes = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].tolist()
    nifty_100_returns = df_returns[equity_codes].mean(axis=1)
    
    end_date = "2026-06-22"
    start_1yr = "2025-06-22"
    start_3yr = "2023-06-22"
    start_5yr = "2022-01-01"
    
    n_1yr = 1.0
    n_3yr = 3.0
    days_5 = (pd.to_datetime(end_date) - pd.to_datetime(start_5yr)).days
    n_5yr = days_5 / 365.25
    
    rf = 0.065
    metrics = []
    
    for code in df_nav_pivot.columns:
        nav_series = df_nav_pivot[code]
        rets_full = df_returns[code].dropna()
        
        # 3yr Return (CAGR)
        nav_end = nav_series.loc[end_date]
        nav_3 = nav_series.loc[start_3yr]
        cagr_3 = (nav_end / nav_3) ** (1 / n_3yr) - 1
        
        # Sharpe (using full period)
        mean_ret = rets_full.mean()
        std_ret = rets_full.std()
        sharpe = (mean_ret * 252 - rf) / (std_ret * np.sqrt(252)) if std_ret > 0 else 0
        
        # Alpha (using full period)
        aligned = pd.concat([rets_full, nifty_100_returns], axis=1).dropna()
        slope, intercept, _, _, _ = linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])
        alpha = intercept * 252
        
        # Max Drawdown (using full period)
        running_max = nav_series.cummax()
        drawdowns = nav_series / running_max - 1
        max_dd = drawdowns.min()
        
        metrics.append({
            "scheme_code": code,
            "cagr_3yr": cagr_3,
            "sharpe_ratio": sharpe,
            "alpha": alpha,
            "max_dd": max_dd
        })
        
    df_metrics = pd.DataFrame(metrics)
    df_metrics = pd.merge(df_metrics, df_fund_40[['scheme_code', 'scheme_name', 'category', 'expense_ratio']], on="scheme_code")
    
    # Let's perform ranks:
    # 1. 3yr return rank: highest gets rank 40
    # 2. Sharpe rank: highest gets rank 40
    # 3. Alpha rank: highest gets rank 40
    # 4. Expense ratio rank (inverse): lowest gets rank 40
    # 5. Max DD rank (inverse): closest to 0 gets rank 40 (which means largest negative is rank 1)
    
    # We will use rank method default (average or min). Let's use ascending=True or False.
    # Note: rank(pct=True) directly gives the percentile rank between 0 and 1.
    # Let's see: pct=True maps the lowest to 1/N, and the highest to 1.0.
    # To get 0-100 scale:
    df_metrics['rank_3yr'] = df_metrics['cagr_3yr'].rank(pct=True) * 100
    df_metrics['rank_sharpe'] = df_metrics['sharpe_ratio'].rank(pct=True) * 100
    df_metrics['rank_alpha'] = df_metrics['alpha'].rank(pct=True) * 100
    df_metrics['rank_expense'] = df_metrics['expense_ratio'].rank(ascending=False, pct=True) * 100
    df_metrics['rank_max_dd'] = df_metrics['max_dd'].rank(pct=True) * 100  # since max_dd is negative, e.g. -0.05 is > -0.50, so ascending=True correctly ranks -0.05 higher
    
    # Compute composite score:
    # 30% × 3yr return rank + 25% × Sharpe rank + 20% × Alpha rank + 15% × expense ratio rank (inverse) + 10% × max DD rank (inverse).
    df_metrics['score'] = (
        0.30 * df_metrics['rank_3yr'] +
        0.25 * df_metrics['rank_sharpe'] +
        0.20 * df_metrics['rank_alpha'] +
        0.15 * df_metrics['rank_expense'] +
        0.10 * df_metrics['rank_max_dd']
    )
    
    # Sort by score descending to rank all 40 funds:
    df_metrics = df_metrics.sort_values('score', ascending=False).reset_index(drop=True)
    df_metrics['final_rank'] = df_metrics.index + 1
    
    print("\n--- Top 10 Funds ---")
    print(df_metrics[['final_rank', 'scheme_code', 'scheme_name', 'category', 'score', 'cagr_3yr', 'sharpe_ratio', 'expense_ratio']].head(10))
    
    print("\n--- Bottom 5 Funds ---")
    print(df_metrics[['final_rank', 'scheme_code', 'scheme_name', 'category', 'score', 'cagr_3yr', 'sharpe_ratio', 'expense_ratio']].tail(5))

if __name__ == "__main__":
    main()
