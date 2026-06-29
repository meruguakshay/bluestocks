import os
import pandas as pd

RAW_DIR = r"c:\Users\user\OneDrive\Desktop\AKshay\project\data\raw"
PROCESSED_DIR = r"c:\Users\user\OneDrive\Desktop\AKshay\project\data\processed"

def inspect_dir(d):
    print(f"=== Directory: {d} ===")
    for f in os.listdir(d):
        if f.endswith('.csv'):
            path = os.path.join(d, f)
            try:
                df = pd.read_csv(path)
                print(f"File: {f} | Rows: {len(df)} | Cols: {list(df.columns)}")
                if 'scheme_code' in df.columns:
                    print(f"  Unique scheme_codes: {df['scheme_code'].nunique()}")
                if 'scheme_name' in df.columns:
                    print(f"  Unique scheme_names: {df['scheme_name'].nunique()}")
            except Exception as e:
                print(f"File: {f} | Error: {e}")
            print("-" * 50)

inspect_dir(RAW_DIR)
inspect_dir(PROCESSED_DIR)
