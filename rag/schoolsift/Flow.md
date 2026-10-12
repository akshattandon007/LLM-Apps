# Schoolsift — Flow

How a request moves through the code, from the terminal to the printed
answer. Every function is listed with its call chain.

## Entry point

```
python3 -m schoolsift <command> [args] [--store PATH]
        │
        ▼
schoolsift/__main__.py
        └─ main()                                  # schoolsift/cli.py
```

`main(argv)` builds one `argparse` parser per invocation and dispatches on
the subcommand via `args.func(args)`:

| Command | Dispatcher            | Purpose                                   |
|---------|-----------------------|-------------------------------------------|
| `index` | `cmd_index(args)`     | Extract + chunk + build + persist index   |
| `ask`   | `cmd_ask(args)`       | Retrieve and print a cited answer         |
| `dates` | `cmd_dates(args)`     | Retrieve and print only dates/deadlines   |
| `list`  | `cmd_list(args)`      | Show what is indexed                      |
| `clear` | `cmd_clear(args)`     | Delete the local index file               |

`cmd_ask`, `cmd_dates`, `cmd_list` share `_load_store(args)` → raises
`SystemExit(1)` with a "No index found" hint when the store is missing.

---

## Path A — `index <folder>`: build the index

```
cmd_index(args)
├─ ingest_folder(folder)                          # schoolsift/ingest.py
│   ├─ extract_pages(path)                        # per supported file (.pdf/.txt/.md)
│   │   ├─ _extract_pdf_pages(path)               # pymupdf (fitz): page.get_text("text")
│   │   └─ (txt/md) → read_text → single page
│   ├─ chunk_page(page_text, page_number)         # ⇄ _chunk_text(text)
│   │     700-char chunks, paragraph/line-aware, 60-char overlap on hard-split
│   └─ → [ {id, path, title, pages, chunks:[{page,text}]}, ... ]  (doc records)
│
├─ index.build(docs)                              # schoolsift/index.py
│   ├─ tokenize.terms(c["text"])                  # unigrams + bigrams
│   ├─ df (document frequency) per term; vocab = sorted(df)
│   ├─ idf[t] = log(1 + N / (1 + df[t]))
│   ├─ per-chunk tf-idf vectors {term: (1+log tf)*idf}
│   ├─ per-chunk raw counts + doc lengths + avgdl   # for BM25 at query time
│   └─ → Store (in-memory)
│
└─ Store.save(path)                               # one JSON file:
      docs, chunks, vocab, idf, df, vectors, counts, doc_lens, avgdl, built_at
```

### Call chain (index)

```
cmd_index ─→ ingest_folder ─→ extract_pages ─→ _extract_pdf_pages
                        └─→ chunk_page ─→ _chunk_text
build ─→ terms (tokenize) ─→ Counter/df ─→ idf smoothing ─→ vectors/counts
```

### Data flow (index)

```
PDF/TXT files
   │  pymupdf text layer
   ▼
page text {number, text}
   │  paragraph + line-aware chunking (700 chars, 60 overlap)
   ▼
chunks {doc_id, page, text}
   │  terms() → unigram + bigram features
   ▼
df / idf → per-chunk tf-idf vectors + BM25 stats
   │
   ▼
~/.schoolsift/index.json   (Store.save)
```

---

## Path B — `ask "<question>"`: retrieve + answer

```
cmd_ask(args)
├─ _load_store(args)
│   └─ Store.load(path)                           # reconstruct in-memory index
├─ search.search(store, question, k=5)            # schoolsift/search.py
│   ├─ terms(question) → qterms (set)
│   ├─ qvec = {t: idf[t] for t ∈ qterms}
│   ├─ _cosine(qvec, chunk_vector)                # sparse dot / norms
│   ├─ _bm25(qterms, counts, doc_len, avgdl, n, df)
│   ├─ blend = 0.65·cosine + 0.35·(bm25/max_bm25)
│   ├─ sort desc, top-k, drop zero-blend
│   └─ → [ {score, chunk, doc}, ... ]
│
└─ answer.build_answer(store, question, hits)     # schoolsift/answer.py
    ├─ _best_sentence(top.chunk.text, qterms)
    │     best-overlap sentence; tie-break: has calendar date → shorter
    ├─ _cite(hit)                                 # "title (p.N)"
    ├─ _snippet(chunk.text, 220)                  # clean + truncate
    ├─ extract_dates(joined top-k text)           # schoolsift/dates.py
    └─ formats: A: <sentence>  /  Supporting passages  /  Key dates
```

### Function-level trace for `ask "when is the science fair?"`

```
cli.main → cmd_ask
  → Store.load("/tmp/idx.json")
  → search.search(store, "when is the science fair")     [returns top-5]
      → terms("when is the science fair") → {"when"→stopword dropped,
        "science","fair","science_fair"} → qvec (idf-weighted)
      → for each chunk: _cosine + _bm25 → blend → rank
      → hits[0] = the permission-slip chunk (title: permission-slip-science-fair)
  → build_answer(store, question, hits)
      → _best_sentence(chunk.text, qterms) → "The Maplewood Science Fair
        will take place on November 20."        (tie-break prefers dated sentence)
      → _cite(hits[0]) → "permission-slip-science-fair (p.1)"
      → _snippet for supporting passages
      → extract_dates(" ".join(top chunk texts))
          → per sentence: month-day/MDY/ISO/weekday regexes, year resolution
            vs today, deadline keyword check → DateHit{iso, kind, context}
      → prints Key dates with iso + "(deadline)" tags
```

---

## Path C — `dates "<question>"`: retrieve + list dates only

```
cmd_dates(args)
├─ _load_store(args)
├─ search.search(store, question, k=5)
└─ extract_dates(" ".join(hits' chunk texts))
    └─ dedupe by (iso, kind) → sort chronologically → print
```

`extract_dates(text, today=None)` internals (`schoolsift/dates.py`):

- `split_sentences` (in `textutil.py`) splits on `[.!?]` **or newlines**
  (preserves title lines from chunking).
- `_is_deadline(sentence)` — keyword signal list.
- `_resolve(month, day, year, today)` — explicit year, else nearest future.
- `_weekday_date(name, qualifier, today)` — bare weekday → next occurrence;
  "next X" → skip current week.
- Explicit-date suppression: if a sentence already produced a calendar date,
  unqualified weekday matches in the same sentence are skipped.

---

## Path D — `list` / `clear`

```
cmd_list(args)  → _load_store → prints docs[].title, pages, chunk_count, built_at
cmd_clear(args) → path.unlink() when store exists
```

---

## Module dependency graph

```
                        ┌─────────────┐
                        │   cli.py    │  (entry: main → cmd_*)
                        └──────┬──────┘
       ┌──────────┬────────────┼────────────┬──────────────┐
       ▼          ▼            ▼            ▼              ▼
   ingest.py   index.py    search.py    answer.py      (Store.load)
       │          │            │            │
       │          │            │            ├──► dates.py
       │          │            │            └──► textutil.py
       │          │            ├──► tokenize.py ──► (stopwords)
       │          └──► tokenize.py
       └──► (pymupdf / fitz)   [external]
```

- `tokenize.py` — used by `index.py` (feature building), `search.py`
  (query features), `answer.py` (overlap scoring).
- `textutil.py` — used by `dates.py` (sentence split) and `answer.py`
  (cleaning/snippets).
- `dates.py` — used by `answer.py` (Key dates) and `cli.py` (`dates` cmd).
- `index.py` / `search.py` / `answer.py` / `dates.py` never import each
  other's internals; they communicate through plain dicts and the `Store`
  object.

## Test → code coverage map

| Test module            | Exercises                                            |
|------------------------|------------------------------------------------------|
| `test_dates.py` (11)   | extract_dates: formats, rollover, weekdays, dedupe   |
| `test_ingest.py` (5)   | extract_pages, chunk_page, _chunk_text, ingest_folder|
| `test_search.py` (6)   | ranking, phrase recall, no-match, stopword-only      |
| `test_answer.py` (6)   | citations, date surfacing, title-fragment regression |
| `test_cli.py` (3)      | full cmd flow, missing store/folder errors           |