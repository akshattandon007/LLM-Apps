"""Seasonal produce guide.

Curated data for US, UK, and EU regions by month. No external API.
Covers 12 months x 3 regions with common fruits and vegetables.

Sources: USDA seasonal availability charts, UK DEFRA, EU FreshInfo.
"""

from __future__ import annotations

from src.models import SeasonalProduce

# KEY: region -> month -> {fruits, vegetables}
_PRODUCE: dict[str, dict[str, dict[str, list[str]]]] = {
    "US": {
        "january": {
            "fruits": ["oranges", "grapefruit", "lemons", "apples", "pears", "pomegranates"],
            "vegetables": ["kale", "cabbage", "broccoli", "cauliflower", "carrots", "sweet potatoes", "parsnips", "turnips"],
        },
        "february": {
            "fruits": ["oranges", "grapefruit", "lemons", "apples", "pears"],
            "vegetables": ["kale", "broccoli", "cauliflower", "brussels sprouts", "carrots", "sweet potatoes", "leeks"],
        },
        "march": {
            "fruits": ["strawberries", "oranges", "grapefruit", "apples", "pineapple"],
            "vegetables": ["asparagus", "spinach", "peas", "artichokes", "broccoli", "cauliflower", "radishes"],
        },
        "april": {
            "fruits": ["strawberries", "rhubarb", "pineapple", "oranges"],
            "vegetables": ["asparagus", "spinach", "peas", "artichokes", "radishes", "spring onions", "morels"],
        },
        "may": {
            "fruits": ["strawberries", "cherries", "rhubarb", "apricots"],
            "vegetables": ["asparagus", "peas", "spinach", "radishes", "spring onions", "zucchini", "broccoli"],
        },
        "june": {
            "fruits": ["strawberries", "blueberries", "cherries", "peaches", "plums", "apricots", "raspberries"],
            "vegetables": ["tomatoes", "zucchini", "corn", "green beans", "bell peppers", "eggplant", "cucumbers"],
        },
        "july": {
            "fruits": ["blueberries", "peaches", "plums", "watermelon", "cantaloupe", "blackberries", "raspberries", "nectarines"],
            "vegetables": ["tomatoes", "corn", "zucchini", "bell peppers", "eggplant", "green beans", "cucumbers", "okra"],
        },
        "august": {
            "fruits": ["watermelon", "cantaloupe", "peaches", "plums", "figs", "blackberries", "nectarines", "grapes"],
            "vegetables": ["tomatoes", "corn", "bell peppers", "eggplant", "okra", "green beans", "summer squash"],
        },
        "september": {
            "fruits": ["apples", "pears", "grapes", "figs", "plums", "cranberries"],
            "vegetables": ["pumpkins", "sweet potatoes", "broccoli", "cauliflower", "brussels sprouts", "carrots", "kale"],
        },
        "october": {
            "fruits": ["apples", "pears", "pumpkins", "cranberries", "grapes", "pomegranates"],
            "vegetables": ["pumpkins", "sweet potatoes", "broccoli", "cauliflower", "brussels sprouts", "kale", "parsnips"],
        },
        "november": {
            "fruits": ["apples", "pears", "pomegranates", "cranberries", "oranges", "grapefruit"],
            "vegetables": ["sweet potatoes", "pumpkins", "kale", "cabbage", "broccoli", "cauliflower", "brussels sprouts", "parsnips"],
        },
        "december": {
            "fruits": ["oranges", "grapefruit", "lemons", "apples", "pears", "pomegranates", "cranberries"],
            "vegetables": ["kale", "cabbage", "broccoli", "cauliflower", "brussels sprouts", "carrots", "sweet potatoes", "parsnips"],
        },
    },
    "UK": {
        "january": {
            "fruits": ["apples", "pears", "forced rhubarb", "oranges", "clementines"],
            "vegetables": ["cabbage", "carrots", "celeriac", "kale", "leeks", "parsnips", "swede", "sprouts"],
        },
        "february": {
            "fruits": ["apples", "pears", "forced rhubarb", "clementines"],
            "vegetables": ["cabbage", "carrots", "celeriac", "kale", "leeks", "parsnips", "swede", "sprouts"],
        },
        "march": {
            "fruits": ["rhubarb", "apples"],
            "vegetables": ["asparagus", "spring greens", "spinach", "watercress", "radishes", "spring onions"],
        },
        "april": {
            "fruits": ["rhubarb", "strawberries"],
            "vegetables": ["asparagus", "spring greens", "watercress", "radishes", "spring onions", "new potatoes"],
        },
        "may": {
            "fruits": ["strawberries", "rhubarb", "elderflowers"],
            "vegetables": ["asparagus", "broad beans", "peas", "new potatoes", "spinach", "watercress"],
        },
        "june": {
            "fruits": ["strawberries", "raspberries", "cherries", "gooseberries", "blackcurrants", "elderflowers"],
            "vegetables": ["broad beans", "peas", "new potatoes", "courgettes", "radishes", "spring onions", "beetroot"],
        },
        "july": {
            "fruits": ["strawberries", "raspberries", "blackcurrants", "cherries", "plums", "gooseberries", "redcurrants"],
            "vegetables": ["broad beans", "peas", "courgettes", "tomatoes", "cucumbers", "beetroot", "carrots", "new potatoes"],
        },
        "august": {
            "fruits": ["plums", "raspberries", "blackberries", "apples", "pears", "figs", "damsons"],
            "vegetables": ["broad beans", "sweetcorn", "tomatoes", "courgettes", "peppers", "aubergines", "beetroot"],
        },
        "september": {
            "fruits": ["apples", "pears", "blackberries", "plums", "damsons", "elderberries"],
            "vegetables": ["sweetcorn", "tomatoes", "peppers", "aubergines", "broccoli", "cauliflower", "pumpkins", "sprouts"],
        },
        "october": {
            "fruits": ["apples", "pears", "blackberries", "sloes"],
            "vegetables": ["pumpkins", "squash", "broccoli", "cauliflower", "leeks", "celeriac", "parsnips", "swede"],
        },
        "november": {
            "fruits": ["apples", "pears", "quince", "cranberries"],
            "vegetables": ["brussels sprouts", "cabbage", "carrots", "celeriac", "kale", "leeks", "parsnips", "swede", "turnips"],
        },
        "december": {
            "fruits": ["apples", "pears", "quince", "cranberries", "forced rhubarb"],
            "vegetables": ["brussels sprouts", "cabbage", "carrots", "celeriac", "kale", "leeks", "parsnips", "swede", "turnips"],
        },
    },
    "EU": {
        "january": {
            "fruits": ["apples", "pears", "oranges", "clementines", "grapefruit", "kiwi"],
            "vegetables": ["cabbage", "carrots", "celery", "leeks", "onions", "parsnips", "squash", "sprouts"],
        },
        "february": {
            "fruits": ["apples", "pears", "oranges", "clementines", "grapefruit", "kiwi"],
            "vegetables": ["cabbage", "carrots", "celery", "leeks", "onions", "parsnips", "squash"],
        },
        "march": {
            "fruits": ["oranges", "kiwi", "rhubarb", "strawberries"],
            "vegetables": ["asparagus", "spinach", "radishes", "spring onions", "artichokes", "peas"],
        },
        "april": {
            "fruits": ["rhubarb", "strawberries", "oranges"],
            "vegetables": ["asparagus", "spinach", "radishes", "spring onions", "artichokes", "peas", "fava beans"],
        },
        "may": {
            "fruits": ["strawberries", "rhubarb", "cherries", "apricots"],
            "vegetables": ["asparagus", "spinach", "peas", "fava beans", "artichokes", "zucchini"],
        },
        "june": {
            "fruits": ["strawberries", "cherries", "apricots", "peaches", "plums", "raspberries", "blueberries"],
            "vegetables": ["tomatoes", "zucchini", "cucumbers", "green beans", "bell peppers", "eggplant", "corn"],
        },
        "july": {
            "fruits": ["peaches", "plums", "apricots", "watermelon", "melons", "raspberries", "blueberries", "figs"],
            "vegetables": ["tomatoes", "zucchini", "cucumbers", "bell peppers", "eggplant", "green beans", "corn", "okra"],
        },
        "august": {
            "fruits": ["peaches", "plums", "figs", "grapes", "watermelon", "melons", "raspberries", "blackberries"],
            "vegetables": ["tomatoes", "zucchini", "bell peppers", "eggplant", "corn", "green beans", "cucumbers"],
        },
        "september": {
            "fruits": ["apples", "pears", "grapes", "figs", "plums", "melons", "cranberries"],
            "vegetables": ["pumpkins", "squash", "broccoli", "cauliflower", "carrots", "kale", "mushrooms"],
        },
        "october": {
            "fruits": ["apples", "pears", "grapes", "pomegranates", "quince", "cranberries"],
            "vegetables": ["pumpkins", "squash", "broccoli", "cauliflower", "carrots", "kale", "celeriac", "mushrooms"],
        },
        "november": {
            "fruits": ["apples", "pears", "pomegranates", "oranges", "grapefruit", "cranberries", "quince"],
            "vegetables": ["pumpkins", "squash", "cabbage", "cauliflower", "brussels sprouts", "carrots", "celeriac", "parsnips"],
        },
        "december": {
            "fruits": ["apples", "pears", "oranges", "grapefruit", "clementines", "pomegranates", "kiwi"],
            "vegetables": ["cabbage", "brussels sprouts", "carrots", "celeriac", "kale", "leeks", "parsnips", "squash"],
        },
    },
}

VALID_REGIONS = sorted(_PRODUCE.keys())
VALID_MONTHS = list(next(iter(_PRODUCE.values())).keys())


def _normalise_month(month: str) -> str:
    """Normalise month string to lowercase."""
    m = month.strip().lower()
    # Accept full or abbreviated names
    month_map = {
        "jan": "january", "feb": "february", "mar": "march", "apr": "april",
        "may": "may", "jun": "june", "jul": "july", "aug": "august",
        "sep": "september", "oct": "october", "nov": "november", "dec": "december",
    }
    return month_map.get(m, m)


def get_seasonal(month: str, region: str = "US") -> SeasonalProduce:
    """Get seasonal produce for a month and region."""
    month_key = _normalise_month(month)
    region_key = region.strip().upper()

    if region_key not in _PRODUCE:
        available = ", ".join(VALID_REGIONS)
        raise ValueError(f"Unknown region '{region}'. Valid: {available}")
    if month_key not in _PRODUCE[region_key]:
        available = ", ".join(_PRODUCE[region_key].keys())
        raise ValueError(f"Unknown month '{month}'. Valid: {available}")

    data = _PRODUCE[region_key][month_key]
    return SeasonalProduce(
        month=month.capitalize(),
        region=region,
        fruits=data["fruits"],
        vegetables=data["vegetables"],
    )


def format_seasonal(sp: SeasonalProduce) -> str:
    """Pretty-print seasonal produce info."""
    lines = [
        f"Seasonal produce — {sp.month} ({sp.region})",
        "",
        "Fruits:",
    ]
    for f in sp.fruits:
        lines.append(f"  - {f}")
    lines.append("")
    lines.append("Vegetables:")
    for v in sp.vegetables:
        lines.append(f"  - {v}")
    return "\n".join(lines)