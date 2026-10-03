# Flow.md — MealWizard execution trace

## Overview
An MCP tool call arrives at `server.py` → dispatched to a handler → calls the
relevant domain module → returns formatted text. This document traces every
tool's call chain end-to-end.

---

## 1. find_recipes(ingredients, diet, cuisine)

### Example call
```
find_recipes("chicken, rice, bell pepper", diet="", cuisine="Italian")
```

### Trace
```
server.py: call_tool("find_recipes", {"ingredients": "chicken,...", ...})
  │
  ├─ _handle_find_recipes()
  │   ├─ Split ingredients string: ["chicken", "rice", "bell pepper"]
  │   │
  │   └─ find_recipes(["chicken", "rice", "bell pepper"], diet="", cuisine="Italian")
  │       │
  │       ├─ MealDBClient.__init__()         # httpx client with base URL
  │       │
  │       ├─ filter_by_ingredient("chicken") # GET /filter.php?i=chicken
  │       │   └─ returns [{idMeal: "52772", ...}, {idMeal: "52801", ...}]
  │       │
  │       ├─ filter_by_ingredient("rice")    # GET /filter.php?i=rice
  │       │   └─ returns [{idMeal: "52772", ...}, ...]
  │       │
  │       ├─ filter_by_ingredient("bell pepper") # GET /filter.php?i=bell%20pepper
  │       │   └─ returns [{idMeal: "52772", ...}, ...]
  │       │
  │       ├─ Counter: {"52772": 3, "52801": 2, ...}  # recipes matching most ingredients
  │       │
  │       ├─ lookup_batch(["52772", "52801", ...])
  │       │   └─ for each ID: GET /lookupmeal.php?i=<id>
  │       │       └─ returns full Recipe with ingredients, instructions, etc.
  │       │
  │       ├─ Filter by cuisine="Italian"     # check recipe.area == "Italian"
  │       │   └─ (no-op if cuisine is empty)
  │       │
  │       ├─ Filter by diet=""               # check recipe.category
  │       │   └─ (no-op if diet is empty)
  │       │
  │       └─ Sort by ingredient match count, return top 10
  │
  └─ format_recipes(recipes, ["chicken", "rice", "bell pepper"])
      └─ Returns formatted string with match counts and IDs
```

### Data flow
```
MCP call → string split → Counter score → API filter calls →
union + ranking → full detail fetch → optional area/category filter →
sort → format → text response
```

---

## 2. get_recipe(id)

### Example call
```
get_recipe("52772")
```

### Trace
```
server.py: call_tool("get_recipe", {"id": "52772"})
  │
  ├─ _handle_get_recipe("52772")
  │   ├─ MealDBClient.__init__()
  │   ├─ lookup_by_id("52772")
  │   │   └─ GET /lookupmeal.php?i=52772
  │   │       └─ returns full Recipe with 20 ingredient slots
  │   └─ format_recipe_detail(recipe)
  │       ├─ Format header: name, cuisine, category
  │       ├─ Parse ingredients (skip None/empty slots)
  │       ├─ Split instructions on \r\n into numbered steps
  │       └─ Include image, YouTube, source URLs if present
  │
  └─ Returns formatted string
```

---

## 3. substitute(ingredient)

### Example call
```
substitute("butter")
```

### Trace
```
server.py: call_tool("substitute", {"ingredient": "butter"})
  │
  ├─ _handle_substitute("butter")
  │   ├─ get_substitutes("butter")
  │   │   ├─ Normalize: "butter".lower()
  │   │   ├─ Look up in _SUBSTITUTIONS dict
  │   │   │   └─ Key found: ["oil (vegetable/canola)", "margarine", ...]
  │   │   └─ Return Substitution(ingredient="butter", substitutes=[...], notes="...")
  │   │
  │   └─ format_substitutes(sub)
  │       └─ "Ingredient: butter\nSubstitutes:\n  - oil (vegetable/canola)\n  - ..."
  │
  └─ Returns formatted string
```

### Partial match fallback
```
get_substitutes("baking powder")
  ├─ Exact match not found
  ├─ Partial scan: "baking" in "baking powder" → match!
  └─ Return Substitution for baking powder
```

---

## 4. meal_plan(days, preferences, restrictions)

### Example call
```
meal_plan(3, "Italian", "no dairy")
```

### Trace
```
server.py: call_tool("meal_plan", {"days": 3, "preferences": "Italian", "restrictions": "no dairy"})
  │
  ├─ _handle_meal_plan(3, "Italian", "no dairy")
  │   ├─ generate_plan(days=3, preferences="Italian", restrictions="no dairy")
  │   │   ├─ Check if "Italian" is a cuisine or diet category
  │   │   │   └─ "Italian" is in _VALID_CUISINES → is_cuisine = True
  │   │   │
  │   │   ├─ Loop: fetch random recipes until we have 3 unique ones
  │   │   │   ├─ GET /random.php → Recipe("Spaghetti Carbonara", area="Italian")
  │   │   │   │   └─ area == "italian" → keep
  │   │   │   ├─ GET /random.php → Recipe("Tacos", area="Mexican")
  │   │   │   │   └─ area != "italian" → skip
  │   │   │   ├─ GET /random.php → Recipe("Pizza", area="Italian")
  │   │   │   │   └─ area == "italian" → keep
  │   │   │   └─ ... until 3 collected or max_attempts reached
  │   │   │
  │   │   └─ Return MealPlan with MealPlanDay objects
  │   │
  │   └─ format_plan(plan)
  │       └─ "Meal Plan — 3 day(s)\nPreferences: Italian\n\nDay 1 — ..."
  │
  └─ Returns formatted string
```

---

## 5. whats_in_season(month, region)

### Example call
```
whats_in_season("June", "US")
```

### Trace
```
server.py: call_tool("whats_in_season", {"month": "June", "region": "US"})
  │
  ├─ _handle_whats_in_season("June", "US")
  │   ├─ get_seasonal("June", "US")
  │   │   ├─ Normalize month: "June" → "june"
  │   │   ├─ Validate region "US", month "june"
  │   │   ├─ Look up _PRODUCE["US"]["june"]
  │   │   │   └─ fruits: ["strawberries", "blueberries", "cherries", ...]
  │   │   │   └─ vegetables: ["tomatoes", "zucchini", "corn", ...]
  │   │   └─ Return SeasonalProduce
  │   │
  │   └─ format_seasonal(sp)
  │       └─ "Seasonal produce — June (US)\n\nFruits:\n  - ...\n\nVegetables:\n  - ..."
  │
  └─ Returns formatted string
```

---

## 6. scale_recipe(id, servings)

### Example call
```
scale_recipe("52772", 6)
```

### Trace
```
server.py: call_tool("scale_recipe", {"id": "52772", "servings": 6})
  │
  ├─ _handle_scale_recipe("52772", 6)
  │   ├─ MealDBClient.__init__()
  │   ├─ lookup_by_id("52772")
  │   │   └─ GET /lookupmeal.php?i=52772
  │   │       └─ returns Recipe("Chicken Teriyaki", ingredients=[...])
  │   │
  │   ├─ scale_recipe(recipe, target_servings=6, original_servings=4)
  │   │   ├─ factor = 6 / 4 = 1.5
  │   │   ├─ For each ingredient ingredient-measure pair:
  │   │   │   ├─ "Chicken breast", "2" → qty=2.0 → 2*1.5=3 → "3"
  │   │   │   ├─ "Soy sauce", "4 tbsp" → qty=4.0 → 4*1.5=6 → "6 tbsp"
  │   │   │   ├─ "Honey", "2 tbsp" → qty=2.0 → 2*1.5=3 → "3 tbsp"
  │   │   │   └─ "Rice", "1 cup" → qty=1.0 → 1*1.5=1.5 → "1 1/2 cup"
  │   │   └─ Return ScaledRecipe
  │   │
  │   └─ format_scaled(sr)
  │       └─ "Chicken Teriyaki (scaled from 4 to 6 servings)\n\nIngredients:\n  - 3 Chicken breast\n  - ..."
  │
  └─ Returns formatted string
```

### Quantity parsing detail
```
_parse_quantity("1.5")        → 1.5
_parse_quantity("1/2")        → 0.5
_parse_quantity("2")          → 2.0
_parse_quantity("4 tbsp")     → 4.0
_parse_quantity("1 cup")      → 1.0
_parse_quantity("to taste")    → 0.0  (unparseable → pass through)

_format_quantity(3.0)        → "3"
_format_quantity(1.5)        → "1.5"
_format_quantity(0.5)        → "1/2"
_format_quantity(0.33)       → "1/3"
```

---

## Error handling pattern (all tools)

```
call_tool(name, arguments)
  ├─ handler found ✓ → try execute
  │   ├─ success → return TextContent(text=formatted_result)
  │   └─ exception → return TextContent(text="Error: <message>")
  │
  └─ handler NOT found → raise ValueError("Unknown tool: <name>")
```

## API call cost per tool (worst case)

| Tool | API calls | Notes |
|---|---|---|
| find_recipes (3 ingredients) | 3 filter + 10 lookup = 13 | 0.15s delay each ≈ 2s |
| get_recipe | 1 lookup | ~0.15s |
| substitute | 0 | Static data only |
| meal_plan (3 days) | up to 60 random | 0.15s each, 3 hits expected |
| whats_in_season | 0 | Static data only |
| scale_recipe | 1 lookup | ~0.15s |