# Decisions — triallight

## 1. Problem: How to present clinical trial data to a non-medical audience

**Decision:** Use RAG pipeline: search API → retrieve structured records → LLM rewrite in plain language.  
**Rejected:** Building a generic "chat with ClinicalTrials.gov" chatbot (too slow, harder to verify accuracy), or a static list view with no explanation (user still can't understand eligibility).  
**Why:** RAG gives the LLM exact ground truth to rewrite from, making hallucinations less likely than an open-ended chatbot. The user gets both the raw data *and* the plain-language summary side by side.

## 2. Problem: Which clinical trial API to use

**Decision:** ClinicalTrials.gov API v2.  
**Rejected:** AACT database (requires PostgreSQL setup), or scraping HTML.  
**Why:** v2 is REST+JSON, no auth needed, returns structured fields (NCTId, eligibilityCriteria, conditions) that map cleanly to our model. AACT would require a database server; scraping is fragile and ToS-sensitive.

## 3. Problem: Whether to include PubMed context

**Decision:** Yes, as an optional module.  
**Rejected:** Skip it entirely, or use a general web search instead.  
**Why:** PubMed E-utilities is the canonical source for recent research about a condition and is free/no-auth. It adds valuable context for the LLM's digest. Users who want speed or data minimization can turn it off with `--no-pubmed`.

## 4. Problem: LLM integration approach

**Decision:** Use the `openai` Python package with configurable base URL.  
**Rejected:** LangChain (heavy dependency), direct HTTP requests to OpenAI API, or a local model.  
**Why:** The `openai` package is lightweight, well-maintained, and works with any OpenAI-compatible provider (OpenAI, OpenRouter, Together, etc.). LangChain adds complexity and cost for what is essentially a prompt → response call. A local model would be too slow for a single-session build and has no advantage for this use case.

## 5. Problem: How to handle eligibility criteria parsing

**Decision:** Parse the free-text `eligibilityCriteria` field by splitting on lines and tracking INCLUSION/EXCLUSION headers.  
**Rejected:** Using a regex-based NLP parser, or leaving the raw text as-is.  
**Why:** The eligibility field is structured text with clear section headers — line-splitting is simple, reliable, and captures 95%+ of records correctly. An NLP parser would add 200+ lines and a model dependency (spaCy etc.) for marginal gain. The LLM gets the full text anyway and handles the nuance.

## 6. Problem: Geocoding for location-based search

**Decision:** Use Open-Meteo Geo API.  
**Rejected:** Google Maps API (requires API key + billing), Nominatim (rate-limited, no bulk), or skipping location filtering.  
**Why:** Open-Meteo is free, no auth, no rate limits, and works for city-level geocoding which is all we need for "near me" trial search. The ClinicalTrials.gov API supports a `locn` parameter for city-level filtering.

## 7. Problem: CLI versus web interface

**Decision:** CLI with `argparse` + `rich` for formatting.  
**Rejected:** FastAPI web app, or a Jupyter notebook.  
**Why:** CLI is the fastest way to ship in one session — no auth, no frontend, no deployment. The `rich` library makes terminal output readable with colors, panels, and markdown rendering. A web app can be added later (and the separation of src/ from main.py makes this straightforward).

## 8. Problem: How to handle missing API key

**Decision:** Support `--raw` mode that shows structured study data without LLM augmentation.  
**Rejected:** Requiring an API key to use the tool at all, or silently failing.  
**Why:** The API search + structured display is still useful without AI digests. Users can try the tool immediately, get value, and add an API key when they want AI summaries.

## 9. Problem: LLM prompt design for medical accuracy

**Decision:** Include a mandatory disclaimer in every digest; instruct the LLM to rewrite, not add medical advice.  
**Rejected:** No disclaimer (liability risk), or a post-hoc warning after the output.  
**Why:** Putting the disclaimer in the prompt ensures it appears in every digest. The prompt explicitly tells the LLM "never give medical advice" and "always verify with the trial coordinator."

## 10. Problem: Which LLM model to default to

**Decision:** `gpt-4o-mini`.  
**Rejected:** gpt-4o (higher cost, slower), claude-3-haiku (requires Anthropic SDK), or gpt-3.5-turbo (worse at instruction following).  
**Why:** gpt-4o-mini is cheap (~$0.15/1M input tokens), fast, and surprisingly good at following the 4-section digest format. Users can override with `--model` anyway. OpenRouter users can specify any compatible model.

## 11. Problem: Whether to add a vector store / embedding step

**Decision:** Skip it.  
**Rejected:** FAISS + sentence-transformers for chunking and retrieval over a static corpus.  
**Why:** The "corpus" here is live API results — no pre-built document collection exists. Each search fetches fresh data, so there's nothing to index ahead of time. Building a vector store would add complexity without benefit.

## 12. Problem: How to structure the Python package

**Decision:** `src/` layout with a top-level `main.py` entry point.  
**Rejected:** Flat layout with all code in one file, or a deep `triallight/` package.  
**Why:** The `src/` layout is the Python community standard for non-trivial CLI tools. Each module has a single responsibility (API wrapper, LLM, models). One-session buildability is preserved — no deep hierarchy or dependency injection framework.

## 13. Problem: How to handle API errors gracefully

**Decision:** Wrap each external call in try/except in main.py, show a warning, and continue with available data.  
**Rejected:** Crash with traceback, or retry infinitely.  
**Why:** If ClinicalTrials.gov is slow but PubMed is down, the user should still get trial results. Failing one data source shouldn't fail the whole pipeline.