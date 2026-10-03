"""MealWizard CLI — test the MCP tools directly from the command line.

Usage:
    python main.py find-recipes --ingredients "chicken,rice,bell pepper"
    python main.py get-recipe --id 52772
    python main.py substitute --ingredient butter
    python main.py meal-plan --days 3 --preferences Italian
    python main.py whats-in-season --month January --region US
    python main.py scale-recipe --id 52772 --servings 6
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="MealWizard — what can I make with what I have?",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # find-recipes
    fr = sub.add_parser("find-recipes", help="Find recipes by ingredients")
    fr.add_argument("--ingredients", "-i", required=True, help="Comma-separated ingredients")
    fr.add_argument("--diet", "-d", default="", help="Diet filter (Vegetarian, Vegan, etc.)")
    fr.add_argument("--cuisine", "-c", default="", help="Cuisine filter (Italian, etc.)")

    # get-recipe
    gr = sub.add_parser("get-recipe", help="Get full recipe details")
    gr.add_argument("--id", required=True, help="TheMealDB recipe ID")

    # substitute
    sb = sub.add_parser("substitute", help="Find ingredient substitutes")
    sb.add_argument("--ingredient", required=True, help="Ingredient to substitute")

    # meal-plan
    mp = sub.add_parser("meal-plan", help="Generate a meal plan")
    mp.add_argument("--days", type=int, default=3, help="Number of days")
    mp.add_argument("--preferences", default="", help="Cuisine or diet preference")
    mp.add_argument("--restrictions", default="", help="Dietary restrictions")

    # whats-in-season
    ws = sub.add_parser("whats-in-season", help="Check seasonal produce")
    ws.add_argument("--month", required=True, help="Month (e.g. January, Jan)")
    ws.add_argument("--region", default="US", help="Region: US, UK, or EU")

    # scale-recipe
    sc = sub.add_parser("scale-recipe", help="Scale a recipe")
    sc.add_argument("--id", required=True, help="TheMealDB recipe ID")
    sc.add_argument("--servings", type=int, required=True, help="Target servings")

    args = parser.parse_args()

    if args.command == "find-recipes":
        from src.recipes import find_recipes, format_recipes
        ing_list = [x.strip() for x in args.ingredients.split(",") if x.strip()]
        recipes = find_recipes(ing_list, diet=args.diet, cuisine=args.cuisine)
        print(format_recipes(recipes, ing_list))

    elif args.command == "get-recipe":
        from src.mealdb import MealDBClient
        from src.recipes import format_recipe_detail
        client = MealDBClient()
        try:
            recipe = client.lookup_by_id(args.id)
            if recipe:
                print(format_recipe_detail(recipe))
            else:
                print(f"No recipe found with ID '{args.id}'.")
        finally:
            client.close()

    elif args.command == "substitute":
        from src.substitutes import get_substitutes, format_substitutes
        sub = get_substitutes(args.ingredient)
        print(format_substitutes(sub))

    elif args.command == "meal-plan":
        from src.mealplanner import generate_plan, format_plan
        plan = generate_plan(days=args.days, preferences=args.preferences, restrictions=args.restrictions)
        print(format_plan(plan))

    elif args.command == "whats-in-season":
        from src.season import get_seasonal, format_seasonal
        try:
            sp = get_seasonal(args.month, args.region)
            print(format_seasonal(sp))
        except ValueError as e:
            print(f"Error: {e}")

    elif args.command == "scale-recipe":
        from src.mealdb import MealDBClient
        from src.scaler import scale_recipe, format_scaled
        client = MealDBClient()
        try:
            recipe = client.lookup_by_id(args.id)
            if not recipe:
                print(f"No recipe found with ID '{args.id}'.")
                sys.exit(1)
            sr = scale_recipe(recipe, args.servings)
            print(format_scaled(sr))
        finally:
            client.close()


if __name__ == "__main__":
    main()