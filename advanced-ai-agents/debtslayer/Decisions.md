# Decisions.md — DebtSlayer

## Architectural decisions with rejected alternatives

### 1. Multi-agent orchestration pattern
- **Chosen**: Coordinator-agent pattern (single orchestrator with specialist agents)
- **Rejected**: Fully distributed agents (each agent communicating directly), LangGraph graph-based orchestration
- **Why**: Coordinator pattern keeps control flow linear and debuggable. A single `DebtSlayerCoordinator` calls agents in sequence, which avoids deadlocks and circular dependencies inherent in distributed agent topologies. LangGraph was rejected as an external dependency that adds complexity without benefit for a 5-agent system.

### 2. CLI interface vs web app
- **Chosen**: CLI (argparse) with subcommand support
- **Rejected**: FastAPI web server, Gradio/Streamlit UI, Telegram bot
- **Why**: CLI is zero-dependency (only stdlib `argparse`), works headlessly on a VPS, and the target user (Akshat) operates from a terminal. A web UI would require hosting, auth, and a frontend framework — overengineered for a CLI tool.

### 3. Python vs compiled language
- **Chosen**: Python 3.10+
- **Rejected**: Rust, Go, Node.js
- **Why**: Python is already installed on the target VPS, tests run instantly, and the algorithmic complexity (monthly interest calculation, payoff simulation) is trivial. No performance-sensitive code exists. Rust/Go would add compile steps with zero runtime benefit.

### 4. No external API dependencies
- **Chosen**: Pure Python + stdlib
- **Rejected**: OpenAI API (for letter drafting), Plaid API (for transaction syncing), Stripe (for payment simulation)
- **Why**: Zero-API means zero API keys, zero auth, zero rate limits, zero cost. The letter agent uses templates rather than GPT (users can plug in an LLM key later). Plaid would require bank-level auth that's infeasible in a CLI tool. The core value proposition (avalanche vs snowball, payoff timeline) is entirely algorithmic.

### 5. Month-by-month simulation vs analytical formula
- **Chosen**: Iterative month-by-month simulation
- **Rejected**: Closed-form amortization formulas (PMT-derived)
- **Why**: Month-by-month handles variable surplus, debt-specific minimum payments, and the target-priority order (pay off one debt fully before moving to the next). Analytical formulas assume uniform payments across all debts, which the target method does not. Simulation also produces a payment schedule for progress tracking.

### 6. Data model — dataclasses vs Pydantic
- **Chosen**: Python dataclasses with manual `to_json()`/`from_json()`
- **Rejected**: Pydantic models, attrs, TypedDict
- **Why**: Dataclasses are stdlib, zero dependency, and sufficient for the 5 small models. Pydantic adds a dependency and validation overhead that is unnecessary for internal-only data. The manual serialization is explicit and testable.

### 7. Template-based vs LLM-based letter drafting
- **Chosen**: Template matching (heuristic category detection)
- **Rejected**: Full LLM integration (OpenAI/Anthropic API)
- **Why**: Template-based letters work offline, need no API key, and 4 templates (reduced hours, medical, job loss, general) cover ~90% of hardship cases. The architecture is extensible — if `LLM_API_KEY` is set, the `LetterAgent` delegates. This follows the "usable with zero configuration" design goal.

### 8. Test framework — pytest
- **Chosen**: pytest (no external plugins)
- **Rejected**: unittest (stdlib), doctest, hypothesis
- **Why**: pytest gives faster feedback (collect only, verbose output) and the 16 tests run in 0.03s. unittest would work but requires more boilerplate. Hypothesis would be overkill for deterministic financial calculations.

### 9. Project packaging — pyproject.toml
- **Chosen**: Minimal pyproject.toml (setuptools build)
- **Rejected**: Poetry, PDM, setup.py, no packaging (running from source tree)
- **Why**: Minimal `pip install -e .`-compatible setup so tests can import `debtslayer` without `PYTHONPATH` hacks. Poetry/PDM add dependency resolution overhead for a package with zero runtime deps.

### 10. Output format — box-drawing UI
- **Chosen**: Extended ASCII box drawing (╔═╗ etc.) for the inventory table
- **Rejected**: JSON-only output, plain text, rich/colorized output
- **Why**: Box-drawing is terminal-safe (UTF-8), needs no library, and makes the CLI output scannable at a glance. JSON would add a `--json` flag later if needed. Rich/tabulate would add dependencies for a cosmetic improvement.

### 11. Surplus calculation — income minus expenses
- **Chosen**: Simple surplus = income - expenses (after debt minimums are paid)
- **Rejected**: Percentage-of-income rule, 50/30/20 budget allocation, envelope method
- **Why**: The user knows their actual expenses. Guessing a budget allocation would produce unrealistic plans. The spending agent does provide rule-of-thumb tips (expenses > 50% of income → trim subscriptions), but the core calculation uses the user's real numbers.

### 12. Payoff cap at 1200 months
- **Chosen**: Safety limit of 1200 months (100 years) on the simulation loop
- **Rejected**: No limit (infinite loop risk), lower limit (might clip high-surplus plans)
- **Why**: 1200 months is high enough that any real plan completes well before it, but low enough to catch the edge case where minimum payments don't cover interest (debt never paid off). In that case, the system reports "N/A" for interest saved.

### 13. Method selection logic
- **Chosen**: Compare total interest; favor avalanche if it saves ≥5%, otherwise pick based on psychological wins
- **Rejected**: Always avalanche (mathematically optimal), always snowball (behavioral), user choice only
- **Why**: The recommendation is a soft suggestion — the user sees both strategies' numbers. The 5% threshold avoids false precision (a $2 difference is noise), and the fallback favors snowball when interest is nearly identical, because early wins improve adherence.

### 14. Progress tracking — read-only plan file reader
- **Chosen**: Read saved JSON plan and compute progress metrics
- **Rejected**: Stateful database, web dashboard, scheduled reminders
- **Why**: A CLI tool should not manage persistent state. The user saves their plan, runs `progress --plan plan.json` later, and manually enters payments made. This keeps the tool stateless and the data in the user's control. A full tracking solution would need auth, a DB, and push notifications — scope creep for a CLI MVP.

### 15. No `.pytest_cache` in .gitignore (defer to repo root)
- **Chosen**: Rely on the repo root's .gitignore
- **Rejected**: Project-specific .gitignore
- **Why**: The project lives inside LLM-Apps, which already has a `.gitignore`. Adding a second `.gitignore` would create ambiguity. The `.pytest_cache` directory is ephemeral and won't be tracked if the user stages specific paths (which is the recommended workflow).