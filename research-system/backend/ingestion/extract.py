import fitz  # PyMuPDF
from pathlib import Path


def extract_text_from_pdf(path: Path) -> str:
    """Extract full text from a PDF file. Returns empty string if extraction fails."""
    try:
        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        doc.close()
        # Strip null bytes — PostgreSQL UTF8 rejects them
        return "\n".join(pages).replace("\x00", "")
    except Exception:
        return ""


def extract_metadata_from_pdf(path: Path) -> dict:
    """Extract title, author, creation date from PDF metadata. Returns empty dict on failure."""
    try:
        doc = fitz.open(str(path))
        meta = doc.metadata
        doc.close()
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "creation_date": meta.get("creationDate", ""),
        }
    except Exception:
        return {"title": "", "author": "", "creation_date": ""}
