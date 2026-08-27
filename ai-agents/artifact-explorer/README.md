# 🔍 Artifact Explorer — Point, Snap, Discover

> *Point your phone at anything and get its whole story.*

**Artifact Explorer** identifies objects and tells you not just *what* they are, but *why they matter* — origin, history, cultural significance, practical uses, and fun facts. Like Google Lens with narrative depth.

## Usage

```bash
# Describe an object
python main.py --describe "a rusty brass thing with dimples"

# Simulated demo — cycles through artifact library
python main.py --simulate

# Try a specific artifact
python main.py --describe "vintage camera"
```

## Artifact Library (simulated mode)

| Artifact | Origin | Era |
|----------|--------|-----|
| 📷 Vintage Camera | France | 1920s |
| 🌿 Spice Blend | Morocco | Ancient |
| 🔧 Weird Tool | England | 1800s |
| 🪴 House Plant | South America | — |
| 💎 Rock/Mineral | Various | Geological |
| 📻 Vintage Gadget | USA | 1950s |
| 🪙 Old Coin | Roman Empire | 100 AD |
| 📜 Antique Book | Italy | 1700s |

## Quick Start

```bash
pip install -r requirements.txt
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |