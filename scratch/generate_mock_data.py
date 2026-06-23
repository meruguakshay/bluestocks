import pandas as pd
import numpy as np
import os

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

print("Generating mock mutual fund datasets...")

# 1. fund_master.csv
# We include the HDFC Top 100 Direct (125497) and 5 Bluechip schemes from the prompt
schemes = [
    {"scheme_code": 125497, "fund_house": "HDFC Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
    {"scheme_code": 119551, "fund_house": "SBI Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
    {"scheme_code": 120503, "fund_house": "ICICI Prudential Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
    {"scheme_code": 118632, "fund_house": "Nippon India Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
    {"scheme_code": 119092, "fund_house": "Axis Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
    {"scheme_code": 120841, "fund_house": "Kotak Mahindra Mutual Fund", "category": "Equity", "sub_category": "Large Cap", "risk_grade": "Very High"},
]

# Generate more mock schemes
fund_houses = ["HDFC Mutual Fund", "SBI Mutual Fund", "ICICI Prudential Mutual Fund", "Nippon India Mutual Fund", "Axis Mutual Fund", "Kotak Mahindra Mutual Fund"]
categories = ["Equity", "Debt", "Hybrid"]
sub_categories = ["Large Cap", "Mid Cap", "Small Cap", "Liquid", "Balanced"]
risk_grades = ["Low", "Moderate", "High", "Very High"]

np.random.seed(42)
extra_schemes = []
for i in range(20):
    code = int(np.random.randint(100000, 130000))
    # Avoid duplicate codes
    if code not in [s["scheme_code"] for s in schemes] and code not in [s["scheme_code"] for s in extra_schemes]:
        extra_schemes.append({
            "scheme_code": code,
            "fund_house": np.random.choice(fund_houses),
            "category": np.random.choice(categories),
            "sub_category": np.random.choice(sub_categories),
            "risk_grade": np.random.choice(risk_grades)
        })

fund_master_df = pd.DataFrame(schemes + extra_schemes)
# Introduce a few duplicate rows to check anomaly logic
fund_master_df = pd.concat([fund_master_df, fund_master_df.iloc[[2]]], ignore_index=True)
fund_master_df.to_csv(os.path.join(RAW_DIR, "fund_master.csv"), index=False)

# 2. nav_history.csv
nav_records = []
master_codes = fund_master_df["scheme_code"].unique()
# We want:
# - Most codes to match
# - Some codes in master missing in NAV history (e.g. new/inactive funds)
# - Some codes in NAV history missing in master (orphan codes)
codes_for_nav = list(master_codes[:-3]) + [999991, 999992] # 999991 and 999992 are orphans

dates = pd.date_range(end="2026-06-23", periods=10).strftime("%Y-%m-%d").tolist()

for code in codes_for_nav:
    base_nav = np.random.uniform(10, 500)
    for dt in dates:
        change = np.random.uniform(-0.02, 0.02)
        base_nav = base_nav * (1 + change)
        nav_records.append({
            "scheme_code": code,
            "date": dt,
            "nav": round(base_nav, 4)
        })

nav_history_df = pd.DataFrame(nav_records)
# Introduce a few nulls in NAV to check anomaly detection
nav_history_df.loc[5, "nav"] = np.nan
nav_history_df.to_csv(os.path.join(RAW_DIR, "nav_history.csv"), index=False)

# 3. portfolio_holdings.csv
holdings = []
for code in master_codes:
    holdings.append({
        "scheme_code": code,
        "company_name": "Reliance Industries",
        "isin": "INE002A01018",
        "weightage": 8.5,
        "sector": "Energy"
    })
    holdings.append({
        "scheme_code": code,
        "company_name": "HDFC Bank",
        "isin": "INE040A01034",
        "weightage": 7.2,
        "sector": "Financial Services"
    })
portfolio_holdings_df = pd.DataFrame(holdings)
portfolio_holdings_df.to_csv(os.path.join(RAW_DIR, "portfolio_holdings.csv"), index=False)

# 4. amc_details.csv
amc_data = []
for idx, name in enumerate(fund_houses):
    amc_data.append({
        "amc_id": idx + 1,
        "amc_name": name,
        "aum_crores": int(np.random.uniform(50000, 500000))
    })
amc_details_df = pd.DataFrame(amc_data)
amc_details_df.to_csv(os.path.join(RAW_DIR, "amc_details.csv"), index=False)

# 5. scheme_details.csv
scheme_details = []
for code in master_codes:
    scheme_details.append({
        "scheme_code": code,
        "isin": f"INF{code}D01012",
        "scheme_name": f"Scheme {code} Direct Growth"
    })
scheme_details_df = pd.DataFrame(scheme_details)
scheme_details_df.to_csv(os.path.join(RAW_DIR, "scheme_details.csv"), index=False)

# 6. returns_data.csv
returns_data = []
for code in master_codes:
    returns_data.append({
        "scheme_code": code,
        "return_1yr": round(np.random.uniform(5, 30), 2),
        "return_3yr": round(np.random.uniform(8, 25), 2),
        "return_5yr": round(np.random.uniform(10, 20), 2)
    })
returns_df = pd.DataFrame(returns_data)
returns_df.to_csv(os.path.join(RAW_DIR, "returns_data.csv"), index=False)

# 7. benchmark_data.csv
benchmarks = [
    {"benchmark_id": 1, "benchmark_name": "Nifty 50 TRI", "daily_return": 0.0012},
    {"benchmark_id": 2, "benchmark_name": "Nifty Large Midcap 250 TRI", "daily_return": 0.0015},
    {"benchmark_id": 3, "benchmark_name": "Nifty Midcap 150 TRI", "daily_return": 0.0018}
]
benchmark_df = pd.DataFrame(benchmarks)
benchmark_df.to_csv(os.path.join(RAW_DIR, "benchmark_data.csv"), index=False)

# 8. risk_metrics.csv
risk_metrics = []
for code in master_codes:
    risk_metrics.append({
        "scheme_code": code,
        "beta": round(np.random.uniform(0.7, 1.3), 2),
        "sharpe_ratio": round(np.random.uniform(1.0, 3.0), 2),
        "alpha": round(np.random.uniform(-2, 5), 2),
        "standard_deviation": round(np.random.uniform(10, 22), 2)
    })
risk_metrics_df = pd.DataFrame(risk_metrics)
risk_metrics_df.to_csv(os.path.join(RAW_DIR, "risk_metrics.csv"), index=False)

# 9. sip_data.csv
sip_data = []
for code in master_codes:
    sip_data.append({
        "scheme_code": code,
        "sip_return_1yr": round(np.random.uniform(6, 28), 2),
        "sip_return_3yr": round(np.random.uniform(9, 24), 2)
    })
sip_df = pd.DataFrame(sip_data)
sip_df.to_csv(os.path.join(RAW_DIR, "sip_data.csv"), index=False)

# 10. investor_data.csv
investor_data = []
names = ["Amit Sharma", "Priya Patel", "Rohan Das", "Sneha Reddy", "Vikram Singh"]
for idx, name in enumerate(names):
    investor_data.append({
        "investor_id": idx + 101,
        "name": name,
        "scheme_code": np.random.choice(master_codes),
        "investment_amount": int(np.random.choice([10000, 25000, 50000, 100000]))
    })
investor_df = pd.DataFrame(investor_data)
investor_df.to_csv(os.path.join(RAW_DIR, "investor_data.csv"), index=False)

print("Successfully generated all 10 CSV datasets in data/raw/.")
