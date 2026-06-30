import os

def search_files():
    search_dirs = [
        r"c:\Users\user\OneDrive\Desktop\AKshay\project",
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads")
    ]
    
    print("Searching for .pbix files...")
    found_pbix = []
    found_pdf = []
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            # Avoid traversing git or cache folders
            if ".git" in root or ".venv" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".pbix"):
                    found_pbix.append(os.path.join(root, f))
                elif f.lower() == "dashboard.pdf" or (f.endswith(".pdf") and "dashboard" in f.lower()):
                    found_pdf.append(os.path.join(root, f))
                    
    print("\n--- PBIX FILES FOUND ---")
    for f in found_pbix:
        print(f)
        
    print("\n--- PDF FILES FOUND ---")
    for f in found_pdf:
        print(f)

if __name__ == "__main__":
    search_files()
