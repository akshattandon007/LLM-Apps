"""MealWizard MCP server.

Exposes 6 MCP tools for recipe discovery, meal planning, ingredient
substitutions, seasonal produce guidance, and recipe scaling.

Run:
    uvicorn server:mcp_app --host 0.0.0.0 --port 8000

Or use the stdio transport for MCP-native tool integration:
    python -m mcp run server.py
"""

from __future__ import annotations

import json
from typing import Any

import mcp.server as mcp_server
import mcp.types as types
from mcp.server.lowlevel import Server

from src.mealdb import MealDBClient
from src.mealplanner import generate_plan, format_plan
from src.recipes import find_recipes, format_recipe_detail, format_recipes
from src.scaler import scale_recipe, format_scaled
from src.season import get_seasonal, format_seasonal
from src.substitutes import get_substitutes, format_substitutes

# Create the MCP server
app = Server("mealwizard")

# ------------------------------------------------------------------
# Handler functions (defined before reference in _handlers dict)
# ------------------------------------------------------------------


def _handle_find_recipes(ingredients: str = "", diet: str = "", cuisine: str = "") -> str:
    ing_list = [x.strip() for x in ingredients.split(",") if x.strip()]
    if not ing_list:
        return "Please provide at least one ingredient."
    recipes = find_recipes(ing_list, diet=diet, cuisine=cuisine)
    return format_recipes(recipes, ing_list)


def _handle_get_recipe(id: str = "") -> str:
    if not id:
        return "Please provide a recipe ID."
    client = MealDBClient()
    try:
        recipe = client.lookup_by_id(id)
        if not recipe:
            return f"No recipe found with ID '{id}'."
        return format_recipe_detail(recipe)
    finally:
        client.close()


def _handle_substitute(ingredient: str = "") -> str:
    if not ingredient:
        return "Please provide an ingredient name."
    sub = get_substitutes(ingredient)
    return format_substitutes(sub)


def _handle_meal_plan(days: int = 3, preferences: str = "", restrictions: str = "") -> str:
    plan = generate_plan(days=days, preferences=preferences, restrictions=restrictions)
    return format_plan(plan)


def _handle_whats_in_season(month: str = "", region: str = "US") -> str:
    if not month:
        return "Please provide a month."
    try:
        sp = get_seasonal(month, region)
        return format_seasonal(sp)
    except ValueError as e:
        return str(e)


def _handle_scale_recipe(id: str = "", servings: int = 4) -> str:
    if not id:
        return "Please provide a recipe ID."
    if servings < 1:
        return "Servings must be at least 1."
    client = MealDBClient()
    try:
        recipe = client.lookup_by_id(id)
        if not recipe:
            return f"No recipe found with ID '{id}'."
        sr = scale_recipe(recipe, servings)
        return format_scaled(sr)
    finally:
        client.close()


# Map tool names to handler functions
_handlers: dict[str, callable] = {
    "find_recipes": _handle_find_recipes,
    "get_recipe": _handle_get_recipe,
    "substitute": _handle_substitute,
    "meal_plan": _handle_meal_plan,
    "whats_in_season": _handle_whats_in_season,
    "scale_recipe": _handle_scale_recipe,
}


def _register_tools(app: Server) -> None:
    """Register all MCP tools on the server."""

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=name,
                description=desc,
                inputSchema=INPUT_SCHEMAS.get(name, {"type": "object", "properties": {}}),
            )
            for name, desc in TOOL_DESCRIPTIONS.items()
        ]

    @app.call_tool()
    async def call_tool(
        name: str,
        arguments: dict[str, Any],
    ) -> list[types.TextContent]:
        handler = _handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = handler(**arguments)
            return [types.TextContent(type="text", text=result)]
        except Exception as exc:
            return [types.TextContent(
                type="text",
                text=f"Error: {exc}",
            )]


# Help text for each tool
TOOL_DESCRIPTIONS: dict[str, str] = {
    "find_recipes": (
        "Search for recipes using ingredients you have on hand. "
        "Optionally filter by diet (Vegetarian, Vegan, Seafood, etc.) "
        "and cuisine (Italian, Mexican, Indian, etc.). "
        "Returns top matching recipes with ingredient match counts."
    ),
    "get_recipe": (
        "Get full details for a specific recipe by its TheMealDB ID. "
        "Returns ingredient list with measures, step-by-step instructions, "
        "cuisine, category, image URL, and YouTube link if available."
    ),
    "substitute": (
        "Find substitute ingredients when you're out of something. "
        "Covers 24+ common ingredients with practical swaps and usage notes. "
        "Examples: eggs -> flax egg, butter -> oil, milk -> almond milk."
    ),
    "meal_plan": (
        "Generate a multi-day meal plan (1-14 days). "
        "Optionally specify preferences (cuisine or diet category) "
        "and restrictions (noted for awareness). "
        "Each day gets a different randomly-selected recipe."
    ),
    "whats_in_season": (
        "Find what fruits and vegetables are in season for a given month "
        "and region (US, UK, or EU). Data sourced from USDA, UK DEFRA, "
        "and EU FreshInfo seasonal charts."
    ),
    "scale_recipe": (
        "Scale a recipe's ingredient quantities to a different number of "
        "servings. Provide a TheMealDB recipe ID and your desired servings. "
        "Returns recalculated measures for every ingredient."
    ),
}

# Tool input schemas
INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "find_recipes": {
        "type": "object",
        "properties": {
            "ingredients": {
                "type": "string",
                "description": "Comma-separated list of ingredients you have (e.g. 'chicken, rice, bell pepper')",
            },
            "diet": {
                "type": "string",
                "description": "Diet filter: Vegetarian, Vegan, Seafood, Chicken, Beef, etc. (optional)",
            },
            "cuisine": {
                "type": "string",
                "description": "Cuisine filter: Italian, Mexican, Indian, Chinese, etc. (optional)",
            },
        },
        "required": ["ingredients"],
    },
    "get_recipe": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "TheMealDB recipe ID (e.g. '52772')",
            },
        },
        "required": ["id"],
    },
    "substitute": {
        "type": "object",
        "properties": {
            "ingredient": {
                "type": "string",
                "description": "Ingredient you're out of (e.g. 'butter', 'milk', 'eggs')",
            },
        },
        "required": ["ingredient"],
    },
    "meal_plan": {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days for the plan (1-14)",
            },
            "preferences": {
                "type": "string",
                "description": "Preferred cuisine or diet (e.g. 'Italian', 'Vegetarian')",
            },
            "restrictions": {
                "type": "string",
                "description": "Dietary restrictions (e.g. 'no dairy')",
            },
        },
        "required": ["days"],
    },
    "whats_in_season": {
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "Month (e.g. 'January', 'Jan', '6' for June)",
            },
            "region": {
                "type": "string",
                "description": "Region: 'US', 'UK', or 'EU' (default: US)",
            },
        },
        "required": ["month"],
    },
    "scale_recipe": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "TheMealDB recipe ID (e.g. '52772')",
            },
            "servings": {
                "type": "integer",
                "description": "Desired number of servings",
            },
        },
        "required": ["id", "servings"],
    },
}


# Register tools on module load
_register_tools(app)

# Export for uvicorn / mcp CLI
mcp_app = app

# When run directly, start stdio server
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    mcp_server.run(app)