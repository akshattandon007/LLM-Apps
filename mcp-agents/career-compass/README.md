# 🧭 Career Compass — MCP Server for Career Intelligence

> *What jobs actually pay, what skills get you hired, and how to switch — no recruiter needed.*

**Career Compass** is an MCP server that gives AI agents the tools to help people understand their earning potential, find growing industries, identify skills gaps, map career progression, and evaluate job offers. Powered by BLS wage data and regional cost-of-living adjustments.

## MCP Tools

| Tool | Description |
|------|-------------|
| `salary_by_role(job_title, zip_code)` | Median wage + 10th/90th percentile with cost-of-living adjustment |
| `growing_industries(region)` | Projected growth sectors with real job counts |
| `skills_gap(current_title, target_title)` | Certifications and courses needed to transition |
| `career_path(entry_job, years)` | Realistic progression with salary milestones |
| `compare_offer(salary, benefits, location)` | Total compensation breakdown with COL adjustment |
| `job_outlook(occupation, region)` | Projected demand, growth rate, and key hiring areas |

## Usage

```bash
# Check salary for a role
python main.py salary "registered nurse" "85001"

# See growing industries
python main.py industries "Phoenix"

# Identify skills gap
python main.py gap "retail manager" "pharmacy tech"

# Compare a job offer
python main.py offer --salary 72000 --bonus 5000 --location "Denver"

# Start the MCP server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py salary "software developer" "10001"
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |