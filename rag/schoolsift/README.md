# Schoolsift 🏫🔎

**Your school-paperwork search engine.** Parents drown in PDFs — newsletters,
permission slips, syllabi, PTA emails. Schoolsift indexes that folder and
answers plain-language questions like *"when is the science fair?"* or *"what
do I need to send by Friday?"* — with the exact document, page, and date
cited. Everything runs **100% locally**: your kids' documents never leave
your machine.

## Quick Start

```bash
# Install the one real dependency
pip install -r requirements.txt

# Index a folder of school PDFs / txt files (recursive)
python3 -m schoolsift index ~/Downloads/school-papers

# Ask a question — get a cited answer
python3 -m schoolsift ask "when is the science fair?"

# Pull just the dates and deadlines out of the relevant documents
python3 -m schoolsift dates "permission slip"

# See what's indexed / start fresh
python3 -m schoolsift list
python3 -m schoolsift clear
```

Example:

```
$ python3 -m schoolsift ask "when is the science fair?"
Q: when is the science fair?
A: The Maplewood Science Fair will take place on November 20.
   — science-fair-permission-slip (p.1)

Supporting passages:
- science-fair-permission-slip (p.1): "Science Fair Permission Slip
  The Maplewood Science Fair will take place on November 20. Please complete
  and return this slip to your child's teacher by October 28. ..."

Key dates found in those passages:
- 2026-10-28 (deadline) — Please complete and return this slip to your child's teacher by October 28.
- 2026-11-20 — The Maplewood Science Fair will take place on November 20.
```

## How It Works

1. **Ingest** — PDFs are read with pymupdf (pure text layer; no OCR needed for
   typed school documents). Text is split into ~700-char chunks with page
   numbers attached.
2. **Index** — a dependency-free TF-IDF index is built in-memory and saved to
   one JSON file. Unigrams **and** significant bigrams ("science_fair",
   "permission_slip") make phrase retrieval work without any embedding model.
3. **Retrieve** — your question is ranked against every chunk with a
   **0.65 cosine tf-idf + 0.35 BM25** blend, so short permission slips don't
   get drowned out by long newsletters.
4. **Answer** — the best-matching sentence is quoted with its source
   (`document (p.N)`), surrounding passages are listed, and a **date
   extractor** surfaces every event and deadline in the retrieved text
   (including relative ones like "return the form on Friday").

## Storage

Index lives in `~/.schoolsift/index.json` by default. Override with
`--store PATH` or the `SCHOOLSIFT_STORE` env var.

## Requirements

- Python 3.9+
- [pymupdf](https://pypi.org/project/PyMuPDF/) (the only install — no torch,
  no ChromaDB, no API keys)

## Project Files

- `schoolsift/` — the package (`ingest`, `index`, `search`, `dates`,
  `answer`, `cli`)
- `tests/` — 31 unit + end-to-end tests (synthetic PDFs generated at
  fixture time, deterministic dates)
- `Decisions.md` — every architecture choice and the alternatives rejected
- `Flow.md` — execution traces, function-level call chains, dependency graph

## Roadmap

- Scanned PDFs (OCR via tesseract) for parents who still get paper copies
- Calendar export (ICS) of extracted deadlines
- Weekly digest: "this week's deadlines from your folder"