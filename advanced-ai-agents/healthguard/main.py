"""HealthGuard — Multi-agent medication interaction & health query system.

Usage:
  python main.py check --drugs aspirin ibuprofen
  python main.py check --drugs warfarin aspirin ibuprofen --symptoms "chest pain" headache
  python main.py symptom headache fever
  python main.py condition hypertension
  python main.py info --drugs lisinopril
  python main.py interactive
"""

import sys
import typer
from typing import Optional as Opt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from agents.drug_checker import (
    check_all_interactions, get_drug_info,
)
from agents.symptom_triage import assess_multiple_symptoms
from agents.condition_researcher import search_multiple_conditions
from agents.report_compiler import compile_report, format_report

app = typer.Typer(help="HealthGuard — Your multi-agent health information system")
console = Console()


@app.command()
def check(
    drugs: Opt[list[str]] = typer.Option(None, "--drugs", "-d",
        help="Medications to check for interactions"),
    symptoms: Opt[list[str]] = typer.Option(None, "--symptoms", "-s",
        help="Symptoms to assess"),
    conditions: Opt[list[str]] = typer.Option(None, "--conditions", "-c",
        help="Conditions to research"),
):
    """Run the full multi-agent health check pipeline."""
    interactions = []
    symptom_results = []
    condition_results = []

    # Agent 1: Drug Interaction Checker
    if drugs:
        with console.status("[bold green]Agent 1: Checking drug interactions..."):
            interactions = check_all_interactions(drugs)
        _show_interactions(drugs, interactions)

    # Agent 2: Symptom Triage
    if symptoms:
        with console.status("[bold yellow]Agent 2: Triaging symptoms..."):
            symptom_results = assess_multiple_symptoms(symptoms)
        _show_symptoms(symptom_results)

    # Agent 3: Condition Researcher
    if conditions or any(
        s.possible_conditions for s in symptom_results
    ):
        all_conditions = list(conditions or [])
        # Collect conditions from symptom assessments
        cond_names = set()
        for s in symptom_results:
            for c in s.possible_conditions:
                cond_names.add(c)
        all_conditions.extend(sorted(cond_names)[:5])

        if all_conditions:
            with console.status("[bold blue]Agent 3: Researching conditions..."):
                condition_results = search_multiple_conditions(all_conditions)
            _show_conditions(condition_results)

    # Agent 4: Report Compiler
    with console.status("[bold magenta]Agent 4: Compiling report..."):
        report = compile_report(interactions, symptom_results, condition_results)

    console.print("\n[bold]📋 FINAL REPORT[/bold]")
    console.print(Panel(format_report(report), title="HealthGuard Report"))


@app.command()
def symptom(
    symptoms: list[str] = typer.Argument(..., help="Symptoms to assess"),
):
    """Assess symptoms and get triage recommendations (Agent 2 only)."""
    with console.status("[bold yellow]Agent 2: Triaging symptoms..."):
        results = assess_multiple_symptoms(symptoms)
    _show_symptoms(results)
    report = compile_report(symptoms=results)
    console.print(Panel(format_report(report), title="Symptom Assessment"))


@app.command()
def condition(
    conditions: list[str] = typer.Argument(..., help="Conditions to research"),
):
    """Research medical conditions from MedlinePlus and local DB (Agent 3 only)."""
    with console.status("[bold blue]Agent 3: Researching conditions..."):
        results = search_multiple_conditions(conditions)
    _show_conditions(results)
    report = compile_report(conditions=results)
    console.print(Panel(format_report(report), title="Condition Research"))


@app.command()
def info(
    drugs: list[str] = typer.Option(..., "--drugs", "-d",
        help="Drug names to look up"),
):
    """Look up drug information (Agent 1 data only)."""
    for drug in drugs:
        info = get_drug_info(drug)
        table = Table(title=f"Drug: {info.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("RxNorm ID", info.rxcui or "N/A")
        table.add_row("Generic Name", info.generic_name or "N/A")
        table.add_row("Brand Names", ", ".join(info.brand_names) or "N/A")
        table.add_row("Source", info.source)
        console.print(table)


@app.command()
def interactive():
    """Run HealthGuard in interactive mode — ask questions in natural language."""
    console.print("[bold]HealthGuard Interactive Mode[/bold]")
    console.print("Enter medications (comma-separated), symptoms, or 'quit' to exit.\n")

    while True:
        try:
            line = console.input("[cyan]healthguard>[/cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            break

        words = [w.strip() for w in line.split(",") if w.strip()]
        drugs = []
        symptoms = []

        # Simple heuristic: words > 3 chars that aren't symptom keywords → drug
        symptom_keywords = {"pain", "ache", "hurt", "fever", "rash", "swelling",
                           "dizziness", "nausea", "vomiting", "bleeding",
                           "chest", "breath", "headache"}
        for w in words:
            if any(k in w.lower() for k in symptom_keywords):
                symptoms.append(w)
            else:
                drugs.append(w)

        if drugs or symptoms:
            check(drugs=drugs or None, symptoms=symptoms or None)
        else:
            console.print("[yellow]No drugs or symptoms detected. Try: aspirin, ibuprofen[/yellow]")


def _show_interactions(drugs: list[str], interactions: list) -> None:
    if not interactions:
        return
    table = Table(title=f"Drug Interactions: {', '.join(drugs)}")
    table.add_column("Drug A", style="cyan")
    table.add_column("Drug B", style="cyan")
    table.add_column("Severity", style="yellow")
    table.add_column("Found", style="green")
    table.add_column("Suggestion", style="white", no_wrap=False)

    for i in interactions:
        sev_color = {
            "low": "green",
            "moderate": "yellow",
            "high": "red",
            "severe": "bold red",
        }.get(i.severity.value, "white")
        table.add_row(
            i.drug_a,
            i.drug_b,
            f"[{sev_color}]{i.severity.value.upper()}[/{sev_color}]",
            "✅" if i.interaction_found else "❌",
            i.management[:80] if i.management else "",
        )
    console.print(table)


def _show_symptoms(results: list) -> None:
    if not results:
        return
    table = Table(title="Symptom Assessment")
    table.add_column("Symptom", style="cyan")
    table.add_column("Urgency", style="yellow")
    table.add_column("Possible", style="white", no_wrap=False)
    table.add_column("Care Needed?", style="red")

    for s in results:
        table.add_row(
            s.symptom,
            s.urgency.value.upper(),
            ", ".join(s.possible_conditions[:3]),
            "🚨 YES" if s.requires_immediate_care else "No",
        )
    console.print(table)


def _show_conditions(results: list) -> None:
    if not results:
        return
    for c in results:
        md = Markdown(f"**{c.name}** — {c.description[:200]}")
        console.print(Panel(md, title=f"Condition: {c.name}"))


def main():
    if len(sys.argv) == 1:
        interactive()
    else:
        app()


if __name__ == "__main__":
    main()