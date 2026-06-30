import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def verify():
    print("=" * 60)
    print("VERIFYING GENERATED DELIVERABLES")
    print("=" * 60)
    
    files = {
        "alpha_beta.csv": os.path.join(BASE_DIR, "alpha_beta.csv"),
        "fund_scorecard.csv": os.path.join(BASE_DIR, "fund_scorecard.csv"),
        "benchmark_comparison_chart.png": os.path.join(BASE_DIR, "benchmark_comparison_chart.png"),
        "reports/charts/benchmark_comparison_chart.png": os.path.join(BASE_DIR, "reports", "charts", "benchmark_comparison_chart.png"),
        "notebooks/Performance_Analytics.ipynb": os.path.join(BASE_DIR, "notebooks", "Performance_Analytics.ipynb")
    }
    
    all_ok = True
    for name, path in files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"[OK] File: {name:<45} | Size: {size:<10} bytes")
            if name.endswith('.csv'):
                df = pd.read_csv(path)
                print(f"     Rows: {len(df)} | Columns: {list(df.columns)}")
                if len(df) != 40:
                    print(f"     [WARN] Expected 40 rows, got {len(df)}")
                    all_ok = False
        else:
            print(f"[FAIL] File not found: {name}")
            all_ok = False
            
    print("-" * 60)
    if all_ok:
        print("Verification SUCCESS: All deliverables are present and correct.")
    else:
        print("Verification FAILURE: Some deliverables are missing or have errors.")
    print("=" * 60)

if __name__ == "__main__":
    verify()
