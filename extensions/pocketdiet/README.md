# pocketdiet

CLI nutrition lookup tool — look up any food's nutritional info using the
[Open Food Facts](https://world.openfoodfacts.org/) database.  No API key
required, zero external dependencies (stdlib only).

## Install

```bash
# Editable install (recommended for development)
pip install -e /path/to/pocketdiet

# Or copy the directory and run as a module
python -m pocketdiet "greek yogurt"
```

## Usage

```bash
# Search by food name
pocketdiet "greek yogurt"

# Look up by barcode
pocketdiet --barcode 3017620422003

# Specify number of servings (scales values accordingly)
pocketdiet "almond milk" --servings 2

# Show multiple top results
pocketdiet "protein bar" --top 3

# Raw JSON output (piped to jq, etc.)
pocketdiet "banana" --json | jq .

# Short flags
pocketdiet "oat milk" -s 2 -t 3 -j
```

## Verdict thresholds (per 100 g / 100 ml)

| Nutrient         | Good          | Warning                  | Bad                     |
|------------------|---------------|--------------------------|-------------------------|
| Calories         | < 40 kcal     | ≥ 200 kcal               | —                       |
| Sugars           | ≤ 5 g         | 5–15 g                   | > 15 g                  |
| Fat              | ≤ 10 g        | 10–20 g                  | > 20 g                  |
| Saturated fat    | ≤ 1.5 g       | 1.5–5 g                  | > 5 g                   |
| Sodium           | ≤ 0.4 g       | 0.4–1.5 g                | > 1.5 g                 |
| Protein          | > 15 g        | 5–15 g                   | ≤ 5 g                   |
| Fiber            | > 5 g         | 2–5 g                    | ≤ 2 g                   |

Colour coding: ✓ green = good, ⚠ yellow = moderate, ✗ red = bad.