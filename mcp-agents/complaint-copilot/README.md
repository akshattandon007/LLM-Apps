# ⚖️ Complaint Copilot — MCP Server for Consumer Complaints

> *Gets your money back from the company that messed up, step by step.*

**Complaint Copilot** helps everyday people draft formal complaints, find the right ombudsman/regulator, quote their consumer rights, track escalation, and generate regulatory referrals. Delayed flight, defective product, overcharge, landlord dispute — no more eating the loss.

## MCP Tools

| Tool | Description |
|------|-------------|
| `draft_complaint(company, issue, amount, outcome)` | Formal complaint letter with relevant law and deadline |
| `find_ombudsman(company, issue_type)` | Right regulator/ombudsman with URL and eligibility |
| `statutory_rights(issue_type, country)` | What the user is owed and deadline to claim |
| `track_complaint(company, reference)` | Status template and recommended next action |
| `escalate_to_regulator(company, ombudsman, case_summary)` | Formal referral letter to the regulatory body |

## Issue Types Covered

| Issue | Example | 
|-------|---------|
| ✈️ Delayed/Cancelled Flight | UK EU261 £350+, US DOT compensation |
| 📦 Defective Product | Return, refund, replacement rights |
| 💳 Overcharge/Billing Error | Unauthorized charges, billing mistakes |
| 🔧 Poor Service | Substandard work, missed appointments |
| 🏠 Landlord/Tenant | Repairs, deposit disputes, evictions |
| 🛡️ Warranty Claim | Manufacturer warranty enforcement |
| 📝 Contract Dispute | Breach of contract, unfair terms |

## Countries Covered

| Country | Key Regulators |
|---------|---------------|
| 🇺🇸 US | FTC, CFPB, DOT, State Attorney Generals |
| 🇬🇧 UK | Citizens Advice, CAA, Financial Ombudsman, Energy Ombudsman |
| 🇪🇺 EU | ECC-Net, national consumer agencies |

## Usage

```bash
# Draft a complaint
python main.py draft "British Airways" "delayed flight" 350 "compensation"

# Find the right ombudsman
python main.py ombudsman "British Airways" "delayed flight"

# Check your statutory rights
python main.py rights "delayed flight" "UK"

# Start the MCP server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
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