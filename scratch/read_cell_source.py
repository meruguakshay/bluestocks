import json
import os

nb_path = r"c:\Users\user\OneDrive\Desktop\AKshay\project\notebooks\EDA_Analysis.ipynb"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell.get('source', []))
        if 'chart5' in source or 'chart6' in source or 'chart9' in source:
            print(f"=== CELL {idx} ===")
            print(source)
            print("\n" + "="*50 + "\n")
