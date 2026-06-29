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
        
    print(f"Notebook loaded. Number of cells: {len(nb['cells'])}")
    
    # Print first few cell contents or code summaries
    code_count = 0
    markdown_count = 0
    for idx, cell in enumerate(nb['cells']):
        cell_type = cell.get('cell_type')
        source = "".join(cell.get('source', []))
        
        if cell_type == 'markdown':
            markdown_count += 1
            if any(term in source.lower() for term in ['scheme', 'return', '40', 'data', 'cagr', 'performance']):
                print(f"Cell {idx} (Markdown): {source[:150]}...")
        elif cell_type == 'code':
            code_count += 1
            if any(term in source.lower() for term in ['scheme', 'return', '40', 'data', 'cagr', 'performance', 'read_csv']):
                print(f"Cell {idx} (Code) [Length: {len(source)}]: {source[:150]}...")
                
    print(f"Total markdown cells: {markdown_count}, Total code cells: {code_count}")

if __name__ == "__main__":
    main()
