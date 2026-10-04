# 🏛️ ClaimCounsel — Multi-Agent Insurance Claims Assistant

**Your personal multi-agent team for navigating insurance claims.**

ClaimCounsel orchestrates 4 specialized AI agents to help everyday people file, track, and manage insurance claims. No more confusing jargon, missed deadlines, or frantic Google searches at 2 AM.

## How It Works

```bash
python main.py --claim-type auto --state CA --incident-date 2026-09-15 \
  --description "Rear-end collision at Main & Oak" --policy policy.pdf
```

## The 4 Agents

| Agent | File | Job |
|-------|------|-----|
| 🕵️ **Policy Parser** | `agents/policy_parser.py` | Reads your insurance policy, extracts coverage details, deductibles, and exclusions. Translates legalese into plain English. |
| 📁 **Document Collector** | `agents/document_collector.py` | Scans your documents, checks what's present vs. what's needed, gives a readiness score. |
| ⏰ **Timeline Tracker** | `agents/timeline_tracker.py` | Knows your state's filing deadlines, calculates days remaining, warns if urgent. |
| ✍️ **Letter Drafter** | `agents/letter_drafter.py` | Writes professional claim letters, appeals, and follow-ups ready to send. |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with CLI
python main.py --claim-type auto --state CA \
  --incident-date 2026-10-01 --description "Fender bender"

# Run with LLM for enhanced analysis (optional)
export LLM_API_KEY="your-key-here"
python main.py --claim-type home --state TX \
  --incident-date 2026-09-20 --description "Roof leak"
```

## Output

After running, you get:

```
~/claimcounsel_data/output/<run_name>/
  ├── claim_counsel_report.json    # Structured data
  └── claim_counsel_report.txt     # Readable report
```

## Supported Claim Types

- 🚗 `auto` — Car accidents, collisions, theft
- 🏠 `home` — Property damage, burglary, natural disasters
- 🏥 `health` — Medical claims, procedure pre-auth
- 💼 `life` — Life insurance claims
- ✈️ `travel` — Trip cancellation, lost baggage, medical abroad

## Architecture

```
┌───────────────────────────────────────┐
│        ClaimCounselOrchestrator       │
├───────────────────────────────────────┤
│                                       │
│  PolicyParser → DocumentCollector →   │
│  → TimelineTracker → LetterDrafter   │
│                                       │
└───────────────────────────────────────┘
```

See [Decisions.md](Decisions.md) for design rationale and [Flow.md](Flow.md) for detailed call chains.

## Requirements

- Python 3.10+
- pip packages: openai, pypdf2, python-dateutil (see requirements.txt)
- Optional: OpenAI-compatible API key for enhanced LLM features

## License

MIT