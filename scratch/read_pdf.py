import os

try:
    import pypdf
    print("pypdf installed")
except ImportError:
    pypdf = None

try:
    import fitz # PyMuPDF
    print("fitz installed")
except ImportError:
    fitz = None

try:
    import pdfplumber
    print("pdfplumber installed")
except ImportError:
    pdfplumber = None

# If pypdf is installed, extract text
if pypdf:
    reader = pypdf.PdfReader("Dashboard.pdf")
    print("Number of pages:", len(reader.pages))
    for i, page in enumerate(reader.pages):
        print(f"--- Page {i+1} ---")
        print(page.extract_text()[:1000])
elif fitz:
    doc = fitz.open("Dashboard.pdf")
    print("Number of pages:", len(doc))
    for i, page in enumerate(doc):
        print(f"--- Page {i+1} ---")
        print(page.get_text()[:1000])
else:
    print("No PDF libraries found. Let's try installing pypdf...")
    import subprocess
    subprocess.run([".venv\\Scripts\\pip", "install", "pypdf"])
    import pypdf
    reader = pypdf.PdfReader("Dashboard.pdf")
    print("Number of pages:", len(reader.pages))
    for i, page in enumerate(reader.pages):
        print(f"--- Page {i+1} ---")
        print(page.extract_text()[:1000])
