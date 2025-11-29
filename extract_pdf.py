import pdfplumber
import sys
import os

# Adjust path if running from backend or root
# Assuming running from project root
pdf_path = os.path.abspath("docs/especificacion-sindicacion.pdf")
output_path = os.path.abspath("docs/especificacion-sindicacion.txt")

print(f"Reading from: {pdf_path}")

try:
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i+1}...")
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Successfully extracted {len(text)} characters to {output_path}")
except Exception as e:
    print(f"Error: {e}")
