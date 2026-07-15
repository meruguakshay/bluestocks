import json
import os

folders = [".", "notebooks"]
for folder in folders:
    for file in os.listdir(folder):
        if file.endswith(".ipynb"):
            nb = os.path.join(folder, file)
            print("="*40)
            print("Searching notebook:", nb)
            with open(nb, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print("Error loading:", e)
                    continue
                cells = data.get("cells", [])
                for idx, cell in enumerate(cells):
                    source = "".join(cell.get("source", []))
                    if "roce" in source.lower() or "sector-relative" in source.lower() or "financials" in source.lower():
                        print(f"Cell {idx} ({cell.get('cell_type')}):")
                        lines = source.split("\n")
                        for l in lines[:5]:
                            print("  ", l)
                        if len(lines) > 5:
                            print("   ...")
