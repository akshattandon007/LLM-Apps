# 📄 Clarity — Legal Document Clarity Analyzer

> **Three AI agents work together to demystify legal documents. Extract clauses, translate to plain language, and assess risk — before you sign.**

![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![Multi-Agent](https://img.shields.io/badge/architecture-multi--agent-orange)

---

## 🚀 What It Does

Clarity takes any legal document (contract, terms of service, lease, insurance policy, NDA) and runs it through a **three-agent pipeline**:

| Step | Agent | What It Does |
|------|-------|-------------|
| 1️⃣ | **Clause Extractor** | Identifies every distinct clause — payment terms, renewal conditions, liability limits, dispute resolution, etc. |
| 2️⃣ | **Plain Language Translator** | Rewrites each clause in simple English (6th-grade reading level) — "indemnify" → "protect from loss" |
| 3️⃣ | **Risk Advisor** | Flags unfair terms, auto-renewal traps, hidden fees, binding arbitration, and generates questions to ask before signing. |

No more signing what you don't understand. ✊

---

## 🎯 Who It's For

- **Non-technical people** who sign contracts, leases, terms of service
- **Freelancers** reviewing client agreements
- **Tenants** checking lease terms
- **Consumers** understanding insurance policies and warranties
- **Anyone** who's ever said "I'll read it later" and never did

---

## 🛠️ Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run with a file
python3 main.py --file sample_contract.txt

# 3. Run with inline text
python3 main.py --text "The Lessee agrees to indemnify and hold harmless..."

# 4. Interactive mode (paste your document)
python3 main.py --interactive
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--file`, `-f` | Path to a text file containing the document |
| `--text`, `-t` | Document text as a string |
| `--interactive`, `-i` | Paste document text interactively |
| `--api-key` | LLM API key (default: `LLM_API_KEY` env var) |
| `--model` | LLM model to use (default: `gpt-4o-mini`) |
| `--output`, `-o` | Save report to file |
| `--json` | Output as JSON only |

---

## 📋 Example Output

```
🔍 Clarity — Analyzing your document...

  Step 1/3: Extracting clauses...
  → Found 6 clause(s)

  Step 2/3: Translating to plain language...
  → Translated 6 clause(s)

  Step 3/3: Assessing risk...
  → Risk assessment complete

📋 Document contains 6 clause(s) analyzed.
⚠️  2 high-risk clause(s) — requires your attention.
🔶 1 medium-risk clause(s) — review recommended.
✅ 3 low-risk clause(s).

🔴 Clause 2: Auto-Renewal (80% risk)
  "This agreement automatically renews unless you give 30 days notice."
  🚩 auto_renewal — Traps you in recurring commitment.

🔴 Clause 3: Binding Arbitration (90% risk)
  "You give up your right to sue in court. All disputes go to private arbitration."
  🚩 binding_arbitration — You waive jury trial rights.

🏁 Overall: ⚠️ CAUTION — One high-risk clause detected. Review carefully.
```

---

## 🧪 Running Tests

```bash
python3 -m pytest tests/ -v
```

Or directly:
```bash
python3 tests/test_clarity.py
```

---

## 🏗️ Architecture

```
main.py
  └── Orchestrator
        ├── ClauseExtractor   → extract clauses from document
        ├── PlainTranslator   → rewrite in plain language
        └── RiskAdvisor       → assess risk & flag issues
              └── Report (Markdown / JSON)
```

Each agent runs independently and can use either:
- **LLM-powered** extraction/translation (requires API key — richer results)
- **Rule-based** fallback (no API key needed — works offline)

---

## 📦 Requirements

- Python 3.8+
- `openai` (optional — for LLM-powered analysis)
- No other external dependencies for rule-based mode

---

## 🔮 Roadmap

- [ ] PDF support (extract text from scanned documents)
- [ ] Web UI (paste document in a browser)
- [ ] Document comparison (what changed vs. last version)
- [ ] Support for more languages
- [ ] Batch processing (multiple documents)

---

## ⚖️ Disclaimer

Clarity is a **tool for understanding**, not a substitute for professional legal advice. Always consult a qualified attorney for important legal decisions.
