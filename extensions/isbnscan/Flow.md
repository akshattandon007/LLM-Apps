# Flow — ISBNScan

## Module Dependency Graph

```
isbnscan/
├── __init__.py        ← Package metadata (__version__)
├── __main__.py        ← Entry point: calls cli.main()
├── cli.py             ← CLI layer: argparse → calls lookup functions → prints results
│   ├── imports: lookup (batch_lookup, clean_isbn, is_valid_isbn, normalize_isbn, results_to_csv)
│   └── functions:
│       ├── read_isbns_from_file(path) -> list[str]
│       ├── colorize(text, color) -> str
│       ├── print_table(results, csv_path) -> None
│       └── main(argv) -> int
└── lookup.py          ← API layer: Open Library HTTP calls
    ├── imports: httpx, csv, json, re, sys, dataclasses
    ├── constants:
    │   ├── OPEN_LIBRARY_API = "https://openlibrary.org/api/books"
    │   └── USER_AGENT = "isbnscan/1.0 ..."
    ├── dataclass:
    │   └── BookResult(isbn, title, authors, publisher, publish_year, page_count, subjects, cover_url, found)
    ├── helpers:
    │   ├── clean_isbn(raw: str) -> str
    │   ├── is_valid_isbn(isbn: str) -> bool
    │   └── normalize_isbn(isbn: str) -> str
    ├── main functions:
    │   ├── lookup_isbn(isbn: str, client: Optional[httpx.Client]) -> BookResult
    │   ├── batch_lookup(isbns: list[str], client: Optional[httpx.Client]) -> list[BookResult]
    │   └── results_to_csv(results: list[BookResult], path: str) -> None
    └── external:
        └── Open Library API GET /api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data

tests/
└── test_lookup.py     ← Test suite (pytest + MockTransport)
    ├── imports: pytest, httpx, MockTransport, all lookup module functions
    ├── helper: _mock_success(book_data) -> MockTransport
    ├── helper: _mock_error(status) -> MockTransport
    ├── TestCleanIsbn
    ├── TestIsValidIsbn
    ├── TestNormalizeIsbn
    ├── TestLookupIsbn
    ├── TestBatchLookup
    └── TestResultsToCsv
```

## Function-Level Call Chains

### Startup → Results

```
python -m isbnscan 9780141036144
  └── __main__.py
       └── cli.main(["9780141036144"])
            ├── normalize_isbn("9780141036144")
            ├── is_valid_isbn("9780141036144")
            ├── batch_lookup(["9780141036144"])
            │    └── lookup_isbn("9780141036144")
            │         ├── clean_isbn("9780141036144")
            │         ├── httpx.Client.get(OPEN_LIBRARY_API, params)
            │         │    └── Open Library API → JSON response
            │         └── BookResult(...) ← parsed from JSON
            └── print_table(results)
                 └── colorize(...) for each field
```

### File Input → CSV Export

```
isbnscan --file isbns.txt --csv results.csv
  └── cli.main()
       ├── read_isbns_from_file("isbns.txt") → list[str]
       ├── [for each ISBN] normalize + validate
       ├── batch_lookup(valid_isbns) → list[BookResult]
       ├── print_table(results)
       └── results_to_csv(results, "results.csv")
            └── csv.DictWriter → writes rows
```

## Data Flow

```
User Input (ISBNs)
    │
    ▼
normalize_isbn() / clean_isbn()  ──►  Remove dashes/spaces/prefixes
    │
    ▼
is_valid_isbn()  ──►  Reject invalid formats
    │
    ▼
lookup_isbn()  ──►  httpx GET → Open Library API
    │                    │
    │                    ▼
    │              JSON response
    │                    │
    ▼                    ▼
BookResult(found=True/False)
    │
    ├──► print_table()  ──►  Terminal output (colorized)
    │
    └──► results_to_csv()  ──►  CSV file
```

## Error Handling Flow

```
lookup_isbn() called
    │
    ├── httpx.HTTPError → BookResult(found=False, title="[ERROR: ...]")
    ├── httpx.TimeoutException → BookResult(found=False, title="[ERROR: ...]")
    ├── json.JSONDecodeError → BookResult(found=False, title="[ERROR: ...]")
    └── bibkey not in response → BookResult(found=False, title="[NOT FOUND]")

cli.main() called
    │
    ├── no ISBNs provided → print help → return 1
    ├── invalid ISBNs → print warning, skip them
    └── no valid ISBNs → print error → return 1
```
