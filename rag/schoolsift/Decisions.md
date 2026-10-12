# Schoolsift — Decisions

Every meaningful architecture choice, the alternatives that were rejected,
and why. Read this before changing the retrieval core.

## 1. Chose Schoolsift as today's RAG project

- **Chosen:** A plain-language search engine over a folder of school
  documents (newsletters, permission slips, syllabi), with cited answers and
  automatic date/deadline extraction.
- **Rejected:** recipe-library search, medication-label Q&A (DailyMed),
  tax-form parsing, travel-notes + Wikivoyage mashup (the other four
  researched ideas).
- **Why:** highest *weekly* pain frequency for parents, free-text PDF
  ingestion with zero parsing complexity, no external API runtime dependency
  — the most reliably shippable RAG app in one session, and nothing in the
  existing repo covers school/parent paperwork.

## 2. Local, dependency-free retrieval core — no embeddings, no API keys

- **Chosen:** pure-Python TF-IDF + BM25 index over chunked text.
- **Rejected:** OpenAI `text-embedding-3-small` + GPT-4o-mini (the stack
  ManualMate uses), sentence-transformers/all-MiniLM + ChromaDB, and any
  hosted embedding API.
- **Why:** a school folder is tens of small documents, and school paperwork
  is keyword-dense ("science fair", "deadline", room numbers) — lexical
  retrieval is genuinely good here. An embedding model would have added an
  ~800MB torch install or a paid API key that must exist at runtime, broke
  offline use, and made the pipeline non-deterministic. Kids' documents also
  deserve a stay-on-your-machine default.

## 3. Hybrid ranker: 0.65 cosine tf-idf + 0.35 BM25

- **Chosen:** blend of cosine similarity over tf-idf vectors and BM25
  scores, BM25 normalized by its max before blending.
- **Rejected:** either ranker alone; pure keyword overlap matching.
- **Why:** cosine tf-idf favors whole-phrase topical match; BM25 saturates
  term-frequency gains and counters raw tf-idf's bias toward long documents
  (a two-paragraph permission slip must not lose to a 2-page newsletter).

## 4. Bigram features alongside unigrams

- **Chosen:** token features include unigrams plus bigrams of adjacent
  ≥3-char terms ("science_fair", "permission_slip").
- **Rejected:** exact-phrase-only matching; embedding-based phrase handling.
- **Why:** parents ask in phrases ("when is the **science fair**"), and
  unigrams alone would return both the science fair and the book fair
  documents with nearly equal scores. Bigrams make phrase-level recall work
  with zero extra dependencies.

## 5. pymupdf (fitz) for PDF text extraction

- **Chosen:** pymupdf's fast text-layer extraction, one self-contained wheel.
- **Rejected:** pdfplumber, PyPDF2/pypdf, OCR (tesseract), and a
  subprocess-based poppler wrapper.
- **Why:** pymupdf is the fastest pure-wheel option and extracts the text
  layer reliably for typed school documents. OCR was rejected for v1 because
  scanned-only documents are out of scope — and OCR would add a heavyweight
  system dependency and slow indexing dramatically.

## 6. Chunking: 700 chars, paragraph- and line-aware, with page metadata

- **Chosen:** paragraphs accumulate into ≤700-char chunks; over-long
  paragraphs are hard-split with a 60-char sliding overlap; every chunk
  carries its document id and page number.
- **Rejected:** whole-document vectors; fixed 100-char windows; sentence-only
  chunks.
- **Why:** 700 chars keeps chunks dense enough for meaningful cosine/BM25
  scores and short enough for useful quoting; the overlap keeps phrases that
  straddle a cut findable; page metadata is what makes citations
  ("Sept Newsletter.pdf p.3") trustworthy. Line breaks inside a paragraph are
  preserved so a title line can never merge into the first body sentence.

## 7. Storage: one JSON index file, rebuilt on every `index` run

- **Chosen:** `Store` serialized to `~/.schoolsift/index.json`
  (override: `--store` flag or `SCHOOLSIFT_STORE` env var).
- **Rejected:** SQLite, ChromaDB, per-document sidecar files, a server/db
  daemon.
- **Why:** the corpus is small; a full rebuild takes milliseconds and
  guarantees the index always matches the folder (no stale-entry bugs). One
  JSON file is trivially portable, inspectable, and testable. ChromaDB would
  drag in onnxruntime and friends for zero benefit at this scale.

## 8. Date extraction: regex + heuristics, not dateparser or an LLM

- **Chosen:** a small deterministic extractor in `dates.py` covering
  month-day ("October 14"), "Oct 14th", MM/DD/YYYY, ISO dates, and relative
  weekdays ("next Wednesday").
- **Rejected:** the `dateparser` library (heavy tzdata dependency, opaque
  behavior, hard to pin in tests) and LLM extraction (needs a key,
  nondeterministic, would violate the offline guarantee).
- **Why:** school-document date formats are a small, enumerable set; regex
  extraction is fast, dependency-free, and — critically — testable with
  exact expected outputs.

## 9. Nearest-future year/date resolution policy

- **Chosen:** dates without a year resolve to the first occurrence on or
  after today (rolling to next year if this year's date has passed); a bare
  weekday means the next one after today.
- **Rejected:** assuming the current year always; assuming "next X weekday"
  means the immediate next occurrence.
- **Why:** school documents are almost always about *upcoming* dates
  ("December 15" on December 20 must mean next December). An explicit
  calendar date in a sentence suppresses that sentence's unqualified weekday
  matches — "Saturday, October 24" must not also spawn a phantom "next
  Saturday" — a bug the test suite caught during development.

## 10. Deadline detection: keyword signals, per sentence

- **Chosen:** a sentence is a "deadline" when it contains any of a small
  signal list — `due`, `deadline`, `return`, `submit`, `no later than`,
  `complete and`, `sign and`, etc.
- **Rejected:** NLP dependency parsing, "due date" field extraction, or
  requiring an explicit "due by X" phrase.
- **Why:** real slips say "Please complete and return this slip by October
  28" — free-form enough that a precise grammar would miss it. The keyword
  heuristic is imperfect but predictable, cheap, and documented; the
  `(deadline)` tag in output makes the assumption transparent to users.

## 11. Answers are extractive and cited — no LLM generation

- **Chosen:** the answer is the best-overlap sentence from the top chunk
  (tie-break: prefer a sentence with a calendar date, then shorter), each
  passage is quoted with `document (p.N)`, and extracted dates are listed
  separately.
- **Rejected:** generating a free-form summary with an LLM.
- **Why:** extractive answers cannot hallucinate, cost nothing, run offline,
  and every claim is backed by a visible source — which is the entire point
  of a RAG app for documents that matter (deadlines, forms, meeting times).

## 12. CLI: argparse subcommands, no server

- **Chosen:** `index / ask / dates / list / clear` via argparse,
  invoked as `python3 -m schoolsift`.
- **Rejected:** a localhost web UI (FastAPI/Flask), a TUI, a hosted service.
- **Why:** the user is one parent on one machine — a server adds a process
  to babysit and a browser tab to lose. Subcommands map 1:1 to the workflow
  and match the repo's existing CLI-first convention. `--store` is defined
  on both the main parser and subparsers (subparser default
  `argparse.SUPPRESS`) so it works both before and after the subcommand —
  a live-found argparse gotcha, now pinned by the CLI tests.

## 13. Tests: synthetic PDFs generated at fixture time

- **Chosen:** `conftest.py` builds newsletter/permission-slip PDFs with
  pymupdf on the fly; date tests inject an explicit `today`; CLI tests run
  in-process with `--store` pointed at tmp paths.
- **Rejected:** checking binary PDF fixtures into git; mocking pymupdf; using
  the real system clock in date assertions.
- **Why:** no binary blobs in the repo, fixtures stay truthful against the
  real extractor, and every date test is deterministic no matter when it
  runs. The synthetic-folder approach also caught the chunking infinite-loop
  and the title-merging bugs that no mock-based suite would have found.

## 14. Packaging: pyproject.toml + `python3 -m schoolsift`

- **Chosen:** minimal `pyproject.toml` (setuptools), package invoked as a
  module; `pytest` configured via `[tool.pytest.ini_options]` with
  `pythonpath = ["."]`.
- **Rejected:** `setup.py` + console-script entry point; installing into the
  environment as a prerequisite.
- **Why:** running from the repo directory with zero install steps is the
  lowest-friction path for a parent; module invocation keeps the package
  importable in tests without installation. Console scripts were rejected —
  they'd require an install step and would silently use a stale copy when
  the repo updates.