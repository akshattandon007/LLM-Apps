"""
File and document utilities for ClaimCounsel.
Handles reading policy documents, extracting text from PDFs, and saving outputs.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

from config import CLAIMS_DIR, OUTPUT_DIR, POLICIES_DIR, DOCUMENTS_DIR


def ensure_dirs():
    """Create all data directories if they don't exist."""
    for d in [CLAIMS_DIR, OUTPUT_DIR, POLICIES_DIR, DOCUMENTS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)


def read_text_file(filepath: str) -> str:
    """Read a plain text file and return its contents."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(filepath: str, content: str):
    """Write content to a text file, creating parent dirs as needed."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def read_json_file(filepath: str) -> dict:
    """Read and parse a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(filepath: str, data: dict):
    """Write a dict as pretty-printed JSON."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_pdf_text(filepath: str) -> Optional[str]:
    """
    Extract text from a PDF file using PyPDF2.
    Returns None if extraction fails or the file isn't a valid PDF.
    """
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages) if pages else None
    except Exception as e:
        return None


def list_claim_files(directory: str) -> List[str]:
    """List all files in a claim directory, sorted by name."""
    path = Path(directory)
    if not path.exists():
        return []
    return sorted(
        [str(p) for p in path.iterdir() if p.is_file()],
    )


def read_all_texts(directory: str) -> Dict[str, str]:
    """
    Read all text/PDF files in a directory.
    Returns a dict of {filename: extracted_text}.
    """
    result = {}
    for filepath in list_claim_files(directory):
        name = os.path.basename(filepath)
        if filepath.lower().endswith(".pdf"):
            text = extract_pdf_text(filepath)
            if text:
                result[name] = text
        elif filepath.lower().endswith((".txt", ".md", ".csv", ".json")):
            try:
                result[name] = read_text_file(filepath)
            except Exception:
                pass
    return result