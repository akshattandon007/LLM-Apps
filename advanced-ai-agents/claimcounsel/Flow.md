# Flow.md — ClaimCounsel

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                   ClaimCounselOrchestrator                │
│                   (main.py / run_full_pipeline)          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. PolicyParserAgent    ─── policy_parser.py            │
│  2. DocumentCollectorAgent ─── document_collector.py     │
│  3. TimelineTrackerAgent ─── timeline_tracker.py         │
│  4. LetterDrafterAgent   ─── letter_drafter.py           │
│                                                          │
│  Shared: config.py, utils/llm_utils.py, file_utils.py   │
└──────────────────────────────────────────────────────────┘
```

## Pipeline Execution Order

```
main() / CLI
  │
  ▼
ClaimCounselOrchestrator.run_full_pipeline()
  │
  ├── [Agent 1] PolicyParserAgent.parse_policy()
  │   ├── file_utils.extract_pdf_text()      # For PDFs
  │   ├── file_utils.read_text_file()        # For .txt/.md
  │   └── llm_utils.LLMClient.extract_json()  # Policy → structured data
  │
  ├── [Agent 1b] PolicyParserAgent.summarize_in_plain_english()
  │   └── llm_utils.LLMClient.chat()          # Jargon → plain English
  │
  ├── [Agent 2] DocumentCollectorAgent.assess_readiness()
  │   ├── file_utils.list_claim_files()       # Scan directory
  │   ├── file_utils.read_all_texts()         # Read all documents
  │   ├── config.CLAIM_TYPE_DOCUMENTS         # Get requirements
  │   └── llm_utils.LLMClient.extract_json()  # Assess readiness
  │
  ├── [Agent 2b] DocumentCollectorAgent.generate_checklist()
  │   └── config.CLAIM_TYPE_DOCUMENTS         # Format checklist
  │
  ├── [Agent 3] TimelineTrackerAgent.calculate_timeline()
  │   ├── config.CLAIM_DEADLINES              # State deadline lookup
  │   ├── datetime math                       # Deadline calculation
  │   └── llm_utils.LLMClient.extract_json()  # Enriched analysis
  │
  ├── [Agent 3b] TimelineTrackerAgent.get_next_steps()
  │   └── Conditional logic based on days_remaining
  │
  ├── [Agent 4] LetterDrafterAgent.draft_initial_claim()
  │   └── llm_utils.LLMClient.chat()          # Formal letter
  │
  ├── file_utils.write_json_file()            # Save structured report
  └── file_utils.write_text_file()            # Save readable report
```

## Module Dependency Graph

```
main.py
  ├── config.py                    (no deps)
  ├── utils/file_utils.py          (os, json, pathlib)
  ├── utils/llm_utils.py           (openai, config)
  ├── agents/policy_parser.py      (utils/llm_utils, utils/file_utils)
  ├── agents/document_collector.py (utils/llm_utils, utils/file_utils, config)
  ├── agents/timeline_tracker.py   (utils/llm_utils, config)
  └── agents/letter_drafter.py     (utils/llm_utils)
```

## Data Flow Between Agents

```
User Input (CLI args)
    │
    ▼
Policy Parser Agent
    │  Policy data (dict: coverage, deductibles, exclusions)
    ▼
Document Collector Agent
    │  Readiness score + missing documents list
    ▼
Timeline Tracker Agent
    │  Deadline date + milestone timeline
    ▼
Letter Drafter Agent
    │  Formatted letter text
    ▼
Output Files (JSON + TXT)
```

## Test Coverage

```
tests/test_claimcounsel.py
  ├── TestConfig           — 2 tests (state coverage, doc types)
  ├── TestFileUtils        — 7 tests (r/w, PDF handling, empty dirs)
  ├── TestTimelineTracker  — 7 tests (deadlines, overdue, invalid dates, next steps)
  ├── TestDocumentCollector— 5 tests (requirements, inventory, checklist)
  ├── TestLetterDrafter    — 1 test (draft without LLM)
  ├── TestPolicyParser     — 3 tests (missing file, empty, plain English)
  └── TestClaimCounselIntegration — 1 test (full pipeline end-to-end)
```

## LLM Call Flow

```
LLMClient.chat(system_prompt, user_prompt)
  → OpenAI client.chat.completions.create()
  → Response text

LLMClient.extract_json(system_prompt, user_prompt)
  → chat() with response_format={"type": "json_object"}
  → json.loads(response)
  → Dict | {"error": "..."}
```

## Output Format

```
~/claimcounsel_data/output/<run_name>/
  ├── claim_counsel_report.json   # Structured data (parseable)
  └── claim_counsel_report.txt    # Human-readable report
```