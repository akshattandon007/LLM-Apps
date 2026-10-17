# Execution Flow

## Module dependency graph

```
pocketdiet/__main__.py
    └── pocketdiet.cli

pocketdiet/cli.py
    ├── pocketdiet.api
    │   └── urllib.request, urllib.error, urllib.parse, json
    └── pocketdiet.nutrition

pocketdiet/nutrition.py
    └── (stdlib only: no external imports)

tests/test_nutrition.py
    └── pocketdiet.nutrition
```

## Execution trace: `python -m pocketdiet "greek yogurt"`

```
__main__.py
  └─ cli.main(argv=None)
       ├─ build_parser()
       │    └─ argparse.ArgumentParser()
       ├─ parser.parse_args(["greek yogurt"])
       │    → args.food="greek yogurt", args.barcode=None, args.servings=1.0,
       │      args.json=False, args.top=1
       ├─ _handle_search(args)
       │    ├─ api.search_foods("greek yogurt", page_size=1)
       │    │    ├─ urllib.parse.urlencode({"search_terms": "greek yogurt",
       │    │    │   "json": "1", "page_size": "1"})
       │    │    ├─ urllib.request.Request(url, headers={"User-Agent": ...})
       │    │    ├─ urllib.request.urlopen(req, timeout=10)
       │    │    ├─ resp.read().decode("utf-8")
       │    │    ├─ json.loads(...)
       │    │    └─ return data.get("products", [])
       │    │
       │    └─ (products is non-empty)
       │         → _print_product(product, servings=1.0)
       │              ├─ product.get("product_name")
       │              ├─ product.get("brands")
       │              ├─ product.get("code")
       │              ├─ print(bold name, brand, barcode)
       │              ├─ product.get("nutriments", {})
       │              └─ nutrition.generate_verdicts(nutriments, 1.0)
       │                   ├─ nutrition.parse_nutriments(nutriments)
       │                   │    └─ extract known keys, cast to float
       │                   ├─ nutrition.get_serving_values(parsed, 1.0)
       │                   │    └─ multiply per-100 g values by servings
       │                   └─ return [verdict dicts with color/level/verdict]
       │
       └─ nutrition.format_verdicts(verdicts)
            └─ render ANSI-coloured table to stdout
```

## Execution trace: `python -m pocketdiet --barcode 3017620422003 --json`

```
__main__.py
  └─ cli.main(argv)
       ├─ parser.parse_args(["--barcode", "3017620422003", "--json"])
       │    → args.barcode="3017620422003", args.json=True
       ├─ _handle_barcode(args)
       │    ├─ api.lookup_barcode("3017620422003")
       │    │    ├─ urllib.request.Request(url)
       │    │    ├─ urlopen / read / json.load
       │    │    ├─ check data.get("status") == 1
       │    │    └─ return data.get("product") or None
       │    ├─ product is not None
       │    └─ json.dumps(product, indent=2) → stdout
```

## Execution trace: `python -m pytest tests/ -v`

```
pytest discovers tests/test_nutrition.py
  → TestParseNutriments   (3 tests)
  → TestGetServingValues  (4 tests)
  → TestGenerateVerdicts  (18 tests)
  → TestFormatVerdicts    (2 tests)
  ────────────────────────────────────
  No network calls.  All functions test in-process.
```

## Data flow (verdict generation)

```
OFF API response
    ↓
product["nutriments"] dict
    ↓
parse_nutriments()
    → {"energy-kcal_100g": 97.0, "fat_100g": 3.5, ...}
    ↓
get_serving_values(parsed, servings)
    → {"energy-kcal": 97.0, "fat": 3.5, ...}   (× servings)
    ↓
generate_verdicts(nutriments, servings)
    → [{"label": "Sugars", "value": "4.0g", "level": "good", ...},
       {"label": "Fat",    "value": "3.5g", "level": "good", ...}, ...]
    ↓
format_verdicts(verdicts)
    → "  ✓ Sugars        4.0g  — Low sugar\n  ✓ Fat           3.5g  — Low fat..."
```