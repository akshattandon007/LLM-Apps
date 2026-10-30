# Flow.md — Clarity

## Function-level call chains, module dependency graph, and execution flow.

---

## 🏗️ Module Dependency Graph

```
main.py
 ├── config.py                         [constants, env vars]
 ├── agents/__init__.py
 ├── agents/clause_extractor.py        [ClauseExtractor]
 │    ├── config.py
 │    └── (optional) openai
 ├── agents/plain_translator.py        [PlainTranslator]
 │    ├── config.py
 │    └── (optional) openai
 ├── agents/risk_advisor.py            [RiskAdvisor]
 │    ├── config.py
 │    └── (optional) openai
 ├── agents/orchestrator.py            [Orchestrator]
 │    └── agents/clause_extractor.py
 │    └── agents/plain_translator.py
 │    └── agents/risk_advisor.py
 └── tests/test_clarity.py
      ├── agents/clause_extractor.py
      ├── agents/plain_translator.py
      ├── agents/risk_advisor.py
      └── agents/orchestrator.py
```

---

## 🔄 Execution Flow

### Normal Execution (CLI)

```
main()
  │
  ├── read_input()
  │   ├── args.file           → Path.read_text()
  │   ├── args.text           → returned directly
  │   └── args.interactive    → sys.stdin.read()
  │
  ├── ClauseExtractor.__init__(api_key, model)
  │
  ├── ClauseExtractor.extract(document)
  │   ├── _llm_extract()       [if API key provided]
  │   │   ├── openai.ChatCompletion.create()
  │   │   └── json.loads()     [parse response]
  │   │
  │   └── _rule_based_extract() [fallback / no API key]
  │       ├── re.split()       [paragraph splitting]
  │       └── re.search()      [pattern matching per type]
  │
  ├── PlainTranslator.__init__(api_key, model)
  │
  ├── PlainTranslator.translate(clauses)
  │   └── _translate_single(clause)
  │       ├── _llm_translate()  [if API key]
  │       └── _rule_based_translate() [fallback]
  │           ├── re.sub()     [legal term → plain language]
  │           └── re.sub()     [sentence simplification]
  │
  ├── RiskAdvisor.__init__(api_key, model)
  │
  ├── RiskAdvisor.assess(clauses, translations, document)
  │   └── _assess_single(clause, translation)
  │       ├── _llm_assess()    [if API key]
  │       └── _rule_based_risk() [fallback]
  │           ├── re.search()  [pattern matching per risk flag]
  │           └── score computation
  │
  ├── Orchestrator.__init__(api_key, model)
  │
  ├── Orchestrator.compile_report(clauses, translations, risks)
  │   ├── _merge_results()     [align by index]
  │   ├── _generate_summary()  [executive summary]
  │   ├── _risk_summary()      [flag category counts]
  │   ├── _compile_questions() [dynamic question generation]
  │   └── _recommendation()    [overall verdict]
  │
  ├── print(report)            [stdout / Markdown]
  │
  └── [optional] write to --output file
```

### Test Execution

```
tests/test_clarity.py
  │
  ├── test_clause_extractor_rule_based()
  │   └── ClauseExtractor.extract()
  │
  ├── test_clause_extractor_empty()
  │   └── ClauseExtractor.extract("")
  │
  ├── test_plain_translator_rule_based()
  │   └── _rule_based_translate()
  │
  ├── test_risk_advisor_rule_based()
  │   └── _rule_based_risk()
  │
  ├── test_orchestrator_compilation()
  │   └── Orchestrator.compile_report()
  │
  ├── test_orchestrator_markdown()
  │   └── Orchestrator.to_markdown()
  │
  ├── test_rule_based_extract()
  │   └── _rule_based_extract()
  │
  ├── test_orchestrator_empty()
  │   └── Orchestrator.compile_report([], [], [])
  │
  ├── test_risk_advisor_empty()
  │   └── _rule_based_risk("cooperative clause")
  │
  └── test_plain_translator_multiple_clauses()
      └── PlainTranslator.translate()
```

---

## 🔑 Key Data Flows

### Clause Data Structure

```python
# From ClauseExtractor
{
    "text": str,          # Original clause text
    "type": str,          # Clause type from taxonomy
    "all_types": [str],   # All matching types
}

# From PlainTranslator
{
    "plain_text": str,    # Plain language version
    "confidence": float,  # 0.0–1.0
}

# From RiskAdvisor
{
    "score": float,       # 0.0–1.0 risk score
    "flags": [str],       # Risk flags raised
    "explanation": str,   # Plain English explanation
}

# Merged by Orchestrator
{
    "clause_number": int,
    "clause_type": str,
    "original_text": str,
    "plain_language": str,
    "confidence": float,
    "risk_score": float,
    "risk_flags": [str],
    "risk_explanation": str,
}
```

---

## 📁 File Map

| File | Purpose | Key Functions |
|------|---------|--------------|
| `main.py` | CLI entry point, input handling | `main()`, `read_input()` |
| `config.py` | Configuration constants | — |
| `agents/__init__.py` | Package init | — |
| `agents/clause_extractor.py` | Agent 1: clause extraction | `ClauseExtractor.extract()`, `_llm_extract()`, `_rule_based_extract()` |
| `agents/plain_translator.py` | Agent 2: plain language translation | `PlainTranslator.translate()`, `_translate_single()`, `_rule_based_translate()` |
| `agents/risk_advisor.py` | Agent 3: risk assessment | `RiskAdvisor.assess()`, `_assess_single()`, `_rule_based_risk()` |
| `agents/orchestrator.py` | Report compilation | `Orchestrator.compile_report()`, `_merge_results()`, `_generate_summary()`, `to_markdown()` |
| `tests/test_clarity.py` | Test suite | 10 test functions |
| `README.md` | Project documentation | — |
| `Decisions.md` | Design decisions | — |
| `Flow.md` | This file | — |

---

## ⚡ Error Handling Flow

```
ClauseExtractor.extract()
  ├── try: _llm_extract()
  │   ├── API error → print warning → _rule_based_extract()
  │   └── JSON parse error → print warning → _rule_based_extract()
  └── except: _rule_based_extract()

PlainTranslator._translate_single()
  ├── try: LLM call
  │   └── any error → _rule_based_translate()
  └── fallback always succeeds (pure regex)

RiskAdvisor._assess_single()
  ├── try: LLM call
  │   └── any error → _rule_based_risk()
  └── fallback always succeeds (pure regex)
```

Each agent independently degrades: if the LLM is unavailable, the agent falls back to its rule-based mode and the pipeline continues. No single point of failure.
