import os
import nbformat
from nbclient import NotebookClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOK_PATH = os.path.join(BASE_DIR, "notebooks", "Performance_Analytics.ipynb")

def main():
    print(f"Loading notebook from {NOTEBOOK_PATH}...")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
        
    print("Executing notebook cells...")
    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    client.execute()
    
    print(f"Saving executed notebook back to {NOTEBOOK_PATH}...")
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
        
    print("Execution complete!")

if __name__ == "__main__":
    main()
