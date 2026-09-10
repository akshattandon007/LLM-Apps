"""Career Compass — CLI entry point for testing.

Runs career tools directly from the command line without starting the MCP server.
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .industries import growing_industries, job_outlook
from .offers import compare_offer
from .paths import career_path
from .salary import salary_by_role
from .skills import skills_gap

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Career Compass — data-driven career answers")
    sub = parser.add_subparsers(dest="command", required=True)

    # salary
    salary_parser = sub.add_parser("salary", help="Get salary data for a role")
    salary_parser.add_argument("job_title", help="Job title (e.g. 'Software Developer')")
    salary_parser.add_argument("--zip", default="", help="ZIP code for COL adjustment")

    # industries
    ind_parser = sub.add_parser("industries", help="Get growing industries")
    ind_parser.add_argument("--region", default="", help="Region filter")

    # skills-gap
    gap_parser = sub.add_parser("skills-gap", help="Analyze skills gap between roles")
    gap_parser.add_argument("current", help="Current job title")
    gap_parser.add_argument("target", help="Target job title")

    # career-path
    path_parser = sub.add_parser("career-path", help="Map career progression")
    path_parser.add_argument("entry_job", help="Entry-level job title")
    path_parser.add_argument("--years", type=int, default=10, help="Years to project")

    # compare-offer
    offer_parser = sub.add_parser("compare-offer", help="Evaluate a job offer")
    offer_parser.add_argument("salary", type=float, help="Annual base salary")
    offer_parser.add_argument("--location", default="", help="Location (zip or city)")
    offer_parser.add_argument("--bonus", type=float, default=0.0, help="Signing bonus")
    offer_parser.add_argument("--bonus-pct", type=float, default=0.0, help="Annual bonus %")
    offer_parser.add_argument("--equity", type=float, default=0.0, help="Annual equity value")
    offer_parser.add_argument("--relocation", type=float, default=0.0, help="Relocation amount")
    offer_parser.add_argument("--employer", default="", help="Employer name")

    # outlook
    outlook_parser = sub.add_parser("outlook", help="Get job outlook")
    outlook_parser.add_argument("occupation", help="Occupation title")
    outlook_parser.add_argument("--region", default="", help="Region filter")

    args = parser.parse_args()

    match args.command:
        case "salary":
            result = salary_by_role(args.job_title, args.zip)
            print(f"Occupation: {result.occupation}")
            print(f"Median wage: ${result.median_wage:,}")
            print(f"10th percentile: ${result.p10_wage:,}")
            print(f"90th percentile: ${result.p90_wage:,}")
            print(f"COL index: {result.cost_of_living_index}")
            print(f"COL-adjusted median: ${result.adjusted_median_wage:,}")
            print(f"Source: {result.data_source}")

        case "industries":
            result = growing_industries(args.region)
            print(f"Growing Industries: {result.region}")
            for ind in result.industries:
                print(f"\n  {ind.industry_name}")
                print(f"    Growth rate: {ind.projected_growth_rate:.1%}")
                print(f"    Jobs added: {ind.projected_jobs_added:,}")
                print(f"    Key regions: {', '.join(ind.key_regions)}")

        case "skills-gap":
            result = skills_gap(args.current, args.target)
            print(f"Skills Gap: {result.current_title} → {result.target_title}")
            for gap in result.gaps:
                print(f"\n  {gap.skill_name} ({gap.importance})")
                courses = "; ".join(gap.typical_courses)
                print(f"    Courses: {courses}")
                print(f"    Cost: {gap.typical_cost_range}")

        case "career-path":
            result = career_path(args.entry_job, args.years)
            print(f"Career Path: {result.entry_job} ({result.years} years)")
            for step in result.steps:
                print(f"\n  Step {step.step}: {step.title} (year {step.years_to_reach})")
                print(f"    Salary: ${step.salary_range}")
                print(f"    {step.description}")

        case "compare-offer":
            result = compare_offer(
                args.salary,
                location=args.location,
                signing_bonus=args.bonus,
                annual_bonus_pct=args.bonus_pct,
                equity=args.equity,
                relocation=args.relocation,
                employer=args.employer,
            )
            print(f"Base salary: ${args.salary:,.2f}")
            print(f"Total compensation: ${result.total_compensation:,.2f}")
            print(f"COL index: {result.cost_of_living_index}")
            print(f"Purchasing power: ${result.effective_purchasing_power:,.2f}")
            print("\nBreakdown:")
            for key, val in result.breakdown.items():
                print(f"  {key}: ${val:,.2f}")

        case "outlook":
            result = job_outlook(args.occupation, args.region)
            print(f"Occupation: {result.occupation}")
            print(f"Region: {result.region}")
            print(f"Growth rate: {result.projected_growth_rate:.1%}")
            print(f"Outlook: {result.growth_outlook.value}")
            print(f"Annual openings: {result.annual_openings:,}")
            print(f"Key industries: {', '.join(result.key_industries)}")

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()