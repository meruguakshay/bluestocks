import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOK_PATH = os.path.join(BASE_DIR, "notebooks", "EDA_Analysis.ipynb")

def main():
    if not os.path.exists(NOTEBOOK_PATH):
        print("Notebook not found!")
        return
        
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    print("Searching notebook cells...")
    for idx, cell in enumerate(nb['cells']):
        cell_type = cell.get('cell_type')
        source = "".join(cell.get('source', []))
        
        for term in ['nifty', 'benchmark', 'alpha', 'beta', 'cagr', 'drawdown', 'scorecard']:
            if term in source.lower():
                print(f"Cell {idx} ({cell_type}) matches '{term}':")
                lines = source.split('\n')
                for line in lines:
                    if term in line.lower():
                        print(f"  Line: {line.strip()[:120]}")

if __name__ == "__main__":
    main()
