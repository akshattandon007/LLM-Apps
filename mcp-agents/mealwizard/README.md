# MealWizard 🧙‍♂️🍽️

**What can I make with what I have?**

MealWizard is an MCP server that answers the daily "what's for dinner?"
question. Give it your ingredients, diet, or cuisine preference, and it finds
matching recipes from TheMealDB, suggests substitutes for missing ingredients,
plans multi-day meals, shows seasonal produce, and scales any recipe.

## Quick start

```bash
# Install
python -m venv /tmp/mealwizard-venv
/tmp/mealwizard-venv/bin/pip install -r requirements.txt

# Copy and configure .env (TheMealDB is free, no API key needed)
cp .env.example .env

# Run the CLI
/tmp/mealwizard-venv/bin/python main.py find-recipes --ingredients "chicken,rice,bell pepper"
/tmp/mealwizard-venv/bin/python main.py get-recipe --id 52772
```

## MCP Tools

| Tool | What it does |
|---|---|
| `find_recipes` | Search recipes by ingredients + optional diet/cuisine filter |
| `get_recipe` | Full recipe details (ingredients, instructions, video) |
| `substitute` | Find swaps for ingredients you're out of |
| `meal_plan` | Multi-day meal plan (1-14 days) with preferences |
| `whats_in_season` | Seasonal produce guide by month and region |
| `scale_recipe` | Scale ingredient quantities for any serving count |

### Example: find recipes

```
find_recipes(ingredients="chicken, rice, bell pepper", cuisine="Italian")
→ Returns top matches with ingredient match counts
```

### Example: scale a recipe

```
scale_recipe(id="52772", servings=6)
→ Returns recalculated ingredient quantities
```

## Running the server

```bash
# HTTP transport (SSE)
/tmp/mealwizard-venv/bin/uvicorn server:mcp_app --host 0.0.0.0 --port 8000

# Stdio transport (for MCP-native clients)
/tmp/mealwizard-venv/bin/python -c "import server; server.mcp_app.run()"
```

## Project structure

```
mealwizard/
├── server.py           # MCP server entry point
├── main.py             # CLI for testing
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Decisions.md        # Architecture rationale
├── Flow.md             # Execution trace
├── src/
│   ├── __init__.py
│   ├── models.py       # Pydantic schemas
│   ├── mealdb.py       # TheMealDB API client
│   ├── recipes.py      # Recipe search + formatting
│   ├── substitutes.py  # 24+ ingredient swaps (static table)
│   ├── mealplanner.py  # Multi-day meal planning
│   ├── season.py       # Seasonal produce (12 months × 3 regions)
│   └── scaler.py       # Recipe serving scaling
└── tests/
    ├── __init__.py
    ├── conftest.py     # Fixtures + mock data
    └── test_smoke.py   # 20+ smoke tests
```

## Data sources

- **Recipes**: [TheMealDB](https://www.themealdb.com/) — free, zero-auth API
- **Substitutions**: Curated from Joy of Cooking, Cook's Illustrated, Serious Eats
- **Seasonal produce**: USDA, UK DEFRA, EU FreshInfo seasonal charts

## License

MIT