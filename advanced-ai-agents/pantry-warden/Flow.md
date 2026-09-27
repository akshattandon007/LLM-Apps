# Flow.md

## PantryWarden — Execution Flow & Module Dependency Graph

### Dependency Graph

```
main.py
  └─ agents/orchestrator.py
       ├─ agents/inventory_agent.py      [InventoryAgent]
       ├─ agents/recipe_agent.py         [RecipeAgent]
       │    └─ agents/nutrition_agent.py [NutritionAgent] (recipe uses NutritionAgent for filtering)
       ├─ agents/nutrition_agent.py      [NutritionAgent, DietaryProfile]
       ├─ agents/budget_agent.py         [BudgetAgent, WeeklyBudget]
       └─ agents/schedule_agent.py       [ScheduleAgent, TimeSlot]
```

No circular dependencies. Each agent is standalone and importable independently. The orchestrator is the only module that depends on multiple agents.

---

### Call Chain: `main.py` → CLI entry points

#### `main.py main()` — argparse dispatch
1. `argparse.ArgumentParser()` — parse subcommand
2. Dispatch to function based on subcommand

#### `main.py add_item()` — add item to pantry
1. → `InventoryAgent(data_path=...)`
2. → `inventory.add_item(name, qty, unit, category, expiry_days)`
3. → `inventory._save()` → writes `pantry_data.json`

#### `main.py remove_item()` — remove from pantry
1. → `InventoryAgent()`
2. → `inventory.remove_item(name, qty)` → decrements or deletes
3. → `inventory._save()`

#### `main.py list_pantry()` — display contents
1. → `InventoryAgent()`
2. → `inventory.list_items()` → returns sorted list
3. → `inventory.get_low_stock_items()` → items below threshold
4. → `inventory.get_expiring_items(within_days=7)` → soon-to-expire

#### `main.py weekly_plan()` — full orchestration
1. → `Orchestrator(inventory, recipes, nutrition, budget, schedule)`
2. → `orchestrator.run_weekly_plan(restrictions, max_cal, min_protein, ...)`
3. → print formatted plan
4. → optionally write JSON to `--output` file

#### `main.py recommend()` — quick recipe search
1. → `Orchestrator(recipes, nutrition)`
2. → `orchestrator.recommend_for_ingredients(ingredients)`
3. → display top 5 matches

---

### Call Chain: `Orchestrator.run_weekly_plan()` (core pipeline)

```
run_weekly_plan()
 │
 ├─ 1. INVENTORY ──────────────────────────────────────────────────
 │   inventory.list_items()              → available ingredient names
 │   inventory.get_low_stock_items()     → items below reorder threshold
 │   inventory.get_expiring_items(3)     → items expiring in 3 days
 │
 ├─ 2. RECIPE MATCHING ────────────────────────────────────────────
 │   recipe_agent.find_by_ingredients(available, min_coverage=0.3)
 │   │  ↓ For each recipe, compute: overlap = |available ∩ recipe.ingredients|
 │   │  ↓ Filter: overlap/len(recipe.ingredients) >= 0.3
 │   │  ↓ Sort by: (coverage DESC, missing_count ASC)
 │   │  Return: sorted list of Recipe objects
 │   │
 │   └─ Uses: each Recipe has .ingredients list
 │
 ├─ 3. NUTRITION FILTER ──────────────────────────────────────────
 │   nutrition_agent.set_profile(DietaryProfile(restrictions, max_calories, min_protein))
 │   recipe_agent.filter_by_diet(candidates, nutrition_agent, ...)
 │   │  ↓ For each candidate:
 │   │    check dietary_tags for each restriction
 │   │    check calories ≤ max_calories
 │   │    check protein ≥ min_protein
 │   │  Return: filtered list
 │   │
 │   └─ Uses: nutrition_agent.profile, recipe.dietary_tags, recipe.nutrition
 │
 ├─ 4. BUDGET FILTER ─────────────────────────────────────────────
 │   budget_agent.within_budget(recipe.cost_per_serving)
 │   │  ↓ Check: cost ≤ budget.max_per_meal
 │   │  Return: filtered list (fall back to all if empty)
 │   │
 │   └─ Uses: budget_agent.budget.max_per_meal
 │
 ├─ 5. SCHEDULING ────────────────────────────────────────────────
 │   schedule_agent.generate_week_slots(weekdays_only, dinners_per_week)
 │   │  ↓ Creates TimeSlot objects (day, start_hour, end_hour)
 │   │
 │   schedule_agent.plan_week(recipe_dicts, meal_type_preferences)
 │   │  ↓ For each TimeSlot (in day order):
 │   │    1. Skip if day already has 3+ meals
 │   │    2. Filter candidates by cook_time ≤ slot.duration
 │   │    3. Exclude recipe IDs already used
 │   │    4. Exclude the last-assigned recipe (variety)
 │   │    5. Pick first viable candidate
 │   │  Return: {day: [list of dicts]}
 │   │
 │   └─ Uses: schedule_agent.slots, each Recipe's cook_time_min
 │
 ├─ 6. GROCERY LIST ──────────────────────────────────────────────
 │   For each planned recipe (by ID):
 │     recipe_agent.get_missing_ingredients(recipe, available)
 │       → ingredient.lower() not in {available.lower()}
 │     Aggregate: ingredient → count
 │
 ├─ 7. BUDGET REVIEW ─────────────────────────────────────────────
 │   budget_agent.check_weekly_budget(all_planned_meals)
 │     → total_spend, remaining, within_budget flag
 │
 └─ Return: {
       "plan": {day: [meal_names]},
       "grocery_list": [(ingredient, count), ...],
       "budget": {planned_spend, budget_limit, remaining, within_budget},
       "inventory_summary": {total_items, low_stock, expiring_soon},
       "meals_planned": int
     }
```

---

### Call Chain: `Orchestrator.recommend_for_ingredients()`

```
recommend_for_ingredients(user_ingredients)
 │
 ├─ 1. recipe_agent.find_by_ingredients(user_ingredients, min_coverage=0.3)
 │
 ├─ 2. For each recipe:
 │      coverage = |user_ingredients ∩ recipe.ingredients| / len(recipe.ingredients)
 │      nutrition_score = nutrition_agent.score_meal_nutrition(recipe.nutrition)
 │      combined = coverage * 0.6 + nutrition_score * 0.4
 │
 ├─ 3. Sort by combined DESC
 │
 └─ Return: top 5 recipe dicts
```

---

### Data Flow (State Transitions)

```
User Input (CLI args)
  │
  ▼
  ┌──────────────┐
  │  Inventory    │ ← reads/writes pantry_data.json
  │  Agent        │
  └──────┬───────┘
         │ available ingredients (List[str])
         ▼
  ┌──────────────┐
  │  Recipe      │ ← reads default_recipes.json
  │  Agent       │
  └──────┬───────┘
         │ candidate recipes (List[Recipe])
         ▼
  ┌──────────────┐
  │  Nutrition   │ ← DietaryProfile (user-configured)
  │  Agent       │
  └──────┬───────┘
         │ filtered recipes (List[Recipe])
         ▼
  ┌──────────────┐
  │  Budget      │ ← WeeklyBudget (user-configured)
  │  Agent       │
  └──────┬───────┘
         │ budget-approved recipes
         ▼
  ┌──────────────┐
  │  Schedule    │ ← TimeSlots (generated from user prefs)
  │  Agent       │
  └──────┬───────┘
         │ planned week: {day: [meals]}
         ▼
  ┌──────────────┐
  │ Orchestrator  │ ← Aggregates: plan + grocery + budget + summary
  │ (aggregation) │
  └──────┬───────┘
         │
         ▼
    User Output (terminal / JSON file)
```

### File-level module map

```
pantry-warden/
├── main.py                          # CLI entry, argparse dispatch
├── agents/
│   ├── __init__.py                  # empty package marker
│   ├── inventory_agent.py           # InventoryAgent, PantryItem
│   ├── recipe_agent.py              # RecipeAgent, Recipe
│   ├── nutrition_agent.py           # NutritionAgent, DietaryProfile
│   ├── budget_agent.py              # BudgetAgent, WeeklyBudget
│   ├── schedule_agent.py            # ScheduleAgent, TimeSlot
│   └── orchestrator.py              # Orchestrator (depends on all 5 agents)
├── data/
│   ├── default_recipes.json         # Static recipe database (12 recipes)
│   └── pantry_data.json             # Persisted user inventory (auto-created)
├── tests/
│   ├── __init__.py
│   └── test_agents.py               # Tests for all agents + integration
├── requirements.txt
├── Decisions.md                     # This file
└── Flow.md                          # This file
```