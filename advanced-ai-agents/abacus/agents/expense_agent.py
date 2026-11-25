"""Expense Agent — categorizes spending, calculates surplus, finds savings."""

from models import FinancialProfile, Expense, ExpenseCategory


class ExpenseAgent:
    """Analyzes expenses: categorization, essential vs discretionary split,
    savings opportunities."""

    def __init__(self):
        self.name = "ExpenseAgent"

    def process(self, profile: FinancialProfile) -> FinancialProfile:
        """Analyze expenses on the profile and identify savings opportunities."""
        total_expenses = profile.total_expenses_monthly()
        essential_total = sum(e.amount for e in profile.expenses if e.essential)
        discretionary_total = total_expenses - essential_total
        surplus = profile.total_income_net_monthly() - total_expenses

        print(f"  [ExpenseAgent] ${total_expenses:,.0f}/mo expenses "
              f"(${essential_total:,.0f} essential + ${discretionary_total:,.0f} discretionary) "
              f"→ ${surplus:,.0f}/mo surplus")
        return profile

    def parse_expense_line(self, text: str) -> Expense:
        """Parse a free-text expense description into structured Expense."""
        text = text.strip()
        if not text:
            raise ValueError("Empty expense description")

        amount = 0.0
        category = ExpenseCategory.OTHER
        name = text
        essential = True

        import re
        amounts = re.findall(r'\$?([\d,]+(?:\.\d+)?)', text.replace(',', ''))
        if amounts:
            amount = float(amounts[0])

        tl = text.lower()
        if any(w in tl for w in ['rent', 'mortgage', 'housing']):
            category = ExpenseCategory.HOUSING
            essential = True
        elif any(w in tl for w in ['grocer', 'food', 'dining', 'restaurant', 'meal']):
            category = ExpenseCategory.FOOD
            essential = 'grocer' in tl or 'food' in tl
        elif any(w in tl for w in ['transit', 'uber', 'lyft', 'gas', 'fuel', 'car', 'metro']):
            category = ExpenseCategory.TRANSPORT
            essential = True
        elif any(w in tl for w in ['electric', 'water', 'internet', 'phone', 'utility']):
            category = ExpenseCategory.UTILITIES
            essential = True
        elif any(w in tl for w in ['health', 'insurance', 'doctor', 'medic']):
            category = ExpenseCategory.HEALTHCARE
            essential = True
        elif any(w in tl for w in ['netflix', 'spotify', 'subscription', 'entertain']):
            category = ExpenseCategory.ENTERTAINMENT
            essential = False
        elif any(w in tl for w in ['debt', 'loan', 'credit card', 'payment']):
            category = ExpenseCategory.DEBT
            essential = True
        elif any(w in tl for w in ['saving', 'invest', '401k', 'ira']):
            category = ExpenseCategory.SAVINGS
            essential = True

        return Expense(
            name=name,
            amount=amount,
            category=category,
            essential=essential,
        )