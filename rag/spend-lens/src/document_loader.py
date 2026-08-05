"""
src/document_loader.py
──────────────────────
Statement ingestion pipeline for SpendLens.

Parses bank/credit-card statements from PDFs (via pdfplumber) and CSVs
(via pandas) into a normalised transaction schema, then chunks them
into searchable LangChain Documents for embedding.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from langchain_core.documents import Document
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# ─── Normalised transaction schema ────────────────────────────────────────────


@dataclass
class Transaction:
    """Single financial transaction in normalised form."""

    date: str               # YYYY-MM-DD
    description: str         # Cleaned merchant / payee text
    amount: float            # Negative = debit, positive = credit
    category: str = "Uncategorised"
    source_file: str = ""
    raw_row: dict = field(default_factory=dict)

    def to_document_text(self) -> str:
        """Render transaction as a compact, searchable text snippet."""
        direction = "debit" if self.amount < 0 else "credit"
        return (
            f"Transaction: {self.description} | "
            f"Date: {self.date} | "
            f"Amount: ${abs(self.amount):.2f} ({direction}) | "
            f"Category: {self.category}"
        )

    def to_metadata(self) -> dict:
        return {
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "source_file": self.source_file,
            "month": self.date[:7],  # YYYY-MM for grouping
        }


# ─── PDF parser ───────────────────────────────────────────────────────────────


def _parse_amount(raw: str) -> float:
    """Robustly convert a dollar string to a float.

    Handles: '$1,234.56', '-$45.00', '(99.99)', '1,234.56'
    """
    if raw is None:
        return 0.0
    raw = str(raw).strip()
    # Remove $ signs and surrounding whitespace
    raw = raw.replace("$", "").replace(" ", "")
    # Parens = negative: "(99.99)" → -99.99
    if raw.startswith("(") and raw.endswith(")"):
        raw = f"-{raw[1:-1]}"
    raw = raw.replace(",", "")
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def _parse_date(raw: str) -> str:
    """Normalise a date string to YYYY-MM-DD. Returns empty string on failure."""
    if raw is None:
        return ""
    raw = str(raw).strip()

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%b %d, %Y",   # Jan 15, 2025
        "%B %d, %Y",   # January 15, 2025
        "%d %b %Y",    # 15 Jan 2025
        "%d %B %Y",    # 15 January 2025
        "%m-%d-%Y",
        "%m-%d-%y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _clean_description(raw: str) -> str:
    """Clean a transaction description: strip noise, normalise whitespace."""
    if raw is None:
        return ""
    raw = str(raw).strip()
    # Collapse multiple spaces
    raw = re.sub(r"\s+", " ", raw)
    # Strip common prefix noise
    raw = re.sub(r"^(DEBIT CARD PURCHASE|ACH DEBIT|POS|PURCHASE)\s+", "", raw, flags=re.I)
    return raw.strip()


# Known category keywords for auto-classification
CATEGORY_KEYWORDS = {
    "Dining": [
        r"restaurant", r"cafe", r"coffee", r"starbucks", r"dunkin", r"mcdonald",
        r"burger", r"pizza", r"doordash", r"ubereats", r"grubhub", r"diner",
        r"bistro", r"tavern", r"bar\b", r"pub\b", r"chipotle", r"wendy",
        r"taco\s?bell", r"subway", r"panera", r"sushi", r"thai",
    ],
    "Groceries": [
        r"grocery", r"supermarket", r"whole\s?foods", r"trader\s?joes",
        r"kroger", r"safeway", r"publix", r"aldi", r"costco", r"sams\s?club",
        r"walmart", r"target", r"market", r"fresh",
    ],
    "Transport": [
        r"uber", r"lyft", r"gas\s?station", r"shell\b", r"bp\b", r"exxon",
        r"chevron", r"fuel", r"parking", r"toll", r"transit", r"metro",
        r"amtrak", r"airline", r"united\s?air", r"delta\s?air", r"southwest",
    ],
    "Shopping": [
        r"amazon", r"ebay", r"etsy", r"shop", r"store", r"retail",
        r"nike", r"adidas", r"zara", r"h&m", r"uniqlo", r"gap\b",
        r"apple\s?(store|\.com|pay)?", r"best\s?buy",
    ],
    "Entertainment": [
        r"netflix", r"spotify", r"hulu", r"disney\+", r"hbo", r"prime\s?video",
        r"youtube", r"cinema", r"theatre", r"theater", r"concert",
        r"ticketmaster", r"stubhub", r"game", r"steam",
    ],
    "Utilities": [
        r"electric", r"gas\s?(bill|co)", r"water", r"internet", r"comcast",
        r"xfinity", r"verizon", r"at&t", r"t-mobile", r"spectrum",
        r"utility", r"sewer", r"trash",
    ],
    "Housing": [
        r"rent", r"mortgage", r"hoa", r"property\s?(tax|mgmt)", r"maintenance",
    ],
    "Healthcare": [
        r"pharmacy", r"cvs", r"walgreens", r"doctor", r"hospital",
        r"clinic", r"dental", r"vision", r"medical", r"prescription",
        r"insurance.*(?:health|medical|dental)",
    ],
    "Subscriptions": [
        r"subscription", r"monthly", r"membership", r"recurring",
        r"apple\.com/bill", r"google\s?.*subscription", r"microsoft\s?\d{2}",
        r"patreon", r"onlyfans", r"substack",
    ],
    "Income": [
        r"payroll", r"direct\s?deposit", r"salary", r"paycheck",
        r"deposit\b", r"payment\s?received", r"venmo.*(?:received|in)",
        r"zelle.*(?:received|in)",
    ],
    "Transfer": [
        r"transfer", r"zelle\s?(?:sent|out|payment)", r"venmo\s?(?:sent|out|payment)",
        r"cash\s?app", r"withdrawal", r"atm",
    ],
}


def _guess_category(description: str) -> str:
    """Auto-guess a category from the transaction description."""
    desc_lower = description.lower()
    for category, patterns in CATEGORY_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, desc_lower):
                return category
    return "Uncategorised"


def parse_pdf_statement(file_path: str | Path) -> List[Transaction]:
    """Parse a PDF bank/credit-card statement into normalised transactions.

    Uses pdfplumber to extract tables from each page. Falls back to
    raw text extraction if no tables are found.
    """
    import pdfplumber

    transactions: List[Transaction] = []
    file_path = Path(file_path)
    source = file_path.name

    console.print(f"[cyan]📄 Parsing PDF: {source}[/cyan]")

    with pdfplumber.open(str(file_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Try table extraction first (most bank statements use tables)
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    transactions.extend(
                        _extract_transactions_from_table(table, source, page_num)
                    )
            else:
                # Fall back to raw text
                text = page.extract_text()
                if text:
                    console.print(
                        f"  [yellow]⚠  Page {page_num}: no tables found, "
                        f"trying text extraction...[/yellow]"
                    )
                    transactions.extend(
                        _extract_transactions_from_text(text, source, page_num)
                    )

    console.print(
        f"  [green]✔[/green] Extracted {len(transactions)} transactions "
        f"from {source}"
    )
    return transactions


def _extract_transactions_from_table(
    table: list[list[str | None]], source: str, page_num: int,
) -> List[Transaction]:
    """Extract transactions from a pdfplumber table (list of rows)."""

    # Detect header row — look for date/description/amount keywords
    header_idx = -1
    for i, row in enumerate(table):
        if row is None:
            continue
        row_text = " ".join(str(c).lower() for c in row if c)
        if any(kw in row_text for kw in ["date", "transaction", "description", "amount"]):
            header_idx = i
            break

    if header_idx < 0:
        # No header found — try to parse all rows
        return _extract_rows_without_header(table, source, page_num)

    # Map columns by header position
    headers = [str(c).lower().strip() if c else "" for c in table[header_idx]]
    date_col = next(
        (i for i, h in enumerate(headers) if "date" in h), 0
    )
    desc_col = next(
        (i for i, h in enumerate(headers) if any(k in h for k in ["desc", "trans", "payee", "merchant", "name"])), 1
    )
    amount_col = next(
        (i for i, h in enumerate(headers) if "amount" in h), -1
    )
    if amount_col < 0:
        amount_col = next(
            (i for i, h in enumerate(headers) if any(k in h for k in ["debit", "credit", "withdrawal", "deposit"])), -1
        )
    if amount_col < 0:
        amount_col = 2  # fallback

    transactions = []
    for row in table[header_idx + 1:]:
        if row is None or all(c is None or str(c).strip() == "" for c in row):
            continue
        try:
            raw_date = str(row[date_col]).strip() if date_col < len(row) and row[date_col] else ""
            raw_desc = str(row[desc_col]).strip() if desc_col < len(row) and row[desc_col] else ""
            raw_amount = str(row[amount_col]).strip() if amount_col < len(row) and row[amount_col] else "0"

            date = _parse_date(raw_date)
            if not date:
                continue  # skip rows without valid dates

            description = _clean_description(raw_desc)
            amount = _parse_amount(raw_amount)
            category = _guess_category(description)

            transactions.append(Transaction(
                date=date,
                description=description,
                amount=amount,
                category=category,
                source_file=source,
                raw_row={"page": page_num, "raw": {str(i): str(c) for i, c in enumerate(row) if c}},
            ))
        except (IndexError, ValueError):
            continue

    return transactions


def _extract_rows_without_header(
    table: list[list[str | None]], source: str, page_num: int,
) -> List[Transaction]:
    """Heuristic extraction when no header row is found."""
    transactions = []
    for row in table:
        if row is None or all(c is None or str(c).strip() == "" for c in row):
            continue
        # Try to find a date-like cell and amount-like cell
        date_str = ""
        desc_parts = []
        amount_str = ""

        for cell in row:
            if cell is None:
                continue
            cell_str = str(cell).strip()
            if not cell_str:
                continue

            # Check for date
            if re.match(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", cell_str):
                date_str = cell_str
            # Check for dollar amounts
            elif re.match(r"^\$?-?\d[\d,]*\.\d{2}$", cell_str.replace("(", "-").replace(")", "")):
                amount_str = cell_str
            else:
                desc_parts.append(cell_str)

        date = _parse_date(date_str)
        if not date or not amount_str:
            continue

        description = _clean_description(" ".join(desc_parts))
        amount = _parse_amount(amount_str)
        category = _guess_category(description)

        transactions.append(Transaction(
            date=date,
            description=description,
            amount=amount,
            category=category,
            source_file=source,
            raw_row={"page": page_num},
        ))

    return transactions


def _extract_transactions_from_text(
    text: str, source: str, page_num: int,
) -> List[Transaction]:
    """Fallback: extract transactions from raw text using regex."""
    transactions = []

    # Look for lines that contain a date and a dollar amount
    # Pattern: MM/DD MM/DD/YYYY text... $XX.XX
    date_pat = r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    amount_pat = r"(\$?\s*-?\s*[\d,]+\.\d{2})"

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        dates = re.findall(date_pat, line)
        amounts = re.findall(amount_pat, line)

        if dates and amounts:
            date = _parse_date(dates[0])
            if not date:
                continue
            amount = _parse_amount(amounts[0])

            # Description = everything between date and amount
            desc = line
            for pat_val in dates + amounts:
                desc = desc.replace(pat_val, "", 1)
            description = _clean_description(desc)

            if not description:
                continue

            category = _guess_category(description)
            transactions.append(Transaction(
                date=date,
                description=description,
                amount=amount,
                category=category,
                source_file=source,
                raw_row={"page": page_num},
            ))

    return transactions


# ─── CSV parser ────────────────────────────────────────────────────────────────


def parse_csv_statement(file_path: str | Path) -> List[Transaction]:
    """Parse a CSV bank/credit-card statement into normalised transactions.

    Automatically detects column mapping by scanning headers for known
    patterns (date, description, amount, category).
    """
    file_path = Path(file_path)
    source = file_path.name

    console.print(f"[cyan]📊 Parsing CSV: {source}[/cyan]")

    df = pd.read_csv(file_path)

    # Auto-detect columns
    cols_lower = {c.lower().strip(): c for c in df.columns}

    date_col = _find_column(cols_lower, ["date", "transaction date", "post date", "posted date", "posting date"])
    desc_col = _find_column(cols_lower, [
        "description", "desc", "merchant", "payee", "name", "transaction",
        "memo", "narrative", "details",
    ])
    amount_col = _find_column(cols_lower, [
        "amount", "transaction amount", "value", "sum",
    ])
    debit_col = _find_column(cols_lower, ["debit", "debit amount", "withdrawal"])
    credit_col = _find_column(cols_lower, ["credit", "credit amount", "deposit", "income"])
    category_col = _find_column(cols_lower, ["category", "tag", "label", "group"])

    if date_col is None or desc_col is None:
        raise ValueError(
            f"Could not auto-detect date/description columns in {source}. "
            f"Available columns: {list(df.columns)}"
        )

    transactions = []
    for _, row in df.iterrows():
        raw_date = str(row[date_col])
        date = _parse_date(raw_date)
        if not date:
            continue

        description = _clean_description(str(row[desc_col]))

        # Determine amount
        if amount_col is not None and pd.notna(row[amount_col]):
            amount = _parse_amount(str(row[amount_col]))
        elif debit_col is not None and pd.notna(row[debit_col]):
            amount = -abs(_parse_amount(str(row[debit_col])))
        elif credit_col is not None and pd.notna(row[credit_col]):
            amount = abs(_parse_amount(str(row[credit_col])))
        else:
            amount = 0.0

        # Use provided category or auto-guess
        if category_col is not None and pd.notna(row[category_col]):
            category = str(row[category_col]).strip()
        else:
            category = _guess_category(description)

        transactions.append(Transaction(
            date=date,
            description=description,
            amount=amount,
            category=category,
            source_file=source,
            raw_row=row.to_dict(),
        ))

    console.print(
        f"  [green]✔[/green] Extracted {len(transactions)} transactions "
        f"from {source}"
    )
    return transactions


def _find_column(cols_lower: dict, candidates: list[str]) -> str | None:
    """Find the first column name that matches any candidate.

    Iterates candidates first (more specific → broader) so 'merchant'
    wins against 'transaction' when 'transaction date' is also a column.
    """
    for candidate in candidates:
        for col_key, col_name in cols_lower.items():
            if candidate in col_key:
                return col_name
    return None


# ─── Unified loader entry point ───────────────────────────────────────────────


def load_transactions(file_path: str | Path) -> List[Transaction]:
    """Load transactions from a statement file (PDF or CSV).

    Auto-detects file type by extension.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf_statement(file_path)
    elif suffix in (".csv", ".tsv", ".txt"):
        return parse_csv_statement(file_path)
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported formats: .pdf, .csv"
        )


# ─── Chunking for RAG ─────────────────────────────────────────────────────────


def transactions_to_documents(
    transactions: List[Transaction],
    group_by_month: bool = True,
) -> List[Document]:
    """Convert a list of Transactions into LangChain Documents ready for embedding.

    Groups transactions by month and creates a document per month,
    then each individual transaction is a document too for fine-grained retrieval.
    """
    documents: List[Document] = []

    if group_by_month and transactions:
        # Group by month
        months: dict[str, list[Transaction]] = {}
        for tx in transactions:
            month_key = tx.date[:7]
            months.setdefault(month_key, []).append(tx)

        for month_key, month_txs in sorted(months.items()):
            total_debits = sum(tx.amount for tx in month_txs if tx.amount < 0)
            total_credits = sum(tx.amount for tx in month_txs if tx.amount > 0)
            text = (
                f"Monthly Summary: {month_key}\n"
                f"Total transactions: {len(month_txs)}\n"
                f"Total spent: ${abs(total_debits):.2f}\n"
                f"Total income/credits: ${total_credits:.2f}\n\n"
                + "\n".join(tx.to_document_text() for tx in month_txs)
            )
            documents.append(Document(
                page_content=text,
                metadata={
                    "type": "monthly_summary",
                    "month": month_key,
                    "transaction_count": len(month_txs),
                    "total_spent": abs(total_debits),
                    "total_income": total_credits,
                    "source_files": list(set(tx.source_file for tx in month_txs)),
                },
            ))

    # Individual transaction documents (for specific queries like "what's that $14.99 charge?")
    for tx in transactions:
        documents.append(Document(
            page_content=tx.to_document_text(),
            metadata=tx.to_metadata(),
        ))

    console.print(
        f"[bold green]✔  Created {len(documents)} searchable documents "
        f"from {len(transactions)} transactions[/bold green]"
    )
    return documents


def load_and_chunk(
    file_paths: list[str | Path],
    group_by_month: bool = True,
) -> list[Document]:
    """Full pipeline: load one or more statement files and chunk for RAG.

    Parameters
    ----------
    file_paths      : List of paths to PDF or CSV statement files.
    group_by_month  : Create monthly summary documents.

    Returns
    -------
    List of LangChain Documents ready for embedding.
    """
    all_transactions: list[Transaction] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Loading statements…", total=len(file_paths))

        for fp in file_paths:
            progress.update(task, description=f"[cyan]Processing: {Path(fp).name}")
            try:
                txs = load_transactions(fp)
                all_transactions.extend(txs)
            except Exception as exc:
                console.print(f"  [red]✗  Failed to load {fp}: {exc}[/red]")
            progress.advance(task)

    if not all_transactions:
        raise ValueError("No transactions could be loaded from the provided files.")

    console.print(
        f"\n[bold green]✔  Loaded {len(all_transactions)} total transactions "
        f"from {len(file_paths)} file(s).[/bold green]"
    )

    return transactions_to_documents(all_transactions, group_by_month=group_by_month)
