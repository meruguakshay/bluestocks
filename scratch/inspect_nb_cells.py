import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOK_PATH = os.path.join(BASE_DIR, "notebooks", "EDA_Analysis.ipynb")

def main():
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    for idx, cell in enumerate(nb['cells']):
        if cell.get('cell_type') == 'code':
            source = "".join(cell.get('source', []))
            if 'fact_performance' in source or 'expense_ratio' in source or 'risk_metrics' in source:
                print(f"=== Cell {idx} ===")
                print(source)
                print("-" * 50)

if __name__ == "__main__":
    main()
