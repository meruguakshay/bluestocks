import pandas as pd
import numpy as np
import os

RAW_DIR = r"C:\Users\user\OneDrive\Desktop\project\data\raw"
os.makedirs(RAW_DIR, exist_ok=True)

print("Generating mock transactions and performance files with anomalies...")

# 1. investor_transactions.csv
# Columns: transaction_id, investor_id, scheme_code, date, transaction_type, amount, kyc_status
# We'll use scheme codes from fund_master
try:
    fund_master = pd.read_csv(os.path.join(RAW_DIR, "fund_master.csv"))
    scheme_codes = fund_master["scheme_code"].unique().tolist()
except Exception:
    scheme_codes = [125497, 119551, 120503, 118632, 119092, 120841]

np.random.seed(100)
num_transactions = 150

tx_ids = list(range(1001, 1001 + num_transactions))
investor_ids = np.random.choice([101, 102, 103, 104, 105, 106, 107, 108], size=num_transactions)
codes = np.random.choice(scheme_codes, size=num_transactions)

# Generate diverse date formats and some invalid/empty dates
dates = []
date_choices = pd.date_range(start="2025-01-01", end="2026-06-15", freq="D")
for i in range(num_transactions):
    dt = pd.Timestamp(np.random.choice(date_choices))
    fmt_choice = np.random.choice([1, 2, 3, 4])
    if fmt_choice == 1:
        dates.append(dt.strftime("%Y-%m-%d"))  # Standard
    elif fmt_choice == 2:
        dates.append(dt.strftime("%d-%m-%Y"))  # Indian style
    elif fmt_choice == 3:
        dates.append(dt.strftime("%Y/%m/%d"))  # Slash separated
    else:
        dates.append(dt.strftime("%d/%m/%Y"))  # Indian slash

# Generate transaction types with casing anomalies
tx_types = np.random.choice(
    ["SIP", "sip", "Sip", "Lumpsum", "lumpsum", "Redemption", "redemption", "REDEMPTION", "invalid_type"],
    size=num_transactions,
    p=[0.4, 0.1, 0.05, 0.2, 0.05, 0.15, 0.02, 0.02, 0.01]
)

# Generate amounts with negative/zero/null anomalies
amounts = np.random.uniform(500, 100000, size=num_transactions)
amounts = np.round(amounts, 2)
# Introduce anomalies
for i in range(5):
    amounts[np.random.randint(0, num_transactions)] = -5000.00
for i in range(3):
    amounts[np.random.randint(0, num_transactions)] = 0.00

# Generate KYC status with anomalies
kyc_statuses = np.random.choice(
    ["Verified", "verified", "VERIFIED", "Pending", "pending", "Failed", "failed", "Y", "N", "Yes", "No", None],
    size=num_transactions,
    p=[0.5, 0.05, 0.05, 0.15, 0.05, 0.05, 0.05, 0.03, 0.02, 0.02, 0.02, 0.01]
)

# Generate states for transactions
states = np.random.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat", "West Bengal"], size=num_transactions)

tx_df = pd.DataFrame({
    "transaction_id": tx_ids,
    "investor_id": investor_ids,
    "scheme_code": codes,
    "date": dates,
    "transaction_type": tx_types,
    "amount": amounts,
    "kyc_status": kyc_statuses,
    "state": states
})

# Save raw file
tx_df.to_csv(os.path.join(RAW_DIR, "investor_transactions.csv"), index=False)
print(f"Generated raw investor_transactions.csv with {len(tx_df)} rows.")

# 2. scheme_performance.csv
# Columns: scheme_code, return_1yr, return_3yr, return_5yr, expense_ratio
performance_records = []
for code in scheme_codes:
    ret_1 = round(np.random.uniform(-10, 45), 2)
    ret_3 = round(np.random.uniform(5, 30), 2)
    ret_5 = round(np.random.uniform(8, 25), 2)
    exp = round(np.random.uniform(0.001, 0.03), 4) # Decimal format, e.g. 0.001 to 0.03 (0.1% to 3.0%)
    
    performance_records.append({
        "scheme_code": code,
        "return_1yr": ret_1,
        "return_3yr": ret_3,
        "return_5yr": ret_5,
        "expense_ratio": exp
    })

perf_df = pd.DataFrame(performance_records).astype(object)

# Introduce anomalies (strings, extreme returns, out of bounds expense ratios)
# 1. Non-numeric return value
perf_df.loc[0, "return_1yr"] = "15.4%"
perf_df.loc[1, "return_3yr"] = "N/A"
perf_df.loc[2, "return_5yr"] = "null"

# 2. Extreme returns (anomaly flag check)
perf_df.loc[3, "return_1yr"] = 120.0  # Anomaly return (> 100%)
perf_df.loc[4, "return_3yr"] = -60.0  # Anomaly return (< -50%)

# 3. Expense ratio out of bounds (should be 0.1% - 2.5%, which is 0.001 - 0.025)
perf_df.loc[0, "expense_ratio"] = 0.0005  # 0.05% (too low)
perf_df.loc[1, "expense_ratio"] = 0.0350  # 3.5% (too high)
perf_df.loc[2, "expense_ratio"] = "1.8%"   # String format

perf_df.to_csv(os.path.join(RAW_DIR, "scheme_performance.csv"), index=False)
print(f"Generated raw scheme_performance.csv with {len(perf_df)} rows.")
