"""Income Agent — parses income descriptions, estimates taxes, projects growth."""

from models import IncomeStream, IncomeType, FinancialProfile


class IncomeAgent:
    """Models income streams: parses descriptions, estimates taxes, projects forward."""

    def __init__(self):
        self.name = "IncomeAgent"

    def process(self, profile: FinancialProfile) -> FinancialProfile:
        """Analyze existing income streams and return enriched profile."""
        # Each income stream already has tax_rate and growth_rate set
        # This agent provides the 'big picture' income analysis
        total_gross = sum(s.amount for s in profile.income_streams)
        total_net_monthly = profile.total_income_net_monthly()

        print(f"  [IncomeAgent] {len(profile.income_streams)} stream(s), "
              f"${total_gross:,.0f}/yr gross → ${total_net_monthly:,.0f}/mo net")
        return profile

    def parse_income_line(self, text: str) -> IncomeStream:
        """Parse a free-text income description into a structured IncomeStream.
        e.g. 'salary 85000' or 'freelance web dev 45000'.
        """
        text = text.strip()
        if not text:
            raise ValueError("Empty income description")

        amount = 0.0
        income_type = IncomeType.OTHER
        name = text

        # Try to extract a dollar amount
        import re
        amounts = re.findall(r'\$?([\d,]+(?:\.\d+)?)', text.replace(',', ''))
        if amounts:
            amount = float(amounts[0])

        # Detect income type from keywords
        tl = text.lower()
        if any(w in tl for w in ['salary', 'wage', 'full-time', 'employment']):
            income_type = IncomeType.SALARY
        elif any(w in tl for w in ['freelance', 'contract', 'gig', 'consulting']):
            income_type = IncomeType.FREELANCE
        elif any(w in tl for w in ['passive', 'dividend', 'rental', 'royalty']):
            income_type = IncomeType.PASSIVE
        elif any(w in tl for w in ['business', 'llc', 'side hustle']):
            income_type = IncomeType.BUSINESS

        return IncomeStream(
            name=name if amount else text,
            amount=amount,
            income_type=income_type,
        )