import re

with open("scratch/pdf_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Let's search for section "22. KPI Definitions" and "23. Data Quality" or page headers
kpi_section = ""
dq_section = ""

# Find where "22" or "KPI Definitions" starts
m_kpi = re.search(r"22\s+KPI Definitions & Business Logic", text)
m_dq = re.search(r"23\s+Data Quality & Validation Rules", text)
m_api = re.search(r"24\s+API &", text)

with open("scratch/kpi_definitions.txt", "w", encoding="utf-8") as out:
    if m_kpi:
        start = m_kpi.start()
        end = m_dq.start() if m_dq else len(text)
        out.write("============================================================\n")
        out.write("22. KPI DEFINITIONS & BUSINESS LOGIC\n")
        out.write("============================================================\n")
        out.write(text[start:end])
        out.write("\n\n")
        
    if m_dq:
        start = m_dq.start()
        end = m_api.start() if m_api else len(text)
        out.write("============================================================\n")
        out.write("23. DATA QUALITY & VALIDATION RULES\n")
        out.write("============================================================\n")
        out.write(text[start:end])
        out.write("\n\n")

print("Saved definitions to scratch/kpi_definitions.txt")
