# FairWheel — Decisions

Architectural and product decisions for the FairWheel car-purchase advisory team (built Oct 15, 2026, rota position 1 — Advanced AI Agents).

## 1. Product: car-purchase advisory over other candidates
**Chosen:** A multi-agent system that answers "should I buy this car?" using NHTSA safety ratings, complaints, recalls, and real fueleconomy.gov MPG.
**Rejected:** Doctor-visit brief (VisitPrep), family emergency planner (HunkerDown), trip planner (TripWise), moving coordinator (MoveMate).
**Why:** A car is most people's second-biggest purchase, made under dealer pressure with zero objective data. Every API needed is a free, zero-auth federal endpoint verified live (200) the same day. Feasibility > value > API availability, and this one wins all three.

## 2. Multi-agent architecture over a single monolithic prompt
**Chosen:** Five specialist agents — Safety Scorer, Grievance Scout, Recall Auditor, Cost Analyst, Deal Reviewer (critic) — coordinated by an orchestrator.
**Rejected:** One LLM call that "does everything"; a simple script that prints API dumps.
**Why:** Each specialist owns one data source and its failure mode; the critic's deterministic weighting is what makes the verdict trustable. The pipeline is honest about which data is live vs simulated per-agency.

## 3. Deterministic critic over LLM judge
**Chosen:** The Deal Reviewer computes a weighted 0-100 score (safety 40%, complaints 30%, recalls 20%, cost 10%) with hard gates (rating < 3 stars → AVOID).
**Rejected:** Sending all findings to an LLM for a judgment call.
**Why:** Reproducible, testable, and zero-cost. An LLM verdict with no fixed rubric could flip-flop between runs for the same car and can't be unit-tested. The LLM adds value on prose, not on hard "buy/no-buy" gates.

## 4. Zero-auth federal APIs over commercial vehicle APIs
**Chosen:** NHTSA SafetyRatings/recalls/complaints + fueleconomy.gov.
**Rejected:** CarFax (paid, gated), Edmunds API (developer key, rate limits), AutoTrader scraping (ToS risk, brittle).
**Why:** No keys, no accounts, no per-call cost, and the data is authoritative government data. All four endpoints verified 200 before the build and again during the smoke test.

## 5. Python + httpx over Node/other
**Chosen:** Python 3 stdlib layout with `httpx` as the only runtime dependency.
**Rejected:** Node/TypeScript (would need a package install chain and separate test tooling).
**Why:** Matches the repo's existing advanced-ai-agents stack (learnerlane, claimcounsel pattern), and `httpx` gives injectable `MockTransport` clients for fully hermetic tests.

## 6. XML parsing via stdlib ElementTree for fueleconomy.gov
**Chosen:** `xml.etree.ElementTree` to parse the fueleconomy.gov REST endpoints (`menu/options` then `/vehicle/{id}`).
**Rejected:** Adding a `requests` + `defusedxml` dependency; regex-scraping the XML.
**Why:** The fuel API is the only non-JSON endpoint; ElementTree is in stdlib, safe for this trusted source, and the two-step lookup (options menu → vehicle id → mpg) was verified live against a 2021 Honda Accord (33 combined mpg).

## 7. Per-agent simulated fallback over hard failure
**Chosen:** Every agent catches `HTTPError` and returns deterministic simulated data, flagged `source="simulated"`.
**Rejected:** Aborting the whole pipeline on any single API failure; empty results.
**Why:** The report always ships, and the provenance flag keeps the user honest about what's real. Simulated data is seeded by a hash of make/model so it's stable across runs — testable and demoable without network.

## 8. Injectable client (`set_client`) over monkeypatching
**Chosen:** A module-level `_client` with `set_client(client)` setter; agents read it via `api.get_json`/`get_text`.
**Rejected:** `unittest.mock.patch` on httpx internals; building a fake HTTP server in tests.
**Why:** This is the repo's established testability pattern (per python-project-build skill). Tests inject `httpx.Client(transport=MockTransport(...))` — no network, no live server, deterministic.

## 9. CLI-first over web app
**Chosen:** `python -m fairwheel` with flags (`--year --make --model --budget ...`), interactive prompts when vehicle args are missing, `--output` for markdown files, `--demo` to force simulation.
**Rejected:** Streamlit/FastAPI web UI.
**Why:** The rota category is Advanced AI Agents, and the repo's agents are CLI-first. A web UI adds a server, port, and deploy step for zero functional gain on the "should I buy this car?" question.

## 10. Fuel cost math is deterministic arithmetic
**Chosen:** `annual_miles / combined_mpg * fuel_price * 5` computed in `CostReport.compute_fuel_costs`.
**Rejected:** Asking an LLM to estimate fuel cost.
**Why:** It's a closed-form calculation; grounding the report in real MPG data makes it verifiable and unit-testable to the cent. The 5-year horizon matches typical ownership windows.

## 11. Negotiation talking points baked into the critic
**Chosen:** The Deal Reviewer emits concrete talking points — open recall campaign numbers (free-fix leverage), complaint-cluster dealer questions, fuel-cost price anchors, budget-blowout anchors.
**Rejected:** A bare score with no actionability.
**Why:** The user's real goal is walking into a dealership armed. Deterministic talking points are the highest-value output and they're tested (`test_deal_reviewer_recall_leverage`).

## 12. Scored complaint themes over raw complaint dump
**Chosen:** Grievance Scout clusters complaints by component (Counter over the `components` field), caps at 400 items, returns top 6 themes with a sample summary.
**Rejected:** Rendering every complaint verbatim (a 2021 Accord had 241 complaints — too long for a one-page brief).
**Why:** One-page report constraint. Clustering turns a 250KB JSON dump into "Electrical System: 66 complaints" — immediately useful, LLM-free.

## 13. Hard gates take precedence over weighted score
**Chosen:** Safety rating < 3 stars forces AVOID regardless of score; the gate reason is appended and tested.
**Rejected:** Letting complaints/recalls/cost math override a terrible crash rating.
**Why:** A car that fails to protect its occupants is not a good deal at any price. This is a product-safety decision, not a statistical one.

## 14. Repo placement: `advanced-ai-agents/fairwheel/`
**Chosen:** Standalone package under the category directory in LLM-Apps, matching learnerlane's layout (`fairwheel/` package inside the project dir).
**Rejected:** New standalone GitHub repo (fine-grained PAT lacks repo-creation scope — known constraint); `extensions/` (wrong category).
**Why:** Rota position 1 is Advanced AI Agents; the directory convention is already established and the README table of contents links per-category.

## 15. Report rendered as markdown, not fancy UI
**Chosen:** `render_markdown()` producing a one-page structured brief, printed to stdout or written via `--output`.
**Rejected:** HTML/PDF generation (extra deps), terminal ANSI styling (harder to copy into notes).
**Why:** Markdown is universally useful — paste into notes, share, print. Matches the repo's README-first documentation style.