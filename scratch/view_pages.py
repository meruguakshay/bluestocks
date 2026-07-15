with open("scratch/pdf_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

pages = text.split("=================== PAGE ")
spec_pages = []

for p in pages:
    if p.strip() == "":
        continue
    # Extract page number
    lines = p.split("\n")
    page_num = lines[0].split(" =")[0].strip()
    try:
        pn = int(page_num)
        # We want pages 30 to 43 (or up to the end)
        if 20 <= pn <= 43:
            spec_pages.append(f"\n=================== PAGE {pn} ===================\n" + "\n".join(lines[1:]))
    except ValueError:
        pass

with open("scratch/spec_pages.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(spec_pages))

print("Saved selected specification pages to scratch/spec_pages.txt")
