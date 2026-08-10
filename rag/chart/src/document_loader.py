"""Document loader: PDF ingestion with PyMuPDF, OCR fallback via tesserocr, metadata extraction."""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from src.models import DocumentType


# ---------- helpers ----------

_DATE_PATTERNS = [
    # "March 2023", "March 10, 2023"
    r"(?i)(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2},?\s+\d{4}",
    r"(?i)(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}",
    # 2023-03-15, 2023/03/15
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    # 03/15/2023, 03-15-2023
    r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",
]

_LAB_PATTERNS = [
    r"(?i)\b(hba1c|a1c|hemoglobin\s*a1c)\b",
    r"(?i)\b(ldl|hdl|total\s*cholesterol|cholesterol|triglycerides?|lipid)\b",
    r"(?i)\b(vitamin\s*d|vitamin\s*b12|ferritin|iron|tsh|t4|t3|glucose|creatinine|bun|egfr)\b",
    r"(?i)\b(wbc|rbc|hemoglobin|hematocrit|platelet|neutrophil|lymphocyte)\b",
    r"(?i)\b(potassium|sodium|calcium|magnesium|albumin|bilirubin|ast|alt|alp)\b",
]

_MED_PATTERNS = [
    r"(?i)\b(ibuprofen|aspirin|acetaminophen|paracetamol|naproxen|omeprazole|lisinopril|atorvastatin|metformin|amlodipine)\b",
    r"(?i)\b(levothyroxine|simvastatin|rosuvastatin|warfarin|apixaban|clopidogrel|furosemide|hydrochlorothiazide)\b",
    r"(?i)\b(albuterol|fluticasone|prednisone|amoxicillin|azithromycin|doxycycline|ciprofloxacin)\b",
    r"(?i)\b(tetanus|tdap|influenza|flu\s*shot|covid|pneumococcal|hpv|hepatitis)\b",
]

_VALUE_PATTERN = r"(\d+\.?\d*)\s*(mg/dL|ng/mL|pg/mL|mmol/L|%|g/dL|mEq/L|IU/L|U/L|mm3|cells/µL)"


def extract_dates(text: str) -> list[str]:
    dates: list[str] = []
    for pat in _DATE_PATTERNS:
        dates.extend(m.group(0) for m in re.finditer(pat, text))
    return dates


def extract_labs(text: str) -> list[str]:
    labs: set[str] = set()
    for pat in _LAB_PATTERNS:
        for m in re.finditer(pat, text):
            labs.add(m.group(0).lower().strip())
    return sorted(labs)


def extract_medications(text: str) -> list[str]:
    meds: set[str] = set()
    for pat in _MED_PATTERNS:
        for m in re.finditer(pat, text):
            meds.add(m.group(0).lower().strip())
    return sorted(meds)


def extract_values(text: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for m in re.finditer(_VALUE_PATTERN, text):
        results.append({"value": m.group(1), "unit": m.group(2)})
    return results


def classify_document_type(text: str, name: str = "") -> DocumentType:
    name_lower = name.lower()
    text_lower = text.lower()

    # Check by name first
    if any(kw in name_lower for kw in ["lab", "result", "blood", "panel", "lipid", "metabolic"]):
        return DocumentType.LAB_RESULT
    if any(kw in name_lower for kw in ["immunization", "vaccine", "vaccination", "shot"]):
        return DocumentType.IMMUNIZATION
    if any(kw in name_lower for kw in ["doctor", "note", "physical", "assessment", "progress"]):
        return DocumentType.DOCTOR_NOTE
    if any(kw in name_lower for kw in ["discharge", "summary", "hospital"]):
        return DocumentType.DISCHARGE_SUMMARY

    # Fall back to content
    if any(kw in text_lower for kw in ["lab result", "test result", "reference range", "lipid panel"]):
        return DocumentType.LAB_RESULT
    if any(kw in text_lower for kw in ["immunization", "vaccine", "vaccination", "tetanus"]):
        return DocumentType.IMMUNIZATION
    if any(kw in text_lower for kw in ["discharge", "hospital course", "admission"]):
        return DocumentType.DISCHARGE_SUMMARY
    if any(kw in text_lower for kw in ["physical exam", "assessment", "plan", "diagnosis"]):
        return DocumentType.DOCTOR_NOTE
    return DocumentType.OTHER


# ---------- PDF extraction ----------

def extract_text_with_pymupdf(path: str) -> str:
    """Extract text from PDF using PyMuPDF, preserving section headers."""
    doc = fitz.open(path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n\n".join(pages)


def extract_text_with_ocr(path: str) -> str:
    """Fallback OCR using tesserocr on each page image."""
    from PIL import Image
    import io
    from tesserocr import PyTessBaseAPI

    doc = fitz.open(path)
    pages = []
    api = PyTessBaseAPI()
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page at 300 DPI
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            api.SetImage(img)
            text = api.GetUTF8Text()
            if text.strip():
                pages.append(text)
    finally:
        api.End()
    doc.close()
    return "\n\n".join(pages)


def load_document(path: str) -> dict[str, Any]:
    """Load a document and return text + metadata.

    Returns:
        dict with keys: text, doc_type, doc_name, dates, medications, labs, values
    """
    path_obj = Path(path)
    name = path_obj.name
    ext = path_obj.suffix.lower()

    if ext in (".jpg", ".jpeg", ".png"):
        # Image-based OCR via tesserocr
        from PIL import Image
        from tesserocr import PyTessBaseAPI

        api = PyTessBaseAPI()
        try:
            api.SetImage(path)
            text = api.GetUTF8Text()
        finally:
            api.End()
    elif ext == ".pdf":
        text = extract_text_with_pymupdf(path)
        if len(text.strip()) < 50:
            # OCR fallback for scanned documents
            text = extract_text_with_ocr(path)
    elif ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    dates = extract_dates(text)
    labs = extract_labs(text)
    medications = extract_medications(text)
    values = extract_values(text)
    doc_type = classify_document_type(text, name)

    return {
        "text": text,
        "doc_type": doc_type,
        "doc_name": name,
        "dates": dates,
        "medications": medications,
        "labs": labs,
        "values": values,
    }