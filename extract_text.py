from PyPDF2 import PdfReader

def extract_pdf_text(file_path):
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    return text

# Save extracted data
pdf_text = extract_pdf_text("business.pdf")
with open("data.txt", "w", encoding="utf-8") as f:
    f.write(pdf_text)