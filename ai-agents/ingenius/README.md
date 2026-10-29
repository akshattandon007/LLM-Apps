# Ingenius

> **🧪 Smart Ingredient Substitutions** — Missing an ingredient mid-recipe? Tell Ingenius what you're out of and get 3 precise substitutes with exact ratios, chemistry explanations, and usage tips.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OpenRouter](https://img.shields.io/badge/API-OpenRouter-green)](https://openrouter.ai)

## 🚀 What It Does

Ever been halfway through a recipe and realised you're out of buttermilk, fish sauce, or sourdough starter? Ingenius gives you **3 viable substitutes** with:

- **Exact replacement ratios** — not "use yogurt instead" but "1 cup yogurt replaces 1 cup buttermilk"
- **Chemistry explanations** — why the substitute works at a molecular level
- **Pro tips** — small adjustments that make the difference between edible and excellent
- **Mood modes** — quick, pantry-only, or gourmet

## 🛠️ Setup

1. **Clone the repo:**

   ```bash
   git clone https://github.com/akshattandon007/LLM-Apps.git
   cd LLM-Apps/ai-agents/ingenius
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Get an OpenRouter API key:**

   - Go to [openrouter.ai/keys](https://openrouter.ai/keys) (free tier, no credit card)
   - Set it as an environment variable:

   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```

## 🧪 Usage

### Basic

```bash
python ingenius.py buttermilk
```

Output:
```
🧪 Ingenius — Substitutes for 'buttermilk'

  1. Yogurt (plain, thinned)
     Ratio:    1 cup replaces 1 cup
     Why:      Yogurt has the same lactic acid profile as buttermilk for tenderising baked goods
     Tip:      Thin with 2 tbsp milk per cup to match buttermilk's consistency

  2. Milk + Lemon Juice
     Ratio:    1 cup minus 1 tbsp milk + 1 tbsp lemon juice
     Why:      The acid curdles the milk, creating a similar tangy, thick liquid
     Tip:      Let sit for 5 minutes before using for best results

  3. Kefir
     Ratio:    1 cup replaces 1 cup
     Why:      Kefir is a fermented milk product with live cultures matching buttermilk's acidity
     Tip:      Shake well first — kefir can separate during storage
```

### With recipe context

```bash
python ingenius.py "fish sauce" --recipe "pad thai"
```

Better results because the LLM considers the dish's flavour profile.

### Mood modes

```bash
python ingenius.py "sourdough starter" --mood quick
python ingenius.py "heavy cream" --mood pantry
python ingenius.py "truffle oil" --mood gourmet
```

| Mood | What it does |
|------|-------------|
| `quick` | Fastest option — minimal extra ingredients |
| `pantry` | Common staples only (no specialty items) |
| `gourmet` | Open to specialty ingredients for best flavour |

## 🧪 Tests

```bash
python -m pytest test_ingenius.py -v
```

Or with unittest directly:

```bash
python -m unittest test_ingenius -v
```

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Free API key from [openrouter.ai/keys](https://openrouter.ai/keys) |

## 📁 Project Structure

```
ingenius/
├── ingenius.py         # Main CLI entry point
├── requirements.txt    # Python dependencies
├── test_ingenius.py    # Unit tests (mocked)
├── Decisions.md        # Architecture decisions
├── Flow.md             # Execution flow documentation
└── README.md           # This file
```

## 🔗 Dependencies

- **Python 3.10+**
- `requests` — HTTP calls to OpenRouter API
- **OpenRouter API** (free tier) — LLM inference

## 📄 License

MIT — free to use, modify, and share.