"""Formatter module — pretty ANSI terminal output using Rich."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _color_country(code: str) -> str:
    """Simple country code colouring helper (just a visual flourish)."""
    colors = {
        "US": "cyan",
        "GB": "red",
        "FR": "yellow",
        "DE": "green",
        "IT": "magenta",
        "ES": "yellow",
        "CA": "red",
        "AU": "green",
        "BR": "green",
        "IN": "blue",
        "CN": "red",
        "JP": "red",
        "RU": "red",
    }
    return colors.get(code, "white")


def print_profile(name: str, data: dict[str, Any]) -> None:
    """Print the full name profile to the terminal."""
    age_data = data.get("age", {})
    gender_data = data.get("gender", {})
    nationality_data = data.get("nationality", {})
    rhymes = data.get("rhymes", [])
    llm_profile = data.get("llm_profile", "")

    # Title
    title = Text(f"📊  NameSage — Profile: {name}", style="bold cyan")
    console.print()
    console.print(title)
    console.print("─" * 50)

    # Age panel
    if "error" in age_data:
        console.print(Panel(f"⚠️ {age_data['error']}", title="⏳ Age"))
    elif age_data and age_data.get("age") is not None:
        age = age_data["age"]
        count = age_data.get("count", 0)
        age_text = Text()
        age_text.append(f"Predicted age: ", style="bold")
        age_text.append(f"{age}", style="bold green")
        age_text.append(f"  (based on {count:,} records)" if count else "")
        console.print(Panel(age_text, title="⏳ Age"))
    else:
        console.print(Panel("No age data available.", title="⏳ Age"))

    # Gender panel
    if "error" in gender_data:
        console.print(Panel(f"⚠️ {gender_data['error']}", title="⚧ Gender"))
    elif gender_data and gender_data.get("gender"):
        gender = gender_data["gender"]
        probability = gender_data.get("probability", 0)
        pct = probability * 100
        gender_text = Text()
        gender_text.append(f"Gender: ", style="bold")
        gender_text.append(f"{gender.capitalize()}", style="bold green")
        gender_text.append(f"\nProbability: {pct:.1f}%")
        console.print(Panel(gender_text, title="⚧ Gender"))
    else:
        console.print(Panel("No gender data available.", title="⚧ Gender"))

    # Nationality table
    if "error" in nationality_data:
        console.print(Panel(f"⚠️ {nationality_data['error']}", title="🌍 Nationality"))
    elif nationality_data and nationality_data.get("country"):
        countries = nationality_data["country"]
        table = Table(title="🌍 Country Probabilities")
        table.add_column("Country", style="bold")
        table.add_column("Probability", justify="right")
        for c in countries[:5]:  # top 5
            country_code = c.get("country_id", "??")
            prob = c.get("probability", 0)
            colored_code = f"[{_color_country(country_code)}]{country_code}[/]"
            table.add_row(colored_code, f"{prob * 100:.1f}%")
        console.print(Panel(table, title="🌍 Nationality"))
    else:
        console.print(Panel("No nationality data available.", title="🌍 Nationality"))

    # Rhymes
    rhyme_words = [r.get("word", "") for r in rhymes if "word" in r and "error" not in r]
    if rhyme_words:
        console.print(Panel(
            ", ".join(rhyme_words[:15]),
            title="🎵 Rhyming Words",
        ))

    # LLM Profile
    if llm_profile:
        console.print()
        console.print(Text("✨ LLM Name Profile", style="bold magenta"))
        console.print("─" * 50)
        console.print(llm_profile)
        console.print("─" * 50)

    console.print()