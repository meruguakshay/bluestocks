import pandas as pd
import os

files = {
    "financial_ratios_drive.xlsx": "financial_ratios_drive.xlsx",
    "market_cap_drive.xlsx": "market_cap_drive.xlsx",
    "peer_groups_drive.xlsx": "peer_groups_drive.xlsx",
    "sectors_drive.xlsx": "sectors_drive.xlsx",
    "stock_prices_drive.xlsx": "stock_prices_drive.xlsx"
}

for name, filename in files.items():
    path = os.path.join("data/raw", filename)
    if os.path.exists(path):
        try:
            df = pd.read_excel(path)
            print("=" * 60)
            print(f"File: {filename}")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("Head:")
            print(df.head(2))
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    else:
        print(f"File not found: {path}")
