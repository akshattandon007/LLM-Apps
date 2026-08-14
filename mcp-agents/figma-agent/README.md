# 🎨 Figma MCP Agent

> Your designs, talking to your code — export specs, assets, and tokens right from Figma. 🚀

Ask questions about Figma designs in plain English and get back structured specs, exported assets, and design tokens ready to drop into your codebase. No more squinting at layers or copying hex values by hand.

---

## 🧰 What it does

| What | How |
|---|---|
| 📐 **Extract design specs** | Pull widths, colors, fonts, spacing from any frame or layer |
| 🖼️ **Export assets** | Export frames/layers as SVG, PNG, or PDF (up to 4×) |
| 🎨 **Extract style tokens** | Colors, typography, spacing → CSS variables or Tailwind JSON |
| 🧩 **List frames & layers** | Navigate the full design hierarchy |
| 🔍 **Get component properties** | Component metadata + variant properties |
| 📊 **Compare design versions** | Diff two file versions and see exactly what changed |

---

## 🛠️ Tool surface

| Tool | What it does |
|---|---|
| `get_design_specs(file_key, node_id)` | Returns structured specs for a node (width, height, fills, strokes, effects, typography, auto-layout) |
| `export_asset(file_key, node_id, format)` | Exports a node as SVG, PNG, or PDF. Optional `scale` (1×–4×) |
| `list_frames_and_layers(file_key)` | Lists all top-level frames and their children with IDs and types |
| `get_component_properties(file_key, component_id)` | Gets component name, description, variant properties |
| `extract_style_tokens(file_key)` | Extracts colors, typography, spacing as CSS vars or Tailwind JSON |
| `get_design_diff(file_key, version_a, version_b)` | Compares two versions — returns added/removed/changed nodes |

---

## 🚀 Quick start

```bash
# 1. Set your Figma access token
export FIGMA_ACCESS_TOKEN="figd_your_token_here"

# 2. Install
pip install -r requirements.txt

# 3. Run!
python main.py                 # stdio mode (for Claude Desktop / MCP hosts)
python main.py --http          # HTTP mode on port 8000
```

Get your Figma PAT from [Manage personal access tokens](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens).  
Optionally set `ANTHROPIC_API_KEY` for LLM-enhanced Tailwind mapping.

---

## 💬 Example queries

> *"Export the hero section from the landing page design as SVG assets and give me the exact Tailwind classes for all the spacing, colors, and typography used."*

> *"What changed between version 42 and version 43 of the main prototype?"*

> *"List every frame in the mobile app design and tell me which ones use auto-layout."*

> *"Give me all the colors used in this file as CSS custom properties."*

---

## 🏗️ Architecture

```
figma-agent/
├── main.py                     # MCP server entry point (stdio / HTTP)
├── requirements.txt
├── .env.example
├── README.md                   # 👋 you are here
├── src/
│   ├── __init__.py
│   ├── figma_client.py         # Figma REST API wrapper
│   ├── tokens.py               # Style token extraction (CSS/Tailwind)
│   ├── specs.py                # Design spec extraction from nodes
│   ├── tools.py                # MCP tool definitions
│   └── models.py               # Pydantic models
└── tests/
    ├── __init__.py
    └── test_smoke.py           # Smoke tests with mocked API + LLM
```

- **`main.py`** — starts an MCP server (stdio or HTTP) and registers all tools
- **`src/figma_client.py`** — talks to the [Figma REST API](https://www.figma.com/developers/api) for file data, images, and version history
- **`src/specs.py`** — walks the node tree and extracts structured design properties
- **`src/tokens.py`** — aggregates colors/typography/spacing across a file and maps to CSS vars or Tailwind config
- **`src/tools.py`** — decorates each tool with MCP annotations, input schemas, and descriptions
- **`src/models.py`** — Pydantic models for typed tool inputs and API responses

---

## ✅ Running tests

```bash
# No Figma credentials needed — everything is mocked
python -m pytest tests/test_smoke.py -v
```

---

## 🧑‍🎨 Why Figma MCP?

Design → code handoff is the messiest part of product development. Designers work in Figma. Developers work in VS Code. The Figma MCP Agent is the bridge: you stay in your editor, ask for what you need, and the agent fetches it straight from the design file. No context switching, no screenshots, no "what font size is that?"