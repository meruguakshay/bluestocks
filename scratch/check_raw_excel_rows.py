import pandas as pd

# Load files using the same header logic as loader.py
bs_df = pd.read_excel("data/raw/balancesheet.xlsx", header=1)
pnl_df = pd.read_excel("data/raw/profitandloss.xlsx", header=1)

for c_id in ["BEL", "HAL", "LT"]:
    print("="*50)
    print("Company ID:", c_id)
    print("Raw Balance Sheet:")
    print(bs_df[bs_df["company_id"] == c_id].to_string(index=False))
    print("\nRaw Profit & Loss:")
    print(pnl_df[pnl_df["company_id"] == c_id].to_string(index=False))

