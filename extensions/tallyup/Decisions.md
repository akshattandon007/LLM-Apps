# Decisions.md

## Why each design decision was made and what was rejected

### 1. CLI over GUI
**Chosen:** Command-line interface via argparse.
**Rejected:** GUI (Tkinter / web app) — adds complexity, requires more dependencies, and the target user is comfortable with terminal tools. CLI is fastest to build and simplest to maintain.

### 2. JSON file storage over SQLite
**Chosen:** JSON file at `~/.tallyup/expenses.json`.
**Rejected:** SQLite — more setup, schema migrations, heavier dependency. For expense data (typically <100 records per trip) JSON is perfectly adequate and human-readable.

### 3. Greedy debt settlement over optimal minimum-transaction
**Chosen:** Greedy algorithm — sort creditors by amount descending, match largest debtor to largest creditor.
**Rejected:** Max-flow/min-cost optimization — mathematically optimal but over-engineered for everyday use. The greedy approach produces ≤ N-1 transactions for N people, which is well within an acceptable range for casual users.

### 4. Decimal over float
**Chosen:** Python's `Decimal` type for all monetary calculations.
**Rejected:** `float` — floating point rounding errors (e.g., $10.00 / 3 = $3.333333...) would cause phantom pennies. Decimal gives precise rounding control.

### 5. argparse over click/typer
**Chosen:** Standard library `argparse`.
**Rejected:** `click` / `typer` / `rich` — additional dependencies. argparse comes with Python, has no install cost, and is sufficient for a utility with 5 commands.

### 6. Payer-in-participants convention
**Chosen:** The payer must be listed in `--split-with` to split the cost with them.
**Rejected:** Auto-including the payer — would break cases where the payer is treating others (not splitting). Explicit is better than implicit for financial tools.

### 7. Single file for expense data, not per-trip
**Chosen:** One `expenses.json` for all expenses across all trips.
**Rejected:** Per-trip files / tags / sessions — adds UI complexity. A `tallyup clear` command resets for the next trip. Users who need multiple concurrent groups can use `--file` to specify a custom path.

### 8. UUID short IDs for expenses
**Chosen:** 8-character hex IDs for each expense.
**Rejected:** Sequential integers — fragile when items are deleted. Short UUIDs are unique without central coordination.

### 9. Settlement rounding at $0.01
**Chosen:** Transfers below $0.01 are discarded.
**Rejected:** Round everything to nearest dollar — too imprecise for large groups. Retaining cents ensures accuracy while discarding sub-penny amounts avoids noise.

### 10. No authentication / no accounts
**Chosen:** Fully local, zero accounts.
**Rejected:** Multi-user sync / cloud storage — violates the "zero-auth" principle. For group trips, one person runs the tool and shares the output.

### 11. `--split-with` as space-separated list
**Chosen:** `tallyup add -d Dinner -a 42 -p Alice -s Alice Bob Carol`
**Rejected:** CSV format `--split-with Alice,Bob,Carol` — argparse nargs="+" is more natural for CLI. CSV feels "wrong" for person names.

### 12. Positive balances = owed money
**Chosen:** Positive balance means "you are owed this much," negative means "you owe."
**Rejected:** Reverse convention — would cause confusion. The sign convention is explained in the summary output.

### 13. No edit/delete expense commands (v1)
**Chosen:** Only add, list, settle, clear, summary.
**Rejected:** Edit/delete — increases scope significantly for v1. Users can clear and re-add if they make a mistake. Edit/delete can be added in v2.

### 14. Report format: visual separator + ordered sections
**Chosen:** A boxed report with expense list, then settlement list, then total.
**Rejected:** JSON-only output — the report is meant to be shared in a group chat. A human-readable, screenshot-ready format is the primary output. JSON can be added as `--json` later.