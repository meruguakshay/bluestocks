import os
import json
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress, skew, kurtosis

# Setup directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
NOTEBOOK_PATH = os.path.join(BASE_DIR, "notebooks", "Performance_Analytics.ipynb")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CHARTS_DIR = os.path.join(REPORTS_DIR, "charts")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

def main():
    print("=" * 60)
    print("RUNNING MUTUAL FUND PERFORMANCE ANALYTICS")
    print("=" * 60)
    
    # ---------------------------------------------------------
    # 1. Load Data & Perform Simulation (Same as EDA Notebook)
    # ---------------------------------------------------------
    print("Loading data from database...")
    conn = sqlite3.connect(DB_PATH)
    dim_fund = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    fact_performance = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    conn.close()
    
    np.random.seed(42)
    
    # Expand schemes from 26 in DB to exactly 40
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
    
    # Impute expense ratios
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
    
    # Generate daily NAVs using Geometric Brownian Motion
    print("Simulating daily NAV history (2022-01-01 to 2026-06-22)...")
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
    
    # ---------------------------------------------------------
    # 2. Compute Daily Returns & Validate Distributions
    # ---------------------------------------------------------
    print("Computing daily returns and validating distribution...")
    df_nav_pivot = df_nav_40.pivot(index='date', columns='scheme_code', values='nav')
    df_returns = df_nav_pivot.pct_change()
    
    # Daily returns stats
    skewness_vals = df_returns.skew()
    kurtosis_vals = df_returns.kurtosis() # Excess kurtosis
    
    print(f"Daily returns: shape={df_returns.shape}")
    print(f"Mean returns skewness: {skewness_vals.mean():.4f} (expected near 0)")
    print(f"Mean returns excess kurtosis: {kurtosis_vals.mean():.4f} (expected near 0 for normal, or slightly positive)")
    
    # ---------------------------------------------------------
    # 3. Compute CAGR for 1yr, 3yr, 5yr
    # ---------------------------------------------------------
    print("Computing CAGR...")
    end_date = "2026-06-22"
    start_1yr = "2025-06-22"
    start_3yr = "2023-06-22"
    start_5yr = "2022-01-01"
    
    n_1yr = 1.0
    n_3yr = 3.0
    days_5 = (pd.to_datetime(end_date) - pd.to_datetime(start_5yr)).days
    n_5yr = days_5 / 365.25
    
    cagr_results = []
    for code in df_nav_pivot.columns:
        nav_end = df_nav_pivot.loc[end_date, code]
        nav_1 = df_nav_pivot.loc[start_1yr, code]
        nav_3 = df_nav_pivot.loc[start_3yr, code]
        nav_5 = df_nav_pivot.loc[start_5yr, code]
        
        c_1 = (nav_end / nav_1) ** (1 / n_1yr) - 1
        c_3 = (nav_end / nav_3) ** (1 / n_3yr) - 1
        c_5 = (nav_end / nav_5) ** (1 / n_5yr) - 1
        
        cagr_results.append({
            "scheme_code": code,
            "cagr_1yr": c_1,
            "cagr_3yr": c_3,
            "cagr_5yr": c_5
        })
    df_cagr = pd.DataFrame(cagr_results)
    
    # ---------------------------------------------------------
    # 4. Compute Sharpe & Sortino Ratios (Rf = 6.5%)
    # ---------------------------------------------------------
    print("Computing Sharpe and Sortino Ratios...")
    rf = 0.065
    ratios = []
    for code in df_nav_pivot.columns:
        rets = df_returns[code].dropna()
        # Annualized return from daily mean
        rp_annual = rets.mean() * 252
        std_annual = rets.std() * np.sqrt(252)
        
        # Sharpe
        sharpe = (rp_annual - rf) / std_annual if std_annual > 0 else 0
        
        # Sortino
        neg_rets = rets[rets < 0]
        std_downside = neg_rets.std() * np.sqrt(252)
        sortino = (rp_annual - rf) / std_downside if std_downside > 0 else 0
        
        ratios.append({
            "scheme_code": code,
            "rp_annualized_mean": rp_annual,
            "std_annualized": std_annual,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino
        })
    df_ratios = pd.DataFrame(ratios)
    
    # ---------------------------------------------------------
    # 5. Compute Alpha and Beta against Nifty 100
    # ---------------------------------------------------------
    print("Computing Alpha and Beta regressions against Nifty 100...")
    equity_codes = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].tolist()
    large_cap_codes = df_fund_40[(df_fund_40['category'] == 'Equity') & (df_fund_40['sub_category'] == 'Large Cap')]['scheme_code'].tolist()
    
    nifty_100_returns = df_returns[equity_codes].mean(axis=1)
    nifty_50_returns = df_returns[large_cap_codes].mean(axis=1)
    
    alpha_beta_list = []
    for code in df_nav_pivot.columns:
        rets = df_returns[code].dropna()
        # Align returns
        aligned = pd.concat([rets, nifty_100_returns], axis=1).dropna()
        slope, intercept, r_val, p_val, std_err = linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])
        alpha = intercept * 252 # Annualized Alpha
        beta = slope
        
        alpha_beta_list.append({
            "scheme_code": code,
            "alpha": alpha,
            "beta": beta,
            "r_squared": r_val ** 2
        })
    df_alpha_beta = pd.DataFrame(alpha_beta_list)
    
    # Save alpha_beta.csv to root
    df_alpha_beta_export = pd.merge(df_fund_40[['scheme_code', 'scheme_name', 'category']], df_alpha_beta, on="scheme_code")
    alpha_beta_path = os.path.join(BASE_DIR, "alpha_beta.csv")
    df_alpha_beta_export.to_csv(alpha_beta_path, index=False)
    print(f"  [OK] Saved alpha_beta.csv to {alpha_beta_path}")
    
    # ---------------------------------------------------------
    # 6. Compute Maximum Drawdown & Date Ranges
    # ---------------------------------------------------------
    print("Computing Maximum Drawdowns and Worst Date Ranges...")
    drawdown_list = []
    for code in df_nav_pivot.columns:
        nav_series = df_nav_pivot[code]
        running_max = nav_series.cummax()
        drawdowns = nav_series / running_max - 1
        max_dd = drawdowns.min()
        
        # Worst drawdown dates
        trough_idx = drawdowns.idxmin()
        peak_idx = nav_series.loc[:trough_idx].idxmax()
        
        # Recovery date
        post_trough = nav_series.loc[trough_idx:]
        recovery_days = post_trough[post_trough >= nav_series.loc[peak_idx]]
        if not recovery_days.empty:
            recovery_idx = recovery_days.index[0]
        else:
            recovery_idx = "Not Recovered Yet"
            
        drawdown_list.append({
            "scheme_code": code,
            "max_dd": max_dd,
            "drawdown_peak_date": peak_idx,
            "drawdown_trough_date": trough_idx,
            "drawdown_recovery_date": recovery_idx
        })
    df_drawdowns = pd.DataFrame(drawdown_list)
    
    # ---------------------------------------------------------
    # 7. Generate Composite Fund Scorecard
    # ---------------------------------------------------------
    print("Generating Composite Scorecard...")
    df_metrics = pd.merge(df_fund_40, df_cagr, on="scheme_code")
    df_metrics = pd.merge(df_metrics, df_ratios, on="scheme_code")
    df_metrics = pd.merge(df_metrics, df_alpha_beta, on="scheme_code")
    df_metrics = pd.merge(df_metrics, df_drawdowns, on="scheme_code")
    
    # Rank inputs to composite scorecard
    df_metrics['rank_3yr'] = df_metrics['cagr_3yr'].rank(pct=True) * 100
    df_metrics['rank_sharpe'] = df_metrics['sharpe_ratio'].rank(pct=True) * 100
    df_metrics['rank_alpha'] = df_metrics['alpha'].rank(pct=True) * 100
    df_metrics['rank_expense'] = df_metrics['expense_ratio'].rank(ascending=False, pct=True) * 100
    df_metrics['rank_max_dd'] = df_metrics['max_dd'].rank(pct=True) * 100 # Closer to 0 is higher rank
    
    # Weighted composite score
    df_metrics['score'] = (
        0.30 * df_metrics['rank_3yr'] +
        0.25 * df_metrics['rank_sharpe'] +
        0.20 * df_metrics['rank_alpha'] +
        0.15 * df_metrics['rank_expense'] +
        0.10 * df_metrics['rank_max_dd']
    )
    
    # Rank composite scorecard
    df_scorecard = df_metrics.sort_values('score', ascending=False).reset_index(drop=True)
    df_scorecard['final_rank'] = df_scorecard.index + 1
    
    scorecard_path = os.path.join(BASE_DIR, "fund_scorecard.csv")
    df_scorecard.to_csv(scorecard_path, index=False)
    print(f"  [OK] Saved fund_scorecard.csv to {scorecard_path}")
    
    # ---------------------------------------------------------
    # 8. Compute Tracking Error & Plot Benchmark Comparison Chart
    # ---------------------------------------------------------
    print("Plotting Benchmark Comparison Chart over 3 years...")
    top_5_funds = df_scorecard.head(5)
    print(f"Top 5 funds identified: {top_5_funds['scheme_name'].tolist()}")
    
    # Extract 3-year slice for plotting and tracking error
    df_returns_3yr = df_returns.loc[start_3yr:end_date]
    nifty_100_returns_3yr = nifty_100_returns.loc[start_3yr:end_date]
    nifty_50_returns_3yr = nifty_50_returns.loc[start_3yr:end_date]
    
    # Build daily index paths starting at 100 on 2023-06-22
    dates_3yr = df_returns_3yr.index
    
    bench_paths = pd.DataFrame(index=df_returns_3yr.index)
    
    # Normalize benchmarks
    cum_nifty_100 = (1 + nifty_100_returns_3yr).cumprod()
    # Shift index and prepend 100
    nifty_100_cum_val = [100.0]
    for val in cum_nifty_100:
        nifty_100_cum_val.append(100.0 * val)
    # The length is N_returns + 1
    
    # Let's construct a clean date index that starts on 2023-06-22
    all_dates_3yr = [start_3yr] + list(dates_3yr)
    
    df_chart = pd.DataFrame(index=all_dates_3yr)
    
    # Recalculate benchmark cumulative paths
    n100_path = [100.0]
    n50_path = [100.0]
    for r100, r50 in zip(nifty_100_returns_3yr, nifty_50_returns_3yr):
        n100_path.append(n100_path[-1] * (1 + r100))
        n50_path.append(n50_path[-1] * (1 + r50))
        
    df_chart['Nifty 100'] = n100_path
    df_chart['Nifty 50'] = n50_path
    
    # Calculate tracking errors and add fund paths
    tracking_errors = []
    for idx, row in top_5_funds.iterrows():
        code = row['scheme_code']
        name = row['scheme_name']
        
        # Calculate daily path
        nav_series_3yr = df_nav_pivot.loc[start_3yr:end_date, code]
        nav_norm = (nav_series_3yr / nav_series_3yr.loc[start_3yr]) * 100
        df_chart[name] = nav_norm
        
        # Compute tracking error
        fund_rets = df_returns_3yr[code]
        te_n100 = (fund_rets - nifty_100_returns_3yr).std() * np.sqrt(252)
        te_n50 = (fund_rets - nifty_50_returns_3yr).std() * np.sqrt(252)
        
        tracking_errors.append({
            "scheme_code": code,
            "scheme_name": name,
            "tracking_error_nifty100": te_n100,
            "tracking_error_nifty50": te_n50
        })
        
    df_te = pd.DataFrame(tracking_errors)
    print("\nTracking Errors for Top 5 Funds:")
    print(df_te.to_string(index=False))
    
    # Save the chart plot
    plt.figure(figsize=(12, 7.5))
    sns.set_theme(style="whitegrid")
    
    # Plot benchmarks
    plt.plot(df_chart.index, df_chart['Nifty 100'], label='Nifty 100 Index', color='#1e272e', linewidth=2.5, linestyle='--')
    plt.plot(df_chart.index, df_chart['Nifty 50'], label='Nifty 50 Index', color='#7f8c8d', linewidth=2.0, linestyle=':')
    
    # Plot top 5 funds
    colors = ['#1abc9c', '#3498db', '#9b59b6', '#e67e22', '#e74c3c']
    for idx, row in top_5_funds.reset_index(drop=True).iterrows():
        name = row['scheme_name']
        plt.plot(df_chart.index, df_chart[name], label=name, color=colors[idx], linewidth=2.0)
        
    plt.title("3-Year Cumulative Performance Comparison (Top 5 Funds vs. Benchmarks)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Date", fontsize=11)
    plt.ylabel("Normalized NAV / Index Value (Starts at 100)", fontsize=11)
    
    # Formatting X-axis dates
    ax = plt.gca()
    # Format x ticks to show every 6 months for readability
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    
    plt.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, edgecolor='#bdc3c7')
    plt.tight_layout()
    
    chart_path = os.path.join(BASE_DIR, "benchmark_comparison_chart.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    # Also save in reports/charts/
    plt.savefig(os.path.join(CHARTS_DIR, "benchmark_comparison_chart.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Saved benchmark comparison chart to {chart_path}")
    
    # ---------------------------------------------------------
    # 9. Generate completed Jupyter Notebook JSON
    # ---------------------------------------------------------
    print("Writing notebook structure...")
    generate_jupyter_notebook(df_te)
    
    print("\n[OK] Run analytics and generation completed successfully!")
    print("=" * 60)

def generate_jupyter_notebook(df_te):
    # We will write the text of the notebook's cells.
    # To keep it extremely clean and readable, we construct the cells list and write JSON.
    cells = []
    
    # Title
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Bluestock Mutual Fund Analytics — Performance and Risk Report\n",
            "This notebook computes the key performance and risk metrics for all **40 mutual fund schemes** (26 ingested from SQLite database + 14 augmented). It covers daily returns analysis, CAGR calculations, Sharpe/Sortino ratios, Alpha and Beta market regressions against Nifty 100, Maximum Drawdowns, and compiles a comprehensive Fund Scorecard to rank the schemes.\n",
            "\n",
            "## Content Index\n",
            "1. **Environment Setup & Data Augmentation**\n",
            "2. **Daily Returns & Distribution Analysis**\n",
            "3. **CAGR Analysis (1Yr, 3Yr, 5Yr)**\n",
            "4. **Risk-Adjusted Ratios (Sharpe, Sortino)**\n",
            "5. **Market Regression (Alpha, Beta against Nifty 100)**\n",
            "6. **Maximum Drawdown and Drawdown Periods**\n",
            "7. **Fund Scorecard (0-100)**\n",
            "8. **Benchmark Comparison Chart & Tracking Error**\n",
            "\n",
            "---"
        ]
    })
    
    # Cell 1: Environment Setup
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 1. Environment Setup & Data Augmentation\n",
            "We import the required scientific libraries, connect to the `bluestock_mf.db` SQLite database to load the conformed tables, and then augment the data to 40 funds. Finally, we simulate daily NAV histories over a 4.5-year period (2022-01-01 to 2026-06-22) using Geometric Brownian Motion (GBM) with a set seed of `42` to match the EDA notebook."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import sqlite3\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "from scipy.stats import linregress, skew, kurtosis\n",
            "\n",
            "%matplotlib inline\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "\n",
            "# Connect to database\n",
            "conn = sqlite3.connect('../bluestock_mf.db')\n",
            "dim_fund = pd.read_sql_query(\"SELECT * FROM dim_fund\", conn)\n",
            "fact_performance = pd.read_sql_query(\"SELECT * FROM fact_performance\", conn)\n",
            "conn.close()\n",
            "\n",
            "# Ingest and augment to 40 schemes\n",
            "np.random.seed(42)\n",
            "existing_schemes = dim_fund.to_dict('records')\n",
            "missing_count = 40 - len(existing_schemes)\n",
            "fund_houses = [\"SBI Mutual Fund\", \"HDFC Mutual Fund\", \"ICICI Prudential Mutual Fund\", \"Nippon India Mutual Fund\", \"Axis Mutual Fund\", \"Kotak Mahindra Mutual Fund\"]\n",
            "categories = [\"Equity\", \"Debt\", \"Hybrid\"]\n",
            "sub_categories_map = {\n",
            "    \"Equity\": [\"Large Cap\", \"Mid Cap\", \"Small Cap\"],\n",
            "    \"Debt\": [\"Liquid\", \"Corporate Bond\", \"Gilt\"],\n",
            "    \"Hybrid\": [\"Balanced\", \"Arbitrage\", \"Dynamic Asset Allocation\"]\n",
            "}\n",
            "risk_grades_map = {\n",
            "    \"Equity\": \"Very High\",\n",
            "    \"Debt\": \"Low to Moderate\",\n",
            "    \"Hybrid\": \"Moderate to High\"\n",
            "}\n",
            "\n",
            "all_schemes = list(existing_schemes)\n",
            "for i in range(missing_count):\n",
            "    code = 140000 + i + 1\n",
            "    cat = np.random.choice(categories)\n",
            "    sub_cat = np.random.choice(sub_categories_map[cat])\n",
            "    fh = np.random.choice(fund_houses)\n",
            "    risk = risk_grades_map[cat]\n",
            "    isin = f\"INF{code}D01012\"\n",
            "    name = f\"{fh.split()[0]} {sub_cat} Fund - Direct Growth\"\n",
            "    all_schemes.append({\n",
            "        \"scheme_code\": code,\n",
            "        \"isin\": isin,\n",
            "        \"scheme_name\": name,\n",
            "        \"fund_house\": fh,\n",
            "        \"category\": cat,\n",
            "        \"sub_category\": sub_cat,\n",
            "        \"risk_grade\": risk\n",
            "    })\n",
            "\n",
            "df_fund_40 = pd.DataFrame(all_schemes)\n",
            "\n",
            "# Map and impute expense ratios\n",
            "db_expense = dict(zip(fact_performance['scheme_code'], fact_performance['expense_ratio']))\n",
            "merged_perf = pd.merge(fact_performance, dim_fund, on=\"scheme_code\")\n",
            "cat_expense = merged_perf.groupby('category')['expense_ratio'].mean().to_dict()\n",
            "\n",
            "expense_ratios = []\n",
            "for s in all_schemes:\n",
            "    code = s['scheme_code']\n",
            "    cat = s['category']\n",
            "    if code in db_expense:\n",
            "        expense_ratios.append(db_expense[code])\n",
            "    else:\n",
            "        # category average + small random adjustment\n",
            "        val = cat_expense.get(cat, 1.0) + np.random.uniform(-0.1, 0.1)\n",
            "        expense_ratios.append(round(max(0.1, min(2.5, val)), 2))\n",
            "df_fund_40['expense_ratio'] = expense_ratios\n",
            "\n",
            "# Generate daily NAVs using Geometric Brownian Motion\n",
            "dates_daily = pd.date_range(start=\"2022-01-01\", end=\"2026-06-22\", freq=\"D\")\n",
            "nav_records = []\n",
            "for scheme in all_schemes:\n",
            "    code = scheme[\"scheme_code\"]\n",
            "    cat = scheme[\"category\"]\n",
            "    base_nav = np.random.uniform(20.0, 150.0)\n",
            "    \n",
            "    sigma = 0.012 if cat == \"Equity\" else (0.008 if cat == \"Hybrid\" else 0.001)\n",
            "    returns = []\n",
            "    for dt in dates_daily:\n",
            "        if pd.Timestamp(\"2023-04-01\") <= dt <= pd.Timestamp(\"2023-12-31\"):\n",
            "            drift = 0.00125 if cat == \"Equity\" else (0.0007 if cat == \"Hybrid\" else 0.0002)\n",
            "        elif dt == pd.Timestamp(\"2024-06-04\"):\n",
            "            drift = -0.078 if cat == \"Equity\" else (-0.038 if cat == \"Hybrid\" else -0.002)\n",
            "        elif pd.Timestamp(\"2024-06-05\") <= dt <= pd.Timestamp(\"2024-06-22\"):\n",
            "            drift = 0.0048 if cat == \"Equity\" else (0.0026 if cat == \"Hybrid\" else 0.0003)\n",
            "        else:\n",
            "            drift = 0.00035 if cat == \"Equity\" else (0.00022 if cat == \"Hybrid\" else 0.0001)\n",
            "        ret = np.random.normal(drift, sigma)\n",
            "        returns.append(ret)\n",
            "    returns = np.array(returns)\n",
            "    nav_values = base_nav * np.cumprod(1 + returns)\n",
            "    for dt, val in zip(dates_daily, nav_values):\n",
            "        nav_records.append({\"scheme_code\": code, \"date\": dt.strftime(\"%Y-%m-%d\"), \"nav\": round(val, 4)})\n",
            "\n",
            "df_nav_40 = pd.DataFrame(nav_records)\n",
            "print(f\"Loaded {len(df_fund_40)} funds and generated {len(df_nav_40)} daily NAV records.\")"
        ]
    })
    
    # Section 2: Daily Returns
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 2. Daily Returns & Distribution Analysis\n",
            "We calculate daily returns for each fund: $\\text{daily\\_return}_t = \\frac{\\text{NAV}_t}{\\text{NAV}_{t-1}} - 1$.\n",
            "We then plot histograms and Kernel Density Estimations (KDE) for a representative fund of each category (Equity, Debt, Hybrid) and compute the skewness and kurtosis of the daily returns to validate that the return distribution matches expectations."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Pivot and compute daily returns\n",
            "df_nav_pivot = df_nav_40.pivot(index='date', columns='scheme_code', values='nav')\n",
            "df_returns = df_nav_pivot.pct_change()\n",
            "\n",
            "# Select representative schemes\n",
            "eq_rep = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].iloc[0]\n",
            "db_rep = df_fund_40[df_fund_40['category'] == 'Debt']['scheme_code'].iloc[0]\n",
            "hb_rep = df_fund_40[df_fund_40['category'] == 'Hybrid']['scheme_code'].iloc[0]\n",
            "\n",
            "plt.figure(figsize=(15, 5))\n",
            "categories_rep = [(eq_rep, 'Equity Fund', '#1abc9c'), (db_rep, 'Debt Fund', '#34495e'), (hb_rep, 'Hybrid Fund', '#e67e22')]\n",
            "\n",
            "for idx, (code, title, color) in enumerate(categories_rep):\n",
            "    plt.subplot(1, 3, idx + 1)\n",
            "    data = df_returns[code].dropna()\n",
            "    sns.histplot(data, kde=True, color=color, stat=\"density\", bins=50)\n",
            "    \n",
            "    # Compute stats\n",
            "    s = skew(data)\n",
            "    k = kurtosis(data) # Excess kurtosis\n",
            "    plt.title(f\"{title} (Code: {code})\\nSkew: {s:.3f} | Excess Kurt: {k:.3f}\", fontsize=12, fontweight='bold')\n",
            "    plt.xlabel(\"Daily Return\")\n",
            "    plt.ylabel(\"Density\")\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "# Print aggregate return validation stats\n",
            "print(\"Aggregate Daily Return Distribution Validation:\")\n",
            "print(f\"  Mean Skewness across all 40 schemes: {df_returns.skew().mean():.4f} (expected near 0)\")\n",
            "print(f\"  Mean Excess Kurtosis across all 40 schemes: {df_returns.kurtosis().mean():.4f} (expected near 0 for Gaussian)\")"
        ]
    })
    
    # Section 3: CAGR
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 3. Compound Annual Growth Rate (CAGR)\n",
            "We compute the CAGR for 1-Year, 3-Year, and 5-Year periods using the formula: \n",
            "$$\\text{CAGR} = \\left(\\frac{\\text{NAV}_{\\text{end}}}{\\text{NAV}_{\\text{start}}}\\right)^{\\frac{1}{n}} - 1$$\n",
            "Where $n$ is the number of years. Since our daily NAV simulation starts on `2022-01-01` and ends on `2026-06-22` (4.47 years total), the \"5-Year CAGR\" is calculated over this maximum available period of 4.47 years ($n=4.4736$)."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "end_date = \"2026-06-22\"\n",
            "start_1yr = \"2025-06-22\"\n",
            "start_3yr = \"2023-06-22\"\n",
            "start_5yr = \"2022-01-01\"\n",
            "\n",
            "n_1yr = 1.0\n",
            "n_3yr = 3.0\n",
            "days_5 = (pd.to_datetime(end_date) - pd.to_datetime(start_5yr)).days\n",
            "n_5yr = days_5 / 365.25\n",
            "\n",
            "cagr_results = []\n",
            "for code in df_nav_pivot.columns:\n",
            "    nav_end = df_nav_pivot.loc[end_date, code]\n",
            "    nav_1 = df_nav_pivot.loc[start_1yr, code]\n",
            "    nav_3 = df_nav_pivot.loc[start_3yr, code]\n",
            "    nav_5 = df_nav_pivot.loc[start_5yr, code]\n",
            "    \n",
            "    c_1 = (nav_end / nav_1) ** (1 / n_1yr) - 1\n",
            "    c_3 = (nav_end / nav_3) ** (1 / n_3yr) - 1\n",
            "    c_5 = (nav_end / nav_5) ** (1 / n_5yr) - 1\n",
            "    \n",
            "    cagr_results.append({\n",
            "        \"scheme_code\": code,\n",
            "        \"cagr_1yr\": c_1,\n",
            "        \"cagr_3yr\": c_3,\n",
            "        \"cagr_5yr\": c_5\n",
            "    })\n",
            "df_cagr = pd.DataFrame(cagr_results)\n",
            "df_cagr_display = pd.merge(df_fund_40[['scheme_code', 'scheme_name', 'category']], df_cagr, on=\"scheme_code\")\n",
            "\n",
            "print(\"CAGR Comparison (First 10 Schemes):\")\n",
            "display_cols = ['scheme_code', 'scheme_name', 'category', 'cagr_1yr', 'cagr_3yr', 'cagr_5yr']\n",
            "print(df_cagr_display[display_cols].head(10).to_string(formatters={\n",
            "    'cagr_1yr': '{:.2%}'.format,\n",
            "    'cagr_3yr': '{:.2%}'.format,\n",
            "    'cagr_5yr': '{:.2%}'.format\n",
            "}))"
        ]
    })
    
    # Section 4: Sharpe and Sortino Ratios
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 4. Sharpe & Sortino Ratios\n",
            "We compute risk-adjusted returns ratios relative to the risk-free rate proxy $R_f = 6.5\\%$ (the RBI repo rate proxy). \n",
            "\n",
            "**Sharpe Ratio Formula**:\n",
            "$$S_p = \\frac{R_p - R_f}{\\sigma(R_p)} \\times \\sqrt{252}$$\n",
            "Where $R_p$ is the annualized mean of daily returns ($R_p = \\text{mean}(R_{\\text{daily}}) \\times 252$), and $\\sigma(R_p)$ is the standard deviation of daily returns.\n",
            "\n",
            "**Sortino Ratio Formula**:\n",
            "$$\\text{Sortino} = \\frac{R_p - R_f}{\\sigma_{\\text{downside}}(R_p)} \\times \\sqrt{252}$$\n",
            "Where $\\sigma_{\\text{downside}}(R_p)$ is the standard deviation computed on negative daily returns only ($R_{\\text{daily}} < 0$). We rank all 40 funds by these ratios."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "rf = 0.065\n",
            "ratios = []\n",
            "for code in df_nav_pivot.columns:\n",
            "    rets = df_returns[code].dropna()\n",
            "    rp_annual = rets.mean() * 252\n",
            "    std_annual = rets.std() * np.sqrt(252)\n",
            "    \n",
            "    sharpe = (rp_annual - rf) / std_annual if std_annual > 0 else 0\n",
            "    \n",
            "    neg_rets = rets[rets < 0]\n",
            "    std_downside = neg_rets.std() * np.sqrt(252)\n",
            "    sortino = (rp_annual - rf) / std_downside if std_downside > 0 else 0\n",
            "    \n",
            "    ratios.append({\n",
            "        \"scheme_code\": code,\n",
            "        \"rp_annualized_mean\": rp_annual,\n",
            "        \"std_annualized\": std_annual,\n",
            "        \"sharpe_ratio\": sharpe,\n",
            "        \"sortino_ratio\": sortino\n",
            "    })\n",
            "df_ratios = pd.DataFrame(ratios)\n",
            "df_ratios_display = pd.merge(df_fund_40[['scheme_code', 'scheme_name', 'category']], df_ratios, on=\"scheme_code\")\n",
            "\n",
            "print(\"Sharpe & Sortino Ratios (Top 10 ranked by Sharpe):\")\n",
            "print(df_ratios_display.sort_values('sharpe_ratio', ascending=False).head(10).to_string(index=False, columns=[\n",
            "    'scheme_code', 'scheme_name', 'category', 'rp_annualized_mean', 'std_annualized', 'sharpe_ratio', 'sortino_ratio'\n",
            "], formatters={\n",
            "    'rp_annualized_mean': '{:.2%}'.format,\n",
            "    'std_annualized': '{:.2%}'.format,\n",
            "    'sharpe_ratio': '{:.3f}'.format,\n",
            "    'sortino_ratio': '{:.3f}'.format\n",
            "}))"
        ]
    })
    
    # Section 5: Alpha and Beta
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 5. Alpha & Beta Regressions (against Nifty 100)\n",
            "We regress the daily returns of each fund against the Nifty 100 returns (proxied by the average of all Equity funds). The regression coefficients provide the Beta (slope) and Alpha (annualized intercept $= \\text{intercept} \\times 252$). We save the results in `alpha_beta.csv`."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "equity_codes = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].tolist()\n",
            "nifty_100_returns = df_returns[equity_codes].mean(axis=1)\n",
            "\n",
            "alpha_beta_list = []\n",
            "for code in df_nav_pivot.columns:\n",
            "    rets = df_returns[code].dropna()\n",
            "    aligned = pd.concat([rets, nifty_100_returns], axis=1).dropna()\n",
            "    slope, intercept, r_val, p_val, std_err = linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])\n",
            "    alpha = intercept * 252\n",
            "    beta = slope\n",
            "    \n",
            "    alpha_beta_list.append({\n",
            "        \"scheme_code\": code,\n",
            "        \"alpha\": alpha,\n",
            "        \"beta\": beta,\n",
            "        \"r_squared\": r_val ** 2\n",
            "    })\n",
            "df_alpha_beta = pd.DataFrame(alpha_beta_list)\n",
            "df_alpha_beta_display = pd.merge(df_fund_40[['scheme_code', 'scheme_name', 'category']], df_alpha_beta, on=\"scheme_code\")\n",
            "\n",
            "print(\"Alpha & Beta Coefficients (First 10 Schemes):\")\n",
            "print(df_alpha_beta_display.head(10).to_string(index=False, formatters={\n",
            "    'alpha': '{:.2%}'.format,\n",
            "    'beta': '{:.4f}'.format,\n",
            "    'r_squared': '{:.4%}'.format\n",
            "}))"
        ]
    })
    
    # Section 6: Maximum Drawdown
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 6. Maximum Drawdown & Worst Date Ranges\n",
            "Maximum Drawdown measures the peak-to-trough decline for each fund. The formula is:\n",
            "$$\\text{Drawdown} = \\frac{\\text{NAV}_t}{\\text{Running Max NAV}_t} - 1$$\n",
            "The Maximum Drawdown is the minimum of this series. We also trace the Peak Date, Trough Date, and the subsequent Recovery Date."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "drawdown_list = []\n",
            "for code in df_nav_pivot.columns:\n",
            "    nav_series = df_nav_pivot[code]\n",
            "    running_max = nav_series.cummax()\n",
            "    drawdowns = nav_series / running_max - 1\n",
            "    max_dd = drawdowns.min()\n",
            "    \n",
            "    trough_idx = drawdowns.idxmin()\n",
            "    peak_idx = nav_series.loc[:trough_idx].idxmax()\n",
            "    \n",
            "    post_trough = nav_series.loc[trough_idx:]\n",
            "    recovery_days = post_trough[post_trough >= nav_series.loc[peak_idx]]\n",
            "    recovery_idx = recovery_days.index[0] if not recovery_days.empty else \"Not Recovered Yet\"\n",
            "    \n",
            "    drawdown_list.append({\n",
            "        \"scheme_code\": code,\n",
            "        \"max_dd\": max_dd,\n",
            "        \"drawdown_peak_date\": peak_idx,\n",
            "        \"drawdown_trough_date\": trough_idx,\n",
            "        \"drawdown_recovery_date\": recovery_idx\n",
            "    })\n",
            "df_drawdowns = pd.DataFrame(drawdown_list)\n",
            "df_drawdowns_display = pd.merge(df_fund_40[['scheme_code', 'scheme_name', 'category']], df_drawdowns, on=\"scheme_code\")\n",
            "\n",
            "print(\"Maximum Drawdown & Date Ranges (Top 10 worst drawdowns):\")\n",
            "print(df_drawdowns_display.sort_values('max_dd').head(10).to_string(index=False, formatters={\n",
            "    'max_dd': '{:.2%}'.format\n",
            "}))"
        ]
    })
    
    # Section 7: Scorecard
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 7. Fund Scorecard\n",
            "We build a composite scorecard (0-100 scale) for all 40 funds using percentile ranks:\n",
            "$$\\text{Score} = 30\\% \\times \\text{Rank}_{\\text{3yr Return}} + 25\\% \\times \\text{Rank}_{\\text{Sharpe}} + 20\\% \\times \\text{Rank}_{\\text{Alpha}} + 15\\% \\times \\text{Rank}_{\\text{Expense (inv)}} + 10\\% \\times \\text{Rank}_{\\text{Max DD (inv)}}$$\n",
            "Percentile ranks map values between `2.5%` and `100%` (for $N=40$). The inverse rankings mean lower values get higher percentile ranks (better). The scorecard is saved to `fund_scorecard.csv`."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "df_metrics = pd.merge(df_fund_40, df_cagr, on=\"scheme_code\")\n",
            "df_metrics = pd.merge(df_metrics, df_ratios, on=\"scheme_code\")\n",
            "df_metrics = pd.merge(df_metrics, df_alpha_beta, on=\"scheme_code\")\n",
            "df_metrics = pd.merge(df_metrics, df_drawdowns, on=\"scheme_code\")\n",
            "\n",
            "df_metrics['rank_3yr'] = df_metrics['cagr_3yr'].rank(pct=True) * 100\n",
            "df_metrics['rank_sharpe'] = df_metrics['sharpe_ratio'].rank(pct=True) * 100\n",
            "df_metrics['rank_alpha'] = df_metrics['alpha'].rank(pct=True) * 100\n",
            "df_metrics['rank_expense'] = df_metrics['expense_ratio'].rank(ascending=False, pct=True) * 100\n",
            "df_metrics['rank_max_dd'] = df_metrics['max_dd'].rank(pct=True) * 100\n",
            "\n",
            "df_metrics['score'] = (\n",
            "    0.30 * df_metrics['rank_3yr'] +\n",
            "    0.25 * df_metrics['rank_sharpe'] +\n",
            "    0.20 * df_metrics['rank_alpha'] +\n",
            "    0.15 * df_metrics['rank_expense'] +\n",
            "    0.10 * df_metrics['rank_max_dd']\n",
            ")\n",
            "\n",
            "df_scorecard = df_metrics.sort_values('score', ascending=False).reset_index(drop=True)\n",
            "df_scorecard['final_rank'] = df_scorecard.index + 1\n",
            "\n",
            "print(\"Scorecard Top 10 Funds:\")\n",
            "print(df_scorecard.head(10).to_string(index=False, columns=[\n",
            "    'final_rank', 'scheme_code', 'scheme_name', 'category', 'score', 'cagr_3yr', 'sharpe_ratio', 'expense_ratio', 'max_dd'\n",
            "], formatters={\n",
            "    'score': '{:.2f}'.format,\n",
            "    'cagr_3yr': '{:.2%}'.format,\n",
            "    'sharpe_ratio': '{:.3f}'.format,\n",
            "    'expense_ratio': '{:.2f}%'.format,\n",
            "    'max_dd': '{:.2%}'.format\n",
            "}))"
        ]
    })
    
    # Section 8: Benchmark comparison chart and tracking error
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### 8. Benchmark Comparison Chart & Tracking Error\n",
            "We identify the top 5 funds from the scorecard. We normalize the NAVs and benchmarks (Nifty 50 and Nifty 100) to start at 100 on `2023-06-22` and plot their growth paths. We also compute each fund's Tracking Error relative to both benchmarks over the 3-year period:\n",
            "$$\\text{Tracking Error} = \\sigma(R_{\\text{fund}} - R_{\\text{benchmark}}) \\times \\sqrt{252}$$"
        ]
    })
    
    # Pre-render tracking error data into the source code cell to avoid runtime variables
    te_rows = []
    for idx, row in df_te.iterrows():
        te_rows.append(f"    {dict(row)},")
    te_data_str = "\n".join(te_rows)
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "top_5_funds = df_scorecard.head(5)\n",
            "large_cap_codes = df_fund_40[(df_fund_40['category'] == 'Equity') & (df_fund_40['sub_category'] == 'Large Cap')]['scheme_code'].tolist()\n",
            "equity_codes = df_fund_40[df_fund_40['category'] == 'Equity']['scheme_code'].tolist()\n",
            "\n",
            "df_returns_3yr = df_returns.loc[start_3yr:end_date]\n",
            "nifty_100_returns_3yr = df_returns_3yr[equity_codes].mean(axis=1)\n",
            "nifty_50_returns_3yr = df_returns_3yr[large_cap_codes].mean(axis=1)\n",
            "\n",
            "all_dates_3yr = [start_3yr] + list(df_returns_3yr.index)\n",
            "df_chart = pd.DataFrame(index=all_dates_3yr)\n",
            "\n",
            "n100_path = [100.0]\n",
            "n50_path = [100.0]\n",
            "for r100, r50 in zip(nifty_100_returns_3yr, nifty_50_returns_3yr):\n",
            "    n100_path.append(n100_path[-1] * (1 + r100))\n",
            "    n50_path.append(n50_path[-1] * (1 + r50))\n",
            "\n",
            "df_chart['Nifty 100'] = n100_path\n",
            "df_chart['Nifty 50'] = n50_path\n",
            "\n",
            "tracking_errors = []\n",
            "for idx, row in top_5_funds.iterrows():\n",
            "    code = row['scheme_code']\n",
            "    name = row['scheme_name']\n",
            "    \n",
            "    nav_series_3yr = df_nav_pivot.loc[start_3yr:end_date, code]\n",
            "    nav_norm = (nav_series_3yr / nav_series_3yr.loc[start_3yr]) * 100\n",
            "    df_chart[name] = nav_norm\n",
            "    \n",
            "    fund_rets = df_returns_3yr[code]\n",
            "    te_n100 = (fund_rets - nifty_100_returns_3yr).std() * np.sqrt(252)\n",
            "    te_n50 = (fund_rets - nifty_50_returns_3yr).std() * np.sqrt(252)\n",
            "    \n",
            "    tracking_errors.append({\n",
            "        \"scheme_code\": code,\n",
            "        \"scheme_name\": name,\n",
            "        \"tracking_error_nifty100\": te_n100,\n",
            "        \"tracking_error_nifty50\": te_n50\n",
            "    })\n",
            "\n",
            "df_te = pd.DataFrame(tracking_errors)\n",
            "\n",
            "plt.figure(figsize=(12, 7.5))\n",
            "plt.plot(df_chart.index, df_chart['Nifty 100'], label='Nifty 100 Index', color='#1e272e', linewidth=2.5, linestyle='--')\n",
            "plt.plot(df_chart.index, df_chart['Nifty 50'], label='Nifty 50 Index', color='#7f8c8d', linewidth=2.0, linestyle=':')\n",
            "\n",
            "colors = ['#1abc9c', '#3498db', '#9b59b6', '#e67e22', '#e74c3c']\n",
            "for idx, row in top_5_funds.reset_index(drop=True).iterrows():\n",
            "    name = row['scheme_name']\n",
            "    plt.plot(df_chart.index, df_chart[name], label=name, color=colors[idx], linewidth=2.0)\n",
            "\n",
            "plt.title(\"3-Year Cumulative Performance Comparison (Top 5 Funds vs. Benchmarks)\", fontsize=14, fontweight='bold', pad=15)\n",
            "plt.xlabel(\"Date\", fontsize=11)\n",
            "plt.ylabel(\"Normalized NAV / Index Value (Starts at 100)\", fontsize=11)\n",
            "plt.xticks(rotation=45)\n",
            "plt.legend(loc='upper left')\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "print(\"Tracking Errors:\")\n",
            "print(df_te.to_string(index=False, formatters={\n",
            "    'tracking_error_nifty100': '{:.2%}'.format,\n",
            "    'tracking_error_nifty50': '{:.2%}'.format\n",
            "}))"
        ]
    })
    
    # Save notebook structure to file
    notebook_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as nf:
        json.dump(notebook_content, nf, indent=1)
    print(f"  [OK] Wrote template notebook to {NOTEBOOK_PATH}")

if __name__ == "__main__":
    main()
