# Decisions.md

## Architectural Decisions for TabCalc

### 1. CLI tool vs. web app
- **Chosen:** CLI tool (Python entry point with argparse)
- **Rejected:** Flask/FastAPI web app, Tkinter GUI
- **Why:** Extensions category demands lightweight standalone utilities. A web app would require a running server, port management, and a browser — overkill for a "split expenses" tool. CLI is instant, composable, and pipeable.

### 2. Pure stdlib vs. external packages
- **Chosen:** Pure Python stdlib only (`argparse`, `decimal`, `json`, `pathlib`)
- **Rejected:** click/typer (CLI frameworks), pandas (data manipulation)
- **Why:** Zero-install wins for a utility meant to be run anywhere. `argparse` handles all CLI needs here. `Decimal` is already stdlib and avoids floating-point rounding errors with money.

### 3. `Decimal` vs. `float` for monetary amounts
- **Chosen:** `decimal.Decimal`
- **Rejected:** `float`
- **Why:** Floating-point arithmetic introduces rounding errors (0.1 + 0.2 != 0.3). Money calculations require exactness. `Decimal` with quantize rounds predictably to the cent.

### 4. Greedy settlement algorithm vs. linear programming
- **Chosen:** Greedy (sort by balance, match biggest creditor with biggest debtor)
- **Rejected:** Linear programming (e.g., simplex) for provably minimal transfers
- **Why:** The greedy algorithm produces the minimum *number* of transfers for the vast majority of real-world cases (it's a well-known result for the debt-settlement problem). LP would require external libraries (`scipy`, `pulp`). Greedy is O(n log n), buildable in 20 lines, and produces correct results.

### 5. One-line-per-expense format vs. JSON/YAML/CSV input
- **Chosen:** Delimited text format (`description | paid_by | amount | person1,person2,...`)
- **Rejected:** JSON input file, CSV, YAML, XML
- **Why:** The pipe-delimited line format is the fastest to type by hand — no brackets, no quotes (unless needed), no indentation. It maps 1:1 to how people think: "Dinner | Alice | 45 | Alice,Bob,Charlie". JSON is supported via `--json` output only.

### 6. Module separation: `core.py` vs. `cli.py`
- **Chosen:** Split into `core.py` (pure logic, no I/O) and `cli.py` (parsing, formatting, entrypoint)
- **Rejected:** Single monolithic file
- **Why:** Separating business logic from I/O makes `core.py` testable without mocking stdin/stdout. It also allows `core.py` to be imported by other tools (e.g., a future web frontend).

### 7. Interactive stdin mode vs. always require flags
- **Chosen:** If no `-f` or `-e` flags given, read from stdin interactively
- **Rejected:** Requiring explicit flags in all cases
- **Why:** The most common use case is "type expenses right now" — stdin mode matches the mental model of a quick calculation. Flags are for batch/scripted use.

### 8. Comment lines (`#`/`//`) in expense files
- **Chosen:** Support both `#` and `//` as comment prefixes
- **Rejected:** No comments, or comments only in specific format
- **Why:** Expense files benefit from context ("# Weekend trip"). Supporting both comment styles reduces friction — people naturally use whichever they're used to.

### 9. JSON output vs. only human-readable text
- **Chosen:** Support both via `--json` flag
- **Rejected:** Human-readable only, or JSON-only
- **Why:** Human-readable output is the primary use case. JSON output enables piping into scripts, dashboards, or saving to files for record-keeping. The flag keeps the default clean while enabling programmatic use.

### 10. Negative balance = owes money convention
- **Chosen:** Negative balance = person owes money; positive = person is owed money
- **Rejected:** Reverse convention (negative = due to receive)
- **Why:** Aligns with standard accounting and banking — a negative balance on a statement means you owe. This makes the output intuitive without explanation.

### 11. `tabcalc` as both module and runnable script
- **Chosen:** `python -m tabcalc.cli` and installable via pip
- **Rejected:** Only installable, or only run via script path
- **Why:** Installing via pip gives a global `tabcalc` command. Running via `python -m` works without install for development. Supporting both covers all workflows.

### 12. `quantize` to 2 decimal places throughout
- **Chosen:** Round all monetary values to $0.01 via `Decimal.quantize`
- **Rejected:** Raw `Decimal` precision, truncation, banker's rounding
- **Why:** Users expect dollars and cents. `quantize` with default rounding (ROUND_HALF_EVEN) handles three-way splits predictably. Raw precision would display ".33333..." which is confusing.

### 13. Single settlement plan vs. per-person breakdown
- **Chosen:** Single aggregate plan with all balances and transfers
- **Rejected:** Individual per-person reports, multiple settlement options
- **Why:** A group wants one answer — "who pays whom how much." Multiple options would cause confusion. The minimum-transfer output is definitive.

### 14. Tests use `pytest` vs. unittest
- **Chosen:** pytest
- **Rejected:** unittest (stdlib)
- **Why:** pytest is the de facto standard for Python testing. Its fixture system, parameterization, and concise assertion syntax make tests more readable. While it's an external dependency for testing, it's not a runtime dependency.