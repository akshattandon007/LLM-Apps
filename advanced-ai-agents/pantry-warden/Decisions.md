# Decisions.md

## Decision Log for PantryWarden

### 1. **Multi-agent architecture over monolithic tool-agent**
- **Decision**: Split into 5 specialized agents (Inventory, Recipe, Nutrition, Budget, Schedule) + an Orchestrator.
- **Rejected alternative**: Single agent with tool calls. **Why not**: Would collapse domain-specific reasoning into one prompt, making dietary constraints, inventory tracking, and scheduling compete for the same context. Dedicated agents each hold their own state and logic.
- **Rejected alternative**: Microservices over HTTP. **Why not**: Overkill for a CLI app that runs locally. Class-based modules are testable and composable without serialization overhead.

### 2. **Pydantic models for inventory items**
- **Decision**: Use `pydantic.BaseModel` for `PantryItem` with typed fields (`quantity: float`, expiry dates).
- **Rejected alternative**: Plain dicts. **Why not**: No type validation — expiring items could have malformed dates. Pydantic adds validation at the boundary with zero runtime cost in normal use.
- **Rejected alternative**: SQLite database. **Why not**: Adds a build dependency and complexity for what is essentially a small JSON-backed key-value store. SQLite adds concurrency and migration concerns.

### 3. **Local recipe database over live API calls**
- **Decision**: Pre-bundled `default_recipes.json` with 12 representative recipes.
- **Rejected alternative**: Spoonacular/Edamam API exclusively. **Why not**: Free tiers are rate-limited (150 req/day) and require API keys. A local DB works offline, tests instantly, and is deterministic. The API option is available as a future extension.
- **Rejected alternative**: Scraping recipe sites. **Why not**: Fragile, likely illegal (TOS violations), and slow. Not suitable for a daily-use CLI tool.

### 4. **CLI interface over web/API**
- **Decision**: argparse-based CLI with subcommands (add-item, weekly-plan, recommend, list-pantry).
- **Rejected alternative**: Flask/FastAPI web service. **Why not**: Adds deployment surface, dependencies, and security concerns. The user runs this locally on a terminal — CLI is the simplest UX.
- **Rejected alternative**: Interactive TUI. **Why not**: Requires a library (textual/urwid) and is harder to test headlessly. CLI works in any environment including cron.

### 5. **Weekly meal plan as the core output, not single-day**
- **Decision**: The orchestrator's main workflow plans 5-7 days, respecting variety and time constraints.
- **Rejected alternative**: Single-meal recommendation. **Why not**: The core problem is "what should I eat all week?" not "what's for dinner tonight?" A week-level view enables cross-recipe ingredient sharing, budget planning, and variety.

### 6. **Score-based recipe ranking (coverage + nutrition)**
- **Decision**: Recipes are scored by ingredient coverage (60%) + nutrition fit (40%).
- **Rejected alternative**: Simple "most matching ingredients" sorting. **Why not**: A recipe matching 3/5 ingredients might still exceed calorie limits. The combined score respects both inventory and health goals.
- **Rejected alternative**: User rating system. **Why not**: No user base; would add persistence and feedback loops without initial value.

### 7. **JSON file persistence for pantry data**
- **Decision**: Inventory data stored as `pantry_data.json` in the user's data directory.
- **Rejected alternative**: No persistence (in-memory only). **Why not**: Would require re-entering pantry items every run. The whole point is ongoing weekly planning.
- **Rejected alternative**: CSV format. **Why not**: JSON supports nested structures (expiry, categories) more naturally and is automatically typed.

### 8. **Dietary profile as a separate concern, not baked into recipes**
- **Decision**: `DietaryProfile` + `NutritionAgent` is a first-class component with configurable constraints.
- **Rejected alternative**: Built-in tags on recipes only. **Why not**: Loses the ability to express numeric constraints (max 600 cal, min 25g protein) and to score partial compliance.

### 9. **Variety enforcement in the scheduler**
- **Decision**: ScheduleAgent prevents back-to-back same-meal assignments.
- **Rejected alternative**: Allow repeats. **Why not**: The system is a *planner* — it should encourage variety. Users can manually override by re-running with specific prefs.

### 10. **Orchestrator's pipeline ordering**
- **Decision**: Inventory → Recipe → Nutrition → Budget → Schedule (as implemented).
- **Rejected alternative**: Budget-first, then nutrition. **Why not**: Eliminating recipes by budget before checking nutrition would remove healthy-but-cheap meals unnecessarily. Nutrition and inventory constraints are harder constraints; budget is softer.
- **Rejected alternative**: Parallel agent execution. **Why not**: Agents share intermediate state (available ingredients flow from inventory to recipe). A sequential pipeline is simpler and 100% deterministic.

### 11. **Expiry tracking with explicit dates**
- **Decision**: Items carry `added_date` and `expiry_date` (ISO format) for deterministic expiring-item detection.
- **Rejected alternative**: Shelf-life defaults by category (e.g., dairy=14 days). **Why not**: Users know their own items' expiry — store-bought eggs vs. farm-fresh have different timelines. Explicit dates are authoritative.

### 12. **Minimum-ingredient-coverage threshold of 30%**
- **Decision**: Recipes must have >=30% ingredient overlap with pantry to be considered.
- **Rejected alternative**: 0% (any recipe qualifies). **Why not**: Would recommend recipes that require buying everything, defeating the waste-reduction purpose.
- **Rejected alternative**: 50%+. **Why not**: Too restrictive for a stocked pantry; users would see empty results and abandon the tool. 30% is a sweet spot.

### 13. **Grocery list as missing-ingredient aggregation**
- **Decision**: The grocery list is built by collecting all ingredients from planned recipes minus what's in stock.
- **Rejected alternative**: Ask user what they want before generating. **Why not**: Slows the flow; the user runs "weekly-plan" and wants the full answer. Missing ingredients can be reviewed and trimmed.

### 14. **No sticky preferences across runs**
- **Decision**: Every `weekly-plan` invocation starts fresh — user passes restrictions, budget, etc. as flags.
- **Rejected alternative**: Persistent user profile with saved preferences. **Why not**: Over-engineered for an initial build. Profile management (update, reset, switch) adds UI complexity without evidence users need it. Easy to add later.

### 15. **Recipe data uses a static embedded file, not editable by user**
- **Decision**: 12 starter recipes in `data/default_recipes.json` shipped with the project.
- **Rejected alternative**: Editable YAML in `~/.pantrywarden/recipes.yaml`. **Why not**: Adds config directory creation, user documentation for recipe format, and the risk of YAML parse errors. Static data works immediately.