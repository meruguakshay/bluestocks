import json

nb_path = r"c:\Users\user\OneDrive\Desktop\AKshay\project\notebooks\EDA_Analysis.ipynb"
output_path = r"c:\Users\user\OneDrive\Desktop\AKshay\project\scratch\notebook_cells.txt"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

with open(output_path, "w", encoding="utf-8") as out:
    for idx, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = "".join(cell.get('source', []))
            if any(term in source for term in ['df_demographics', 'age_group', 'city_tier', 'gender', 'state_dist', 'chart9']):
                out.write(f"=== CELL {idx} ===\n")
                out.write(source)
                out.write("\n\n" + "="*80 + "\n\n")

print(f"Done. Output saved to {output_path}")
