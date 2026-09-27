#!/usr/bin/env python3
"""PantryWarden — Multi-agent kitchen logistics system.

A weekly meal planning system where specialized agents collaborate:
- InventoryAgent: what's in the pantry
- RecipeAgent: what to cook
- NutritionAgent: dietary needs and restrictions
- BudgetAgent: cost optimization
- ScheduleAgent: time slot fitting
- Orchestrator: coordinates everything
"""

import argparse
import json
import sys
from typing import Dict, List, Optional

from agents.inventory_agent import InventoryAgent
from agents.recipe_agent import RecipeAgent
from agents.nutrition_agent import NutritionAgent, DietaryProfile
from agents.budget_agent import BudgetAgent, WeeklyBudget
from agents.schedule_agent import ScheduleAgent
from agents.orchestrator import Orchestrator


def add_item(args):
    inventory = InventoryAgent()
    inventory.add_item(args.name, float(args.quantity), args.unit,
                       category=args.category or "other",
                       expiry_days=int(args.expiry_days) if args.expiry_days else 0)
    print(f"✅ Added {args.quantity} {args.unit} of '{args.name}' to pantry.")
    sys.exit(0)


def remove_item(args):
    inventory = InventoryAgent()
    if inventory.remove_item(args.name, float(args.quantity)):
        print(f"✅ Removed {args.quantity} of '{args.name}' from pantry.")
    else:
        print(f"❌ Could not remove {args.quantity} of '{args.name}' — insufficient stock.")
    sys.exit(0)


def list_pantry(args):
    inventory = InventoryAgent()
    items = inventory.list_items()
    if not items:
        print("🧺 Pantry is empty. Add items with 'add-item'.")
        sys.exit(0)
    print(f"{'Item':<20} {'Qty':<8} {'Unit':<8} {'Expiry':<12} {'Category':<12}")
    print("-" * 60)
    for i in items:
        exp = i.expiry_date or "—"
        print(f"{i.name:<20} {i.quantity:<8.1f} {i.unit:<8} {exp:<12} {i.category:<12}")
    low = inventory.get_low_stock_items()
    if low:
        print(f"\n⚠️  Low stock: {', '.join(i.name for i in low)}")
    expiring = inventory.get_expiring_items(within_days=7)
    if expiring:
        print(f"⏰ Expiring soon: {', '.join(i.name for i in expiring)}")
    sys.exit(0)


def weekly_plan(args):
    """Run the full multi-agent orchestration pipeline."""
    restrictions = args.restrictions.split(",") if args.restrictions else None
    max_cal = int(args.max_calories) if args.max_calories else None
    min_protein = float(args.min_protein) if args.min_protein else None
    budget_per = float(args.budget_per_meal) if args.budget_per_meal else None
    dinners = int(args.dinners) if args.dinners else 5

    orchestrator = Orchestrator(
        inventory=InventoryAgent(),
        recipes=RecipeAgent(),
        nutrition=NutritionAgent(),
        budget=BudgetAgent(),
        schedule=ScheduleAgent(),
    )

    result = orchestrator.run_weekly_plan(
        dietary_restrictions=restrictions,
        max_calories_per_meal=max_cal,
        min_protein_g=min_protein,
        weekdays_only=not args.weekends,
        dinners_per_week=dinners,
        budget_per_meal=budget_per,
    )

    print("=" * 60)
    print("🍽️  PANTRYWARDEN — WEEKLY MEAL PLAN")
    print("=" * 60)

    print("\n📅 PLAN:")
    for day, meals in result["plan"].items():
        if meals:
            print(f"  {day.capitalize():<10}: {', '.join(meals)}")

    print("\n🛒 GROCERY LIST (missing ingredients):")
    if result["grocery_list"]:
        for item, count in result["grocery_list"]:
            print(f"  • {item} (x{count})")
    else:
        print("  Everything is in stock!")

    budget = result["budget"]
    print(f"\n💰 BUDGET: ${budget['planned_spend']:.2f} / ${budget['budget_limit']:.2f} "
          f"planned ({'✅ within budget' if budget['within_budget'] else '⚠️ over budget'})")

    inv = result["inventory_summary"]
    print(f"\n🧺 PANTRY: {inv['total_items']} items")
    if inv['low_stock']:
        print(f"  ⚠️  Low stock: {', '.join(inv['low_stock'])}")
    if inv['expiring_soon']:
        print(f"  ⏰ Expiring soon: {', '.join(inv['expiring_soon'])}")

    print(f"\n📊 {result['meals_planned']} meals planned for the week.")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Plan saved to {args.output}")
    sys.exit(0)


def recommend(args):
    """Quick recommendation based on ingredients."""
    ingredients = args.ingredients.split(",") if args.ingredients else []
    if not ingredients:
        inventory = InventoryAgent()
        ingredients = [i.name for i in inventory.list_items()]
    if not ingredients:
        print("❌ No ingredients specified and pantry is empty.")
        sys.exit(1)

    orch = Orchestrator(recipes=RecipeAgent(), nutrition=NutritionAgent())
    recs = orch.recommend_for_ingredients(ingredients)
    if not recs:
        print("😕 No recipes match your ingredients.")
        sys.exit(0)

    print(f"🍳 Recipes matching: {', '.join(ingredients)}")
    print("-" * 50)
    for r in recs:
        print(f"\n  {r['name']}")
        print(f"    Cook time: {r['cook_time_min']} min | Cost: ${r['cost_per_serving']:.2f}")
        print(f"    Ingredients needed: {', '.join(r['ingredients'])}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="PantryWarden — Multi-agent kitchen logistics",
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # add-item
    p_add = sub.add_parser("add-item", help="Add item to pantry")
    p_add.add_argument("name")
    p_add.add_argument("quantity")
    p_add.add_argument("--unit", default="unit")
    p_add.add_argument("--category")
    p_add.add_argument("--expiry-days", default="0")
    p_add.set_defaults(func=add_item)

    # remove-item
    p_rm = sub.add_parser("remove-item", help="Remove item from pantry")
    p_rm.add_argument("name")
    p_rm.add_argument("quantity")
    p_rm.set_defaults(func=remove_item)

    # list-pantry
    p_ls = sub.add_parser("list-pantry", help="List pantry contents")
    p_ls.set_defaults(func=list_pantry)

    # weekly-plan
    p_wp = sub.add_parser("weekly-plan", help="Generate weekly meal plan")
    p_wp.add_argument("--restrictions",
                      help="Comma-separated: vegan,gluten_free,low_carb,dairy_free,keto")
    p_wp.add_argument("--max-calories", help="Max calories per meal")
    p_wp.add_argument("--min-protein", help="Min protein (g) per meal")
    p_wp.add_argument("--budget-per-meal", help="Max $ per meal")
    p_wp.add_argument("--dinners", default="5", help="Dinners per week")
    p_wp.add_argument("--weekends", action="store_true",
                      help="Include weekend slots")
    p_wp.add_argument("--output", help="Save plan to JSON file")
    p_wp.set_defaults(func=weekly_plan)

    # recommend
    p_rec = sub.add_parser("recommend", help="Get recipe recommendations")
    p_rec.add_argument("--ingredients",
                       help="Comma-separated ingredient list")
    p_rec.set_defaults(func=recommend)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()