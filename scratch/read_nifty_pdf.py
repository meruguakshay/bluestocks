import pypdf

reader = pypdf.PdfReader("data/raw/Nifty100_Project_Document_FINAL.pdf")
print("Total Pages:", len(reader.pages))

with open("scratch/pdf_text.txt", "w", encoding="utf-8") as out:
    for idx, page in enumerate(reader.pages):
        out.write(f"\n=================== PAGE {idx+1} ===================\n")
        out.write(page.extract_text() or "")
print("Saved all pages text to scratch/pdf_text.txt")
