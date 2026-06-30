import os
import shutil
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def copy_files():
    # Source paths
    pdf_src = os.path.join(BASE_DIR, "reports", "Dashboard.pdf")
    p1_src = os.path.join(BASE_DIR, "dashboard", "page1_industry_overview.png")
    p2_src = os.path.join(BASE_DIR, "dashboard", "page2_fund_performance.png")
    p3_src = os.path.join(BASE_DIR, "dashboard", "page3_investor_analytics.png")
    p4_src = os.path.join(BASE_DIR, "dashboard", "page4_sip_market_trends.png")
    
    # Destination paths in root
    pdf_dst = os.path.join(BASE_DIR, "Dashboard.pdf")
    p1_dst = os.path.join(BASE_DIR, "page1_industry_overview.png")
    p2_dst = os.path.join(BASE_DIR, "page2_fund_performance.png")
    p3_dst = os.path.join(BASE_DIR, "page3_investor_analytics.png")
    p4_dst = os.path.join(BASE_DIR, "page4_sip_market_trends.png")
    
    # Copy files
    shutil.copy2(pdf_src, pdf_dst)
    shutil.copy2(p1_src, p1_dst)
    shutil.copy2(p2_src, p2_dst)
    shutil.copy2(p3_src, p3_dst)
    shutil.copy2(p4_src, p4_dst)
    
    print("Successfully copied all deliverables to the project root!")
    print(f"- Copied {pdf_dst}")
    print(f"- Copied {p1_dst}")
    print(f"- Copied {p2_dst}")
    print(f"- Copied {p3_dst}")
    print(f"- Copied {p4_dst}")

def create_theme_file():
    # Power BI custom JSON theme definition
    theme = {
        "name": "Bluestock Color Theme",
        "dataColors": [
            "#0052CC", # Primary Blue
            "#0A2540", # Deep Navy
            "#0DCAF0", # Electric Cyan
            "#20C997", # Soft Teal
            "#FD7E14", # Vivid Orange
            "#FFC107", # Bright Amber
            "#6F42C1", # Royal Purple
            "#E83E8C"  # Deep Pink
        ],
        "background": "#FFFFFF",
        "foreground": "#1E293B",
        "tableAccent": "#0052CC",
        "visualStyles": {
            "*": {
                "*": {
                    "fontFamily": [{"value": "Arial"}],
                    "color": [{"value": "#1E293B"}]
                }
            },
            "page": {
                "*": {
                    "background": [
                        {
                            "color": {"solid": {"color": "#F4F6F9"}},
                            "transparency": 0
                        }
                    ]
                }
            }
        }
    }
    
    # Save theme to root and dashboard
    root_theme_path = os.path.join(BASE_DIR, "bluestock_theme.json")
    dash_theme_path = os.path.join(BASE_DIR, "dashboard", "bluestock_theme.json")
    
    for path in [root_theme_path, dash_theme_path]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(theme, f, indent=4)
        print(f"Created theme file: {path}")

if __name__ == "__main__":
    copy_files()
    create_theme_file()
