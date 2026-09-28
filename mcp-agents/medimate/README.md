# 💊 MediMate — Drug Safety & Pharmacy Intelligence MCP

**An MCP agent that puts the FDA's drug safety database at your fingertips.** Search drug labels, check adverse events, find generic alternatives, and look up NDC codes — all in plain English.

## 🛠 Tools

| Tool | Description |
|------|-------------|
| `search_drug` | Search by brand or generic name → warnings, interactions, ingredients, manufacturer |
| `check_adverse_events` | Look up reported adverse reactions and outcomes |
| `find_generic_alternatives` | Find all brand-name drugs containing a given active ingredient |
| `ndc_lookup` | Lookup drug by National Drug Code |
| `browse_drugs` | Browse recently updated drug labels with pagination |

## 🚀 Usage

Add to your MCP config:

```json
{
  "mcpServers": {
    "medimate": {
      "command": "python",
      "args": ["/path/to/medimate/server.py"]
    }
  }
}
```

Then ask your LLM:
- _"What are the side effects of Tylenol?"_
- _"Check adverse events for Lipitor"_
- _"What brand names contain acetaminophen?"_
- _"Look up NDC 15631-0404-0"_

## 📡 Data Source

All data comes from the **OpenFDA API** — free, zero-auth, updated weekly by the FDA. Coverage:
- 262,000+ drug labels (OTC + prescription)
- 2M+ adverse event reports
- Full NDC directory

## 🔒 Safety

Read-only agent — no write operations. All data sourced from official FDA databases with the disclaimer: _Do not rely on openFDA to make decisions regarding medical care._

## ⚖️ License

MIT