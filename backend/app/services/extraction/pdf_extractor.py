import pdfplumber
from pathlib import Path


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract plain text from a PDF, concatenating all pages."""
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                pages.append(text.strip())
    return "\n\n".join(pages)
