import re

with open("scratch/pdf_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

keywords = [
    r"Ratio Engine", r"ratios\.py", r"report\.py", r"dashboard\.py", r"api\.py",
    r"D08", r"D09", r"D10", r"D11", r"D12", r"D13", r"D14",
    r"Day 8", r"Day 9", r"Day 10", r"Day 11", r"Day 12", r"Day 13", r"Day 14",
    r"Acceptance Criteria", r"Deliverables"
]

with open("scratch/search_results.txt", "w", encoding="utf-8") as out:
    for kw in keywords:
        matches = list(re.finditer(kw, text, re.IGNORECASE))
        out.write(f"\n============================================================\n")
        out.write(f"KEYWORD: '{kw}' matched {len(matches)} times\n")
        out.write(f"============================================================\n")
        for idx, m in enumerate(matches):
            start = max(0, m.start() - 300)
            end = min(len(text), m.end() + 300)
            out.write(f"\n--- Match {idx+1} (Position {m.start()}) ---\n")
            out.write(text[start:end].strip() + "\n")

print("Saved search results to scratch/search_results.txt")
