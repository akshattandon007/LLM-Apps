# Decisions.md — DreamDecoder

## Architectural decisions, trade-offs, and rejected alternatives

---

### 1. CLI over Web UI

**Chosen:** Command-line interface with argparse  
**Rejected:** Flask web app, Streamlit dashboard, TUI (Textual)  
**Why:** CLI is the fastest path to a working product. The target user (Akshat / Hermes ops) live in the terminal. A web app would add UX complexity, CSS/JS dependencies, and deployment overhead with no benefit for daily CLI use. Streamlit or Textual would be nice but add a dependency chain and aren't available on the VPS without install.

### 2. Local JSON file over SQLite

**Chosen:** Flat JSON file at `~/.dreamdecoder_journal.json`  
**Rejected:** SQLite, DuckDB, SQLAlchemy, Redis  
**Why:** The journal is a simple ordered list of entries — no relational queries, no concurrent writers, no need for ACID beyond file-level atomicity. JSON is human-readable, debuggable, requires zero schema migrations, and uses zero external dependencies. SQLite would be overkill for a single-user append-only journal. The atomic `write → rename` pattern prevents corruption.

### 3. Subprocess LLM call over direct HTTP API

**Chosen:** `subprocess.run(["/opt/venv/bin/hermes", "chat", ...])`  
**Rejected:** Direct HTTP to OpenRouter/OpenAI, `requests` library, LangChain  
**Why:** The Hermes CLI is configured and authenticated in this environment. It works without API keys, without additional Python packages, and respects the user's configured provider/model. Direct HTTP would require parsing config files for keys and duplicating auth logic. LangChain is a 100MB+ dependency for what amounts to one API call. The trade-off: subprocess is slower (process spawn per call) and fragile to CLI output changes, but it's zero-dependency and zero-configuration.

### 4. Fallback symbolic interpreter over LLM-only

**Chosen:** Two-tier: try LLM first, fall back to keyword-based symbol library  
**Rejected:** LLM-only with no fallback, hardcoded responses only  
**Why:** The Hermes CLI may be unavailable (model downtime, process not running, not installed). A keyword-based symbol library with 12+ common dream motifs provides a meaningful interpretation even when the LLM is offline. The fallback is transparent — users get useful analysis either way. The cost: maintaining a symbol library that will never be as nuanced as the LLM.

### 5. Python dataclasses over dicts or Pydantic

**Chosen:** `@dataclass` with `to_dict`/`from_dict` methods  
**Rejected:** Plain dicts, Pydantic models, attrs, TypedDict  
**Why:** Dataclasses give type hints, immutability options, and clean serialization without external deps. Pydantic would add a dependency and is overkill for 4 simple models. Plain dicts lack type safety — `entry["interprtation"]` silently fails. The manual `to_dict`/`from_dict` is a few lines per class and keeps the zero-dependency promise.

### 6. Single-file CLI over multiple subcommands

**Chosen:** Single `main.py` with subcommands (log, list, view, search, stats, delete, clear)  
**Rejected:** One-off scripts per command, single `--mode` flag, multi-file CLI tool  
**Why:** argparse subcommands give the most intuitive UX. `python main.py log "text"` reads better than `python main.py --mode log --text "text"`. The dispatch table pattern in cli.py is clean and testable.

### 7. UUID hex IDs over auto-increment integers

**Chosen:** 12-char hex UUID (first 12 hex chars of uuid4)  
**Rejected:** Auto-increment integers, full UUID4 strings, ULIDs  
**Why:** Short enough to type, unique without coordination, prevents ID confusion when sharing entries. Full UUID4 strings (36 chars) are too long for CLI use. Auto-increment would collide if entries are ever merged or manually edited.

### 8. `datetime.now(timezone.utc)` over naive UTC

**Chosen:** Timezone-aware UTC timestamp  
**Rejected:** Naive UTC, local time, epoch integers  
**Why:** All entries sort correctly regardless of the user's timezone or DST changes. The ISO format is human-readable. Naive UTC would be ambiguous if we ever add timezone display.

### 9. Rich terminal output over plain text

**Chosen:** Emoji-rich formatting with box-drawing characters  
**Rejected:** Plain text, HTML rendering, ANSI colors via colorama  
**Why:** Emoji + Unicode box drawing works in every modern terminal without dependencies. ANSI colors via colorama need an install. The formatting makes dream entries feel personal and engaging rather than like raw data dumps. The `_term_width()` dynamic width ensures it works on narrow and wide terminals.

### 10. Stats module over external analytics

**Chosen:** Built-in aggregator (top symbols, mood distribution, themes bar chart)  
**Rejected:** Matplotlib charts, pandas analysis, external service  
**Why:** The stats are simple counts — no need for a data science stack. The ASCII mood bar chart is fun and dependency-free. Users get pattern recognition without exporting data or running external tools.

### 11. Test isolation via tempfile over monkey-patching

**Chosen:** `tempfile.mkdtemp()` + swapping `journal.JOURNAL_PATH` in setUp/tearDown  
**Rejected:** `pyfakefs`, `unittest.mock` for file operations, fixture files  
**Why:** Temp directories are zero-dependency and reliable. Mocking `open()` or `pathlib` is fragile across Python versions. The setUp/tearDown pattern is explicit and easy to debug. The trade-off is a few extra lines per test class.

### 12. No `setup.py`/`pyproject.toml` over packaging

**Chosen:** Run via `python main.py` directly  
**Rejected:** pip-installable package, entry_points, Poetry project  
**Why:** This is a personal tool, not a library. Packaging adds metadata, version management, and install steps for no benefit. Running `python main.py <command>` from the project directory is the simplest path.

### 13. Single-directory output files over XDG spec

**Chosen:** `~/.dreamdecoder_journal.json`  
**Rejected:** `$XDG_DATA_HOME/dreamdecoder/journal.json`, `~/.local/share/dreamdecoder/`  
**Why:** XDG spec is more correct but adds complexity on systems without `$XDG_DATA_HOME` set. The `~/.` prefix is standard for user-level config/data files and works everywhere Unix runs.

### 14. No caching over LRU cache

**Chosen:** Re-read journal file on every command  
**Rejected:** In-memory LRU cache, daemon watcher, SQLite in-memory  
**Why:** The journal file is typically <100KB. Reading from disk takes <5ms. An LRU cache adds complexity for marginal speed gain that would not be user-visible. The journal module is stateless — simpler to reason about and test.

### 15. Comprehensive test coverage over optimistic minimal tests

**Chosen:** Test journal CRUD, search, stats, and model serialization  
**Rejected:** Only testing model construction, skipping persistence tests  
**Why:** The journal file is the most failure-prone component (file I/O, JSON parsing, corruption). Testing save/load/search/delete/clear catches real-world failure modes that model-only tests miss. The trade-off is more test code than application code, which is appropriate for a data-persistence-heavy tool.