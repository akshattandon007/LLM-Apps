# 🚇 CommuteCrafter

**Your commute is 22 minutes. Here's exactly 22 minutes of things worth reading.**

Most content is sold in fixed doses — a 47 minute podcast, a 3,000 word essay — and your commute is an arbitrary number of minutes that ends whether you're finished or not. CommuteCrafter inverts that: tell it how long you're moving, and it assembles a plan that **fits the window to within 90 seconds**, paced like a good radio show: light warm-up, deep middle, gentle landing.

No API keys. No accounts. No "sign in to continue".

```bash
$ commutecrafter plan -m 22 -i history,philosophy --transport train

╭───── CommuteCrafter ──────╮
│  window  22 min (22:00)   │
│ planned  22.0 min (22:00) │
│    mode  read · train     │
│  status  ✔ fits  (+0s)    │
╰───────────────────────────╯

☕ WARM-UP  ·  budget 3:58
  1   4:03  The Prophet, On Work                       gutenberg
  2   1:24  Large Synoptic Survey Telescope            arxiv

🧠 CORE  ·  budget 13:38
  1  17:05  History of computer science                wikipedia
  2   4:52  History of political science  [39%]        wikipedia

🌙 WIND-DOWN  ·  budget 4:24
  1   2:35  Ask HN: Best way to learn a city on foot?  hackernews
```

Note the `[39%]`. CommuteCrafter doesn't pad your commute with content you can't finish and doesn't leave nine minutes of dead air. It tells you to read 39% of that article and where the time goes.

## ✨ What it actually does

- 🕐 **Fits the window** — plans land within ±90s (configurable) of your real commute length
- 🎭 **Three-act pacing** — warm-up (18%) → core (62%) → wind-down (20%), so you arrive composed instead of mid-sentence
- 📏 **Real word counts** — fetches the actual article text from Wikipedia, so "17 minutes" means 3,897 words at 230 wpm, not a guess from file size
- ✂️ **Honest partials** — when nothing fits, it trims the last item and labels the fraction
- 🌦️ **Weather-aware** — raining or freezing? It switches to audio/wind-down pacing. Cycling or driving? Audio only, obviously
- 🔁 **Never repeats itself** — a local SQLite memory keeps yesterday's articles out of today's plan
- 🎧 **Read *or* listen** — 230 wpm reading / 150 wpm narration, so the same article is 17 minutes read or 26 minutes listened
- 🔌 **Zero API keys** — every source is public and keyless
- 📦 **JSON output** — `--json` for piping into your own tooling

## 📦 Install

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/ai-agents/commutecrafter
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
commutecrafter plan -m 22 -i history
```

## 🚀 Usage

### The basics

```bash
# 22 minute train ride, you're into history and philosophy
commutecrafter plan -m 22 -i history,philosophy --transport train

# 40 minute drive — audio only, weather included
commutecrafter plan -m 40 -i technology,economics --transport drive --city Mumbai

# 11 minute walk, force audio mode
commutecrafter plan -m 11 -i science --mode listen

# Machine-readable
commutecrafter plan -m 18 -i design --json
```

### Options that matter

| Flag | What it does |
|---|---|
| `-m, --minutes` | Your commute length in minutes (2–240) |
| `-i, --interests` | Comma-separated topics — `history,tech,philosophy` |
| `--transport` | `walk` `train` `drive` `cycle` `bus` — sets read vs listen |
| `--mode` | Force `read`, `listen` or `either` |
| `--city` | Adds live weather (Open-Meteo) and lets weather pick the mode |
| `--tolerance` | Seconds of acceptable overshoot (default 90) |
| `--offline` | Use the bundled 44-item corpus, no network at all |
| `--json` | Emit the full plan as JSON |

### Other commands

```bash
commutecrafter search "roman engineering"        # see what's available
commutecrafter search "stoicism" --source gutenberg
commutecrafter sources                            # list content sources
commutecrafter history                            # your last plans
commutecrafter stats                              # cache size
commutecrafter clear                              # forget served items
```

### What it pulls from

| Source | What you get | Key needed |
|---|---|---|
| **Wikipedia** | Full-article plaintext with real word counts | none |
| **arXiv** | Research abstracts — the deep-dive segment | none |
| **Hacker News** | Ask HN threads (real long-form prose) | none |
| **Project Gutenberg** | Public-domain classics, first ~6,000 words | none |
| **Open-Meteo** | Weather for mode selection (`--city`) | none |

Every source is best-effort: if arXiv is down, you still get a plan. If every live source fails, it falls back to the bundled corpus rather than erroring out.

### Add an LLM (optional)

Set a key and each item gets a one-sentence "why this, why now" instead of the numeric template:

```bash
export OPENROUTER_API_KEY=sk-or-...
commutecrafter plan -m 22 -i history --explain
```

Everything works without it — the LLM only adds colour, never correctness.

## 🧪 Tests

```bash
python3 -m pytest -q
```

```
103 passed in 0.35s
```

The suite is hermetic: **no network calls, no real user cache**. Coverage includes

- `test_timing.py` — word/second conversion, inverse round-trip, pacing budgets summing exactly to the window
- `test_planner.py` — fits 8/11/15/22/30/45/60 minute windows, source diversity, determinism, exclusion of served items, graceful degradation on empty and single-item pools
- `test_sources.py` — all four parsers against fixtures (Wikipedia JSON, arXiv Atom, HN Algolia, Gutenberg boilerplate)
- `test_weather.py` — the full transport × weather decision table
- `test_store.py` — SQLite schema, history ordering, served-memory window expiry, idempotent writes
- `test_cli.py` — end-to-end CLI runs on the offline corpus, including JSON schema and history persistence

## 🏗️ How it fits together

```
cli.py           argparse → gather → weather → plan → render/persist
planner.py       three-act budget → best-fit per act → pad/trim to tolerance
timing.py        words ⇄ seconds, pacing profiles (pure, no I/O)
sources/         wikipedia · arxiv · hackernews · gutenberg (each: parse + fetch)
weather.py       Open-Meteo geocode + current conditions, mode decision table
store.py         SQLite: plan history + "already served" URLs
render.py        rich tables, JSON
llm.py           optional one-line explanations with template fallback
```

See [`Flow.md`](./Flow.md) for function-level call chains and [`Decisions.md`](./Decisions.md) for why each of these choices beat the alternatives.

## 🩺 Limitations, stated honestly

- Wikipedia and arXiv give you text, not audio — `--mode listen` plans by narration speed but you supply the TTS
- arXiv abstracts are short, so they serve as short deep-dives, not hour-long listens
- Commute *variability* is not modelled — a 22 minute plan assumes 22 minutes, not "22, plus the 6 you spend waiting"
- Partial items are instructions ("read 39%"), not enforced cuts

## 📄 License

MIT — same as the rest of this repo.
