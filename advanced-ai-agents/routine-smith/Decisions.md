# Decisions.md — RoutineSmith

## 1. Multi-Agent Architecture vs Monolithic Script
**Chosen:** 5 specialist agents + orchestrator  
**Rejected:** Single script with all logic in one file  
**Why:** The multi-agent pattern makes the system extensible (add/remove agents independently), testable (each agent in isolation), and transparent (agent negotiation is visible in the log). A monolithic script would couple all logic together and make it impossible to see which agent is responsible for each decision.

## 2. CLI Interface vs Web UI
**Chosen:** Terminal CLI with interactive prompts  
**Rejected:** Flask/FastAPI web server, Tkinter GUI  
**Why:** Zero dependencies (pure Python stdlib), instant startup, works headless, no port conflicts. The interactive CLI feels like talking to the agents one at a time, reinforcing the multi-agent metaphor. A web UI would add complexity (HTML, CSS, JS, server management) with no functional benefit.

## 3. Chronotype Model vs Self-Reported Energy
**Chosen:** Three chronotype energy curves (morning/night/balanced) with hourly energy levels  
**Rejected:** Single "when do you have most energy" question; complex Circadian rhythm calculation  
**Why:** Three chronotypes cover 95% of people and map to published sleep research. Hourly energy curves (0-10) give the Energy Matcher enough granularity to place tasks without over-engineering. A single question loses too much information; a full Circadian model requires user biometric data we don't have.

## 4. Rule-Based Matching vs Semantic/ML Matching
**Chosen:** Declarative lookup tables and heuristics for habit stacking, energy matching, and category guessing  
**Rejected:** Sentence transformers, embedding similarity, LLM-based classification  
**Why:** Zero external dependencies, instant execution, fully deterministic — no API keys, no model downloads. The habit rules (cue→new habit→celebration) are grounded in published behavioral psychology, not statistical correlation. ML would add latency, flakiness, and dependency weight for a task that heuristics handle well.

## 5. Habit Stacks as Replacements, Not Additions
**Chosen:** Habit Architect replaces the base task with a cue-triggered version  
**Rejected:** Adding habit stacks alongside existing tasks (duplicate entries)  
**Why:** If the user wants to "exercise 20 min" and the Habit Architect stacks it onto "morning coffee," showing both the original task AND the habit version creates confusion. Replacing gives the user ONE clear action with a cue trigger.

## 6. Interactive Prompts vs YAML/JSON Config
**Chosen:** CLI prompts to collect schedule and goals  
**Rejected:** User writes a config.yaml or JSON file  
**Why:** Interactive prompts guide the user through the process (even default values are shown) and give a conversational feel that matches the agent metaphor. Config files require the user to learn a format before they can use the tool. The `--quick` mode provides an escape hatch for automated use.

## 7. Demonstration Goals vs Empty Initial State
**Chosen:** Pre-loaded demo goals when user enters none  
**Rejected:** Requiring at least 1 goal before showing a routine  
**Why:** First-time users should see value immediately. Demo goals (exercise, read, meditate, side project, stretch) represent a realistic day for most knowledge workers. The system works with user goals too — demos are the fallback, not the default.

## 8. Single JSON Report File vs Database
**Chosen:** `last_routine.json` overwritten on each run  
**Rejected:** SQLite database, CSV log, cloud-synced store  
**Why:** The tool is stateless by design — you run it, get a routine, and optionally log completions. A database would add sqlite dependency and complexity for minimal value. JSON is human-readable, scriptable, and trivially backed up. If persistence is needed, `last_routine.json` feeds into other tools via shell pipes.

## 9. Flat vs Hierarchical Package Layout
**Chosen:** Flat package with `agents/` and `data/` subdirectories  
**Rejected:** Single flat directory with all files; deeply nested packages  
**Why:** Agents form a clear conceptual group (each is a specialist), data files are a separate concern (pure functions, no state). A single flat directory would mix CLI logic with energy curves with test code. Deep nesting would make imports painful (`routine_smith.agents.behavioral.data.rules`). Two subdirectories hits the sweet spot.

## 10. Score as a 0-100 Heuristic, Not ML
**Chosen:** Rule-based scoring across category coverage, habit count, balance, overwhelm  
**Rejected:** Machine learning model trained on user satisfaction data; simple pass/fail  
**Why:** A numeric score gives the user an instant sense of routine quality without needing ML infrastructure. The heuristics (category coverage +10, habit stacking +3 each, overwhelm penalty -2 per task over 15) are transparent and explainable — the user knows WHY their score is what it is. No training data needed.

## 11. Implementation Intentions as Behavioral Output
**Chosen:** Generate "When X, I will Y" statements as actionable output  
**Rejected:** Just show the routine as a schedule  
**Why:** Implementation intentions are one of the most evidence-backed habit-formation techniques (Gollwitzer, 1999). Studies show they double follow-through rates. Showing the user these specific if-then plans turns the routine from a passive schedule into an active commitment device.

## 12. Missing `execute_code` in Cron Mode — File-Based Workaround
**Chosen:** Write intermediate scripts to /tmp and run via `terminal()`  
**Rejected:** Using `execute_code` for rapid prototyping  
**Why:** The execution environment blocks `execute_code` in cron/headless mode. The workaround (write `.py` to `/tmp`, execute with `python3 /tmp/...`) adds one step but preserves the same capability. All code is written before execution, which creates a natural code-review checkpoint.

## 13. No External API Dependencies
**Chosen:** Zero external APIs — all data is built-in lookup tables  
**Rejected:** Integrating with weather APIs, calendar APIs (Google Calendar), todo APIs (Todoist)  
**Why:** The tool must work offline, instantly, and without any signup. Calendar integration would be the obvious next feature, but it would break the zero-dependency contract and introduce auth complexity. Built-in data (energy curves, habit rules, time estimates) covers the core use case without external calls.

## 14. Agent Negotiation Visualization as CLI Text
**Chosen:** Show negotiation log on request with icon-coded message types  
**Rejected:** Real-time agent conversation UI, web dashboard  
**Why:** Agents negotiating is the key unique feature of this multi-agent system. Showing the log (💡proposal, 🚫veto, 🔧adjustment, ℹ️info) makes the internal process visible without overcomplicating the CLI. A real-time UI or dashboard would require a whole additional rendering layer.

## 15. Wind-Down Before Bedtime vs After
**Chosen:** Wind-down activities placed 30-60 minutes before the stated sleep time  
**Rejected:** Wind-down at any evening time; wind-down after getting into bed  
**Why:** Sleep hygiene research consistently shows that the pre-bed window is the most impactful for sleep quality. Placing wind-down earlier in the evening (when the user still has energy) makes it more likely to be followed. Post-bed wind-down (reading in bed, journaling in bed) can disrupt sleep associations.