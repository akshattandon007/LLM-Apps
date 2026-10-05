# 🚗 RecallGuard — Vehicle Safety Recall MCP Agent ⚠️

**Check open safety recalls on any vehicle — by year, make, and model — directly through your AI assistant.**

RecallGuard is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that taps into the **NHTSA public API** (zero-auth, free) to check vehicle safety recalls. No signup, no API key, no ads — just factual recall data from the National Highway Traffic Safety Administration.

## ✨ Why RecallGuard?

| Problem | How RecallGuard Helps |
|---------|----------------------|
| **Buying a used car?** 🔍 | Check if it has any open recalls before you buy |
| **Got a recall notice?** 📬 | Look up the full details — what's broken, how dangerous, how to fix |
| **Selling your car?** 💰 | Prove to the buyer that recalls were addressed |
| **Car seat / tire recall?** 👶 | NHTSA covers child seats, tires, and equipment too |
| **Need to check your fleet?** 🚛 | Systematic lookups by make/model/year |

## ⚡ Quick Start

```bash
# 1. Install
cd recallguard
pip install -e .

# 2. Run as MCP server (stdio)
recallguard
```

### Claude Desktop Config

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "recallguard": {
      "command": "python",
      "args": ["-m", "recallguard.server"]
    }
  }
}
```

### Claude Code / Codex CLI

```bash
# Add to your MCP config
claude mcp add recallguard -- python -m recallguard.server
```

## 🛠 Tools

| Tool | Description |
|------|-------------|
| `get_recall_years` | List all vehicle model years with recall data |
| `get_recall_makes` | List manufacturers with recalls in a given year |
| `get_recall_models` | List vehicle models with recalls for a make + year |
| `check_vehicle_recalls` | **The main one** — check recalls for a specific vehicle |
| `get_recall_by_campaign` | Look up a specific recall by its NHTSA campaign number |

## 💬 Example Queries

> *"Check if my 2020 Toyota Corolla has any open recalls"*
> → AI calls `check_vehicle_recalls(make="TOYOTA", model="COROLLA", model_year="2020")`
> → Returns full recall details with component, summary, remedy

> *"What years does NHTSA have recall data for?"*
> → AI calls `get_recall_years()`
> → "Range: 1949 – 2027 (80 years)"

> *"Tell me about recall 23V865000"*
> → AI calls `get_recall_by_campaign(campaign_number="23V865000")`
> → Returns the full Toyota airbag sensor recall details

## 📦 Dependencies

- `mcp` >= 1.0.0 — MCP Python SDK
- `httpx` >= 0.27.0 — HTTP client
- `pydantic` >= 2.0.0 — Type validation

## 🧪 Testing

```bash
# Unit tests (mocked HTTP)
pytest tests/

# Live API tests (hits real NHTSA)
pytest tests/ --live
```

## 🔑 Auth

**None.** The NHTSA public API requires zero authentication. RecallGuard does not need or store any API keys.

## ⚠ Limitations

- **Bulk VIN lookups are prohibited** by NHTSA's API policy. Single vehicle lookups are fine.
- **Data freshness**: NHTSA updates as manufacturers file reports. New recalls may take days to appear.
- **Rate limiting**: NHTSA applies per-IP throttling. The server uses polite 15s timeouts and single-shot requests.

## 📄 License

This project uses data from the National Highway Traffic Safety Administration, a U.S. government agency. The data is public domain.