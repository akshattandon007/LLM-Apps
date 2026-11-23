"""Fetch drug label data from the OpenFDA API.

OpenFDA Drug Label API is free, no API key needed for basic queries.
API: https://open.fda.gov/apis/drug/label/
"""

import json
import time
import requests
from pathlib import Path
from typing import Optional

OPENFDA_BASE = "https://api.fda.gov/drug/label.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Fields we extract from FDA drug labels
USEFUL_FIELDS = [
    "openfda.brand_name",
    "openfda.generic_name",
    "openfda.route",
    "openfda.product_type",
    "openfda.substance_name",
    "openfda.manufacturer_name",
    "purpose",
    "indications_and_usage",
    "dosage_and_administration",
    "contraindications",
    "warnings",
    "adverse_reactions",
    "drug_interactions",
    "pregnancy_or_breast_feeding",
    "active_ingredient",
    "inactive_ingredient",
    "questions",
    "storage_and_handling",
]


def _extract_field(result: dict, field: str) -> Optional[str]:
    """Extract a field from an FDA API result, handling arrays."""
    keys = field.split(".")
    val = result
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return None
    if isinstance(val, list):
        return " ".join(str(v) for v in val if v)
    return str(val) if val else None


def fetch_drug_labels(limit: int = 200, skip: int = 0) -> list[dict]:
    """Fetch drug labels from OpenFDA, returning structured records.

    Args:
        limit: Number of results to fetch (max 100 per API call, but we paginate).
        skip: Number of results to skip.

    Returns:
        List of dicts with extracted label info.
    """
    records = []
    page_size = min(limit, 100)
    current_skip = skip

    while len(records) < limit:
        params = {
            "limit": page_size,
            "skip": current_skip,
        }
        try:
            resp = requests.get(OPENFDA_BASE, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[WARN] OpenFDA fetch error at skip={current_skip}: {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for result in results:
            record = {}
            for field in USEFUL_FIELDS:
                val = _extract_field(result, field)
                if val:
                    record[field] = val
            records.append(record)

        print(f"  Fetched {len(results)} labels (total: {len(records)})")
        current_skip += len(results)

        if len(results) < page_size:
            break  # no more results

        time.sleep(0.35)  # rate limit courtesy

    return records[:limit]


def save_labels(records: list[dict], path: Optional[Path] = None) -> Path:
    """Save fetched drug labels to a JSON file."""
    if path is None:
        path = DATA_DIR / "drug_labels.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved {len(records)} drug labels to {path}")
    return path


def load_labels(path: Optional[Path] = None) -> list[dict]:
    """Load drug labels from a JSON file."""
    if path is None:
        path = DATA_DIR / "drug_labels.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def prepare_chunks(records: list[dict], chunk_size: int = 500) -> list[dict]:
    """Split drug labels into text chunks for embedding and retrieval.

    Each drug label is split into field-level chunks so queries about
    specific aspects (e.g. side effects, dosage) retrieve the right section.
    """
    chunks = []
    for idx, rec in enumerate(records):
        brand = rec.get("openfda.brand_name", rec.get("openfda.generic_name", f"Drug-{idx}"))
        generic = rec.get("openfda.generic_name", "")
        drug_id = f"{brand} {generic}".strip()

        for field in USEFUL_FIELDS:
            text = rec.get(field)
            if not text or len(text) < 10:
                continue
            # Split long fields into chunks
            words = text.split()
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)
                if len(chunk_text) < 20:
                    continue

                # Friendly field name for display
                field_label = field.replace("openfda.", "").replace("_", " ").title()
                if field.startswith("openfda."):
                    field_label = "Meta: " + field_label

                chunks.append({
                    "drug_id": drug_id,
                    "drug_name": brand,
                    "field": field,
                    "field_label": field_label,
                    "text": chunk_text,
                    "source": f"FDA Label — {brand} — {field_label}",
                })
    return chunks
