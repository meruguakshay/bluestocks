import os
import glob

def check_paths():
    search_paths = [
        r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
        r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
        r"C:\Program Files\WindowsApps\**\PBIDesktop.exe",
    ]
    
    found = []
    # Check fixed paths first
    for p in search_paths[:2]:
        if os.path.exists(p):
            found.append(p)
            
    # Check store path
    try:
        store_matches = glob.glob(r"C:\Program Files\WindowsApps\*PowerBIDesktop*")
        for match in store_matches:
            exe_path = os.path.join(match, "bin", "PBIDesktop.exe")
            if os.path.exists(exe_path):
                found.append(exe_path)
            # also search recursively inside the folder
            for root, dirs, files in os.walk(match):
                if "PBIDesktop.exe" in files:
                    found.append(os.path.join(root, "PBIDesktop.exe"))
    except Exception as e:
        print(f"Error searching WindowsApps: {e}")
        
    # Search Start Menu shortcuts
    start_menu_paths = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
    ]
    
    shortcuts = []
    for sm in start_menu_paths:
        if os.path.exists(sm):
            for root, dirs, files in os.walk(sm):
                for f in files:
                    if "power bi" in f.lower() or "pbi" in f.lower():
                        shortcuts.append(os.path.join(root, f))
                        
    print("Found Executables:")
    for f in found:
        print("-", f)
        
    print("\nFound Shortcuts:")
    for s in shortcuts:
        print("-", s)

if __name__ == "__main__":
    check_paths()
