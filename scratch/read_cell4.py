import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOK_PATH = os.path.join(BASE_DIR, "notebooks", "EDA_Analysis.ipynb")

def main():
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cell = nb['cells'][4]
    print("".join(cell['source']))

if __name__ == "__main__":
    main()
