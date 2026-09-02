"""Scanner — Parse bank statements and email exports for transactions."""

import csv
import io
import re
from datetime import date, datetime
from typing import Optional

from src.merchant_db import resolve_merchant
from src.models import Charge, ScanResult


# Date format patterns commonly found in CSV exports
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d-%b-%Y",
    "%d %b %Y",
]


def _guess_date_format(date_str: str) -> Optional[str]:
    """Try common date formats against a date string."""
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(date_str.strip(), fmt)
            return fmt
        except ValueError:
            continue
    return None


def _parse_date(date_str: str) -> Optional[date]:
    """Parse a date string using common formats."""
    fmt = _guess_date_format(date_str)
    if fmt:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass

    # Try extracting date with regex for messy strings
    match = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})", date_str)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def _parse_amount(amount_str: str) -> Optional[float]:
    """Parse a dollar amount string to float."""
    cleaned = amount_str.strip()
    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[^\d.,\-]", "", cleaned)
    # Handle European format (1.234,56 -> 1234.56)
    if "," in cleaned and "." in cleaned:
        if cleaned.rindex(",") > cleaned.rindex("."):
            # European: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        # else already US format: 1,234.56 -> remove comma
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Could be European 1234,56 or US 1,234
        if re.search(r",\d{2}$", cleaned):
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return abs(float(cleaned))  # Use absolute value for debits
    except ValueError:
        return None


HEADER_PATTERNS = {
    "date": re.compile(r"date|posting.?date|transaction.?date|posted.?date", re.I),
    "description": re.compile(r"description|narrative|memo|details|merchant|payee|name", re.I),
    "amount": re.compile(r"amount|value|sum|debit|credit|charge", re.I),
    "debit": re.compile(r"debit|withdrawal|charge|payment.?out", re.I),
    "credit": re.compile(r"credit|deposit|payment.?in|refund", re.I),
}


def scan_statements(csv_path: str) -> ScanResult:
    """Parse a bank statement CSV file into Charge objects.

    Handles common CSV formats from major banks including:
    - Header rows with varying column names
    - Multiple date formats
    - Amounts with currency symbols and various number formats
    - Description/memo/merchant fields

    Supports two-column (description, amount) and multi-column formats.
    """
    result = ScanResult()

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except FileNotFoundError:
        result.errors.append(f"File not found: {csv_path}")
        return result
    except Exception as e:
        result.errors.append(f"Error reading file: {e}")
        return result

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        result.errors.append("Empty CSV file")
        return result

    # Detect header row and column mapping
    header_row_idx = None
    col_map = {"date": None, "description": None, "amount": None, "debit": None, "credit": None}

    for idx, row in enumerate(rows):
        if len(row) < 2:
            continue
        # Check if this row looks like a header
        for col_idx, cell in enumerate(row):
            cell_stripped = cell.strip()
            for key, pattern in HEADER_PATTERNS.items():
                if pattern.search(cell_stripped) and col_map[key] is None:
                    col_map[key] = col_idx
        # If we found at least description and something numeric, stop
        if col_map["description"] is not None and (col_map["amount"] is not None or col_map["debit"] is not None):
            header_row_idx = idx
            break

    data_rows = rows[header_row_idx + 1:] if header_row_idx is not None else rows

    for row in data_rows:
        if len(row) < 2:
            continue

        try:
            # Extract amount
            amount = None
            if col_map["amount"] is not None and col_map["amount"] < len(row):
                amount = _parse_amount(row[col_map["amount"]])
            elif col_map["debit"] is not None and col_map["debit"] < len(row):
                amount = _parse_amount(row[col_map["debit"]])
            elif col_map["credit"] is not None and col_map["credit"] < len(row):
                # Skip credits (income) — only interested in charges
                continue
            else:
                # Fallback: look for numeric values in the row
                for cell in row:
                    parsed = _parse_amount(cell)
                    if parsed is not None and parsed > 0:
                        amount = parsed
                        break

            if amount is None or amount <= 0:
                continue

            # Extract description
            description = ""
            if col_map["description"] is not None and col_map["description"] < len(row):
                description = row[col_map["description"]].strip()
            else:
                # Use the first non-date, non-amount column
                for i, cell in enumerate(row):
                    if i != col_map.get("date") and i != col_map.get("amount") and i != col_map.get("debit") and i != col_map.get("credit"):
                        description = cell.strip()
                        if description:
                            break

            if not description:
                continue

            # Extract date
            charge_date = None
            if col_map["date"] is not None and col_map["date"] < len(row):
                charge_date = _parse_date(row[col_map["date"]])
            if charge_date is None:
                charge_date = date.today()

            # Resolve merchant
            merchant_name, _ = resolve_merchant(description)

            charge = Charge(
                date=charge_date,
                description=description,
                amount=amount,
                merchant=merchant_name,
            )
            result.charges.append(charge)

        except (ValueError, IndexError, TypeError) as e:
            result.errors.append(f"Parse error on row: {row[:4]} — {e}")
            continue

    result.total_transactions = len(result.charges)
    return result


def scan_statement_text(text_content: str) -> ScanResult:
    """Parse statement text (CSV string) directly."""
    result = ScanResult()
    reader = csv.reader(io.StringIO(text_content))
    rows = list(reader)
    if not rows:
        result.errors.append("Empty CSV text")
        return result

    # Reuse the file scan logic — write to temp and read back
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(text_content)
        tmp_path = f.name

    result = scan_statements(tmp_path)
    import os
    os.unlink(tmp_path)
    return result