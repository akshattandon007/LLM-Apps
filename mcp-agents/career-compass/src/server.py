"""Career Compass MCP Server.

FastAPI + MCP SDK server that exposes career data tools for AI agents.
Each tool returns structured data for data-driven career answers.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from .industries import growing_industries, job_outlook
from .offers import compare_offer
from .paths import career_path
from .salary import salary_by_role
from .skills import skills_gap

load_dotenv()

# ── MCP Server Definition ──────────────────────────────────────────────────────

mcp = FastMCP(
    name="Career Compass",
    instructions="""I am Career Compass, an MCP server that provides data-driven career 
answers. I can tell you what jobs pay, what skills get you hired, and how to 
switch careers — no recruiter needed. My data is sourced from the Bureau of 
Labor Statistics (BLS) and related public data.""",
)


@mcp.tool()
def salary_by_role_tool(job_title: str, zip_code: str = "") -> str:
    """Get median wage, 10th/90th percentile, and cost-of-living adjusted salary for a job.

    Args:
        job_title: Job title (e.g. 'Software Developer', 'Registered Nurse').
        zip_code: Optional 5-digit US ZIP code for cost-of-living adjustment.
    """
    result = salary_by_role(job_title, zip_code)
    lines = [
        f"## Salary: {result.occupation}",
        f"Median Annual Wage: ${result.median_wage:,}",
        f"10th Percentile: ${result.p10_wage:,}",
        f"90th Percentile: ${result.p90_wage:,}",
        f"Cost-of-Living Index: {result.cost_of_living_index} (US avg = 100)",
        f"COL-Adjusted Median: ${result.adjusted_median_wage:,}",
        f"Data source: {result.data_source}",
    ]
    return "\n".join(lines)


@mcp.tool()
def growing_industries_tool(region: str = "") -> str:
    """Get projected growth sectors with real job counts.

    Args:
        region: Optional region filter (e.g. 'San Francisco', 'Texas', 'Midwest').
    """
    result = growing_industries(region)
    lines = [f"## Growing Industries: {result.region}", ""]
    for ind in result.industries:
        lines.extend([
            f"**{ind.industry_name}**",
            f"  Projected Growth: {ind.projected_growth_rate:.1%}",
            f"  Jobs Added: {ind.projected_jobs_added:,}",
            f"  Current Employment: {ind.current_employment:,}",
            f"  Key Regions: {', '.join(ind.key_regions)}",
            f"  Top Occupations: {', '.join(ind.top_occupations)}",
            "",
        ])
    return "\n".join(lines)


@mcp.tool()
def skills_gap_tool(current_title: str, target_title: str) -> str:
    """Identify certifications and courses needed to switch from one job to another.

    Args:
        current_title: Your current job title.
        target_title: The job title you want to move to.
    """
    result = skills_gap(current_title, target_title)
    lines = [
        f"## Skills Gap: {result.current_title} → {result.target_title}",
        "",
    ]
    if not result.gaps:
        lines.append("No specific gaps identified. Your current role already covers the key skills.")
    else:
        for gap in result.gaps:
            courses = "; ".join(gap.typical_courses) if gap.typical_courses else "Self-study"
            lines.extend([
                f"**{gap.skill_name}**",
                f"  Importance: {gap.importance}",
                f"  Category: {gap.category}",
                f"  Typical Courses: {courses}",
                f"  Estimated Cost: {gap.typical_cost_range}",
                "",
            ])
    return "\n".join(lines)


@mcp.tool()
def career_path_tool(entry_job: str, years: int = 10) -> str:
    """Get realistic career progression with salary milestones.

    Args:
        entry_job: Your entry-level job title.
        years: How many years you want to project forward (default 10).
    """
    result = career_path(entry_job, years)
    lines = [
        f"## Career Path: {result.entry_title}",
        f"Projection horizon: {result.years} years",
        "",
    ]
    for step in result.steps:
        lines.extend([
            f"**Step {step.step}: {step.title}** (year {step.years_to_reach})",
            f"  Salary Range: ${step.salary_range}",
            f"  {step.description}",
            f"  Promotion Path: {step.typical_promotion_path}",
            "",
        ])
    return "\n".join(lines)


@mcp.tool()
def compare_offer_tool(
    salary: float,
    benefits: str = "",
    location: str = "",
    signing_bonus: float = 0.0,
    annual_bonus_pct: float = 0.0,
    equity: float = 0.0,
    relocation: float = 0.0,
    employer: str = "",
) -> str:
    """Evaluate a job offer with total compensation breakdown and purchasing power.

    Args:
        salary: Annual base salary in USD.
        benefits: Brief description of benefits (free text, for context).
        location: City/ST or ZIP code for cost-of-living adjustment.
        signing_bonus: One-time signing bonus (default 0).
        annual_bonus_pct: Target annual bonus as % of base (default 0).
        equity: Annual equity value in USD (default 0).
        relocation: Relocation assistance amount in USD (default 0).
        employer: Employer name (optional).
    """
    result = compare_offer(salary, benefits, location, signing_bonus, annual_bonus_pct, equity, relocation, employer)

    lines = [
        f"## Offer Evaluation{': ' + employer if employer else ''}",
        "",
        f"**Base Salary:** ${salary:,.2f}",
        f"**Total Compensation:** ${result.total_compensation:,.2f}",
        f"**Cost-of-Living Index:** {result.cost_of_living_index} (US avg = 100)",
        f"**Effective Purchasing Power:** ${result.effective_purchasing_power:,.2f}",
        "",
        "### Breakdown",
    ]
    for key, val in result.breakdown.items():
        label = key.replace("_", " ").title()
        lines.append(f"  {label}: ${val:,.2f}")
    lines.append(f"\n*Data source: {result.data_source}*")
    return "\n".join(lines)


@mcp.tool()
def job_outlook_tool(occupation: str, region: str = "") -> str:
    """Get projected job demand, growth rate, and key hiring areas.

    Args:
        occupation: Occupation title (e.g. 'Software Developer').
        region: Optional region for localized outlook.
    """
    result = job_outlook(occupation, region)
    lines = [
        f"## Job Outlook: {result.occupation}",
        f"Region: {result.region}",
        "",
        f"**Growth Rate:** {result.projected_growth_rate:.1%}",
        f"**Outlook:** {result.growth_outlook.value.replace('_', ' ').title()}",
        f"**Current Estimated Employment:** {result.current_employment:,}",
        f"**Annual Openings:** {result.annual_openings:,}",
        "",
        "**Key Hiring Industries:**",
    ]
    for ind in result.key_industries:
        lines.append(f"  - {ind}")
    lines.append(f"\n*Data source: {result.data_source}*")
    return "\n".join(lines)


# ── FastAPI Wrapper ────────────────────────────────────────────────────────────


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Initialize MCP server tools on startup."""
    yield


app = FastAPI(title="Career Compass MCP Server", version="1.0.0", lifespan=_lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "career-compass"}


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run the FastAPI + MCP server."""
    # Mount the MCP server's SSE transport
    mcp_app = mcp.sse_app()

    # We integrate MCP via its own mount point
    @app.get("/mcp")
    async def mcp_info():
        """List available MCP tools."""
        tools = mcp._tool_manager.list_tools()
        return {"tools": [{"name": t.name, "description": t.description} for t in tools]}

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()