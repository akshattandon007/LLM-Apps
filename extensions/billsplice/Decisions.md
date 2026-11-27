# Decisions.md — BillSplice

Architectural decisions with rejected alternatives.

## 1. CLI-only vs Web UI / TUI

- **Chosen:** CLI (argparse + interactive input)
- **Rejected:** Web UI (Flask/HTML) — overkill for a utility; adds deployment + browser dependency. Text-based TUI (rich/prompt_toolkit) — too heavy for a single-purpose tool; `input()` calls keep it zero-dependency.
- **Why:** A bill splitter is a 30-second interaction. A full UI wastes time.

## 2. Pure Python vs external deps (click, typer)

- **Chosen:** stdlib only (`argparse`)
- **Rejected:** Click/Typer/rich — they'd be the only dependencies. For a 300-line utility, shipping with zero `pip install` requirements wins.
- **Why:** `pip install -e .` on a fresh machine works instantly. No dependency resolution, no conflicts.

## 3. Interactive wizard vs flags-only

- **Chosen:** Both — interactive as default, `--quick` for scripting
- **Rejected:** Flags-only (too verbose for one-off use) or interactive-only (can't automate/alias)
- **Why:** Casual users want the wizard; power users want `--quick`. Supporting both costs ~50 lines.

## 4. Decimal vs float for money

- **Chosen:** `decimal.Decimal`
- **Rejected:** `float` (1.1 + 2.2 ≠ 3.3 — floating-point arithmetic loses pennies on tax/tip calculations)
- **Why:** Money must be exact. Decimal with 2-place rounding is the standard.

## 5. Per-person items vs "who had what" as a separate step

- **Chosen:** Items entered first, then assigned to people in a second step
- **Rejected:** Inline syntax like "Alice:Steak,45.00" — fragile, harder to parse, no easy correction path. Tagged items at entry time — requires knowing everyone's name before you've thought of it.
- **Why:** A two-phase flow mirrors how real bill-splitting works: list all items first, then figure out who had what.

## 6. Shared items via trailing `!` suffix vs separate command

- **Chosen:** Trailing `!` on the item name, e.g. `Fries,8.00!`
- **Rejected:** Separate "add shared item" prompt — adds UI complexity; "shared" flag typed post-entry — extra keystrokes. The `!` is intuitive (common in CLI tools) and unambiguous.
- **Why:** Minimal typing, maximal clarity.

## 7. Tax/tip as percentage vs fixed amounts

- **Chosen:** Percentage input (converts to amount internally)
- **Rejected:** Fixed-amount input — less common in restaurant billing (tax and tip are % of subtotal). Both supported internally (amounts are Decimal); UX asks for %.
- **Why:** Percentage matches how every restaurant presents tax and tip. Users type `8.875` not `$6.57`.

## 8. Proportional tax/tip vs equal split

- **Chosen:** Tax and tip prorated by each person's fraction of the subtotal
- **Rejected:** Equal split — Alice who had the $45 steak shouldn't pay the same tax as Bob who had $22 pasta. Per-person fixed split — some groups split tax/tip equally regardless. Default proportional is fairer; can override if needed.
- **Why:** Proportional is the mathematically fairest default.

## 9. One-file CLI vs module package structure

- **Chosen:** Package (`billsplice/` with `models.py`, `splitter.py`, `cli.py`)
- **Rejected:** Single `billsplice.py` — keeps things simple but makes unit testing harder (import side effects). Package structure separates concerns cleanly.
- **Why:** `tests/` can import `billsplice.splitter` without pulling in the CLI. Cleaner test isolation.

## 10. `pyproject.toml` vs `setup.py`

- **Chosen:** `pyproject.toml` (PEP 621 modern standard)
- **Rejected:** `setup.py` — deprecated style; `setup.cfg` — fewer IDE tooltips. `pyproject.toml` is the 2026 standard.
- **Why:** `pip install -e .` works identically; `pyproject.toml` is more readable and future-proof.

## 11. `__init__.py` empty vs re-exporting

- **Chosen:** Empty `__init__.py` (namespace only)
- **Rejected:** Re-exporting `split_bill`, `Bill`, etc. — creates circular import risk and makes traceability harder. Direct `from billsplice.splitter import split_bill` is explicit.
- **Why:** Explicit > implicit. Zen of Python.

## 12. ROUND_HALF_UP vs BANKER's rounding

- **Chosen:** `ROUND_HALF_UP` (standard rounding taught in school)
- **Rejected:** `ROUND_HALF_EVEN` (banker's rounding) — less intuitive for normal users. Money rounding in restaurants always rounds 0.005 up.
- **Why:** Users expect $1.005 to round to $1.01, not $1.00.

## 13. Handling edge cases (empty bill, no people, zero subtotal)

- **Chosen:** Early return / guard clauses in `split_bill()`
- **Rejected:** Letting arithmetic happen and catching ZeroDivisionError — masks bugs. Early returns make intent clear.
- **Why:** Defensive programming. Zero people or zero items = no valid split.

## 14. Test strategy — pure logic tests only

- **Chosen:** Unit tests on `split_bill()` with various bill configurations
- **Rejected:** CLI integration tests (subprocess) — fragile, slow, test the framework not the logic. Snapshot tests — overkill for deterministic math.
- **Why:** The core value is correct arithmetic. If `split_bill()` works, the CLI works. 9 test cases cover normal, edge, and degenerate cases.