# DebtSlayer — Multi-Agent Debt Payoff Optimizer

**💰 Take control of your debt with a coordinated team of AI agents.**

DebtSlayer is a multi-agent orchestration system that creates a personalized debt payoff plan, helps you negotiate with creditors, and tracks your progress. Instead of a single monolithic calculator, DebtSlayer uses specialized agents that each handle one aspect of debt management — tracking balances, analyzing your spending, computing the optimal payoff strategy, drafting negotiation letters, and monitoring your journey to zero debt.

## How It Works

```
You → CLI (describe your debts)
        │
        ├── Creditor Agent     → Tracks each debt (balance, APR, minimum)
        ├── Spending Agent     → Analyzes income vs expenses for surplus
        ├── Strategy Agent     → Computes avalanche vs snowball plans
        ├── Letter Agent       → Drafts creditor negotiation letters (LLM)
        └── Progress Agent     → Reports timeline and milestone tracking
        │
        └── Coordinator Agent  → Orchestrates the team, presents unified plan
```

## Installation

```bash
# Clone the repo (if you haven't)
cd LLM-Apps/debtslayer/

# Install dependencies
pip install -r requirements.txt
```

## Usage

**Interactive setup** — enter debts one by one:

```bash
python3 -m debtslayer
```

**Quick one-shot from arguments:**

```bash
python3 -m debtslayer \
  --debt "Visa:4500:22.99:50" \
  --debt "Mastercard:3200:18.0:40" \
  --debt "StudentLoan:15000:5.5:200" \
  --income 4800 --expenses 3200
```

Format: `Label:Balance:APR:MinimumPayment`

**Generate a negotiation letter:**

```bash
python3 -m debtslayer letter \
  --creditor "Visa" \
  --balance 4500 \
  --apr 22.99 \
  --hardship "reduced hours at work"
```

**Track progress (from saved plan file):**

```bash
python3 -m debtslayer progress --plan debtslayer_plan_2026-10-20.json
```

## What You Get

1. **Complete debt inventory** — all debts in one view
2. **Two payoff plans** — avalanche (highest APR first) and snowball (smallest balance first) with timelines and total interest
3. **Recommended strategy** — the coordinator analyzes your situation and picks the best approach
4. **Creditor negotiation letters** — personalized hardship letters you can mail/email
5. **Progress tracking** — save your plan and check in to see how you're doing

## Example

```
$ python3 -m debtslayer \
  --debt "Visa:4500:22.99:50" \
  --debt "Mastercard:3200:18.0:40" \
  --debt "StudentLoan:15000:5.5:200" \
  --income 4800 --expenses 3200

╔══════════════════════════════════════════════════════╗
║              DEBTSLAYER — DEBT INVENTORY             ║
╠══════════════════════════════════════════════════════╣
║ 1. Visa ......... $4,500.00 @ 22.99% (min $50/mo)   ║
║ 2. Mastercard ... $3,200.00 @ 18.00% (min $40/mo)   ║
║ 3. StudentLoan .. $15,000.00 @ 5.50% (min $200/mo)  ║
╠══════════════════════════════════════════════════════╣
║ Total Debt: $22,700.00  |  Surplus: $1,600/mo       ║
╚══════════════════════════════════════════════════════╝

🏆 RECOMMENDED: Avalanche Method (highest APR first)

📅 Payoff Timeline: 16 months | Total Interest: $2,847
💰 Interest Saved vs Minimums: $6,320

📄 Generated negotiation letter for Visa...
📄 Generated negotiation letter for Mastercard...
```

## Running Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/ -v
```

## Project Structure

```
debtslayer/
├── __main__.py          # CLI entry point (argparse)
├── __init__.py
├── coordinator.py       # Orchestration agent — manages the team
├── agents/
│   ├── __init__.py
│   ├── creditor_agent.py   # Tracks individual debt accounts
│   ├── spending_agent.py   # Analyzes income/expenses
│   ├── strategy_agent.py   # Avalanche vs snowball computation
│   ├── letter_agent.py     # LLM-powered negotiation letters
│   └── progress_agent.py   # Payoff timeline & progress tracking
├── models.py            # Data models (Debt, Plan, Letter)
├── tests/
│   ├── test_strategy.py
│   ├── test_models.py
│   └── test_coordinator.py
├── requirements.txt
├── README.md
├── Decisions.md
└── Flow.md
```