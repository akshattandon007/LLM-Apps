"""Coordinator — runs all 5 agents and synthesises the daily briefing.

The coordinator orchestrates the multi-agent pipeline and produces a
structured markdown briefing with specific alerts.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from .models import DailyBriefing, PortfolioSummary
from .portfolio_agent import PortfolioAgent
from .technical_agent import TechnicalAgent
from .fundamental_agent import FundamentalAgent
from .sentiment_agent import SentimentAgent
from .risk_agent import RiskAgent

logger = logging.getLogger(__name__)


class Coordinator:
    """Orchestrates the 5 specialist agents and synthesises results."""

    def __init__(self, tickers: list[str], shares: Optional[list[float]] = None,
                 avg_costs: Optional[list[float]] = None, simulate: bool = False) -> None:
        self.tickers = tickers
        self.shares = shares or [10.0] * len(tickers)
        self.avg_costs = avg_costs or [150.0] * len(tickers)
        self.simulate = simulate

    def run(self) -> DailyBriefing:
        briefing = DailyBriefing()

        # 1. Portfolio Agent
        logger.info("Running Portfolio Agent...")
        pa = PortfolioAgent(self.tickers, self.shares, self.avg_costs)
        briefing.portfolio = pa.run()

        # 2. Technical Agent
        logger.info("Running Technical Agent...")
        ta = TechnicalAgent(self.tickers)
        briefing.technical = ta.run()

        # 3. Fundamental Agent
        logger.info("Running Fundamental Agent...")
        fa = FundamentalAgent(self.tickers)
        briefing.fundamental = fa.run()

        # 4. Sentiment Agent
        logger.info("Running Sentiment Agent...")
        sa = SentimentAgent(self.tickers)
        briefing.sentiment = sa.run()

        # 5. Risk Agent
        logger.info("Running Risk Agent...")
        ra = RiskAgent(briefing.portfolio)
        briefing.risk = ra.run()

        # Synthesise
        briefing.all_alerts = (
            briefing.technical.alerts
            + briefing.fundamental.alerts
            + briefing.sentiment.alerts
            + briefing.risk.alerts
        )

        briefing.sections = {
            "portfolio": self._format_portfolio(briefing.portfolio),
            "technical": self._format_technical(briefing),
            "fundamental": self._format_fundamental(briefing),
            "sentiment": self._format_sentiment(briefing),
            "risk": self._format_risk(briefing),
        }

        briefing.summary = self._write_summary(briefing)
        return briefing

    def to_markdown(self, briefing: DailyBriefing) -> str:
        """Render the full briefing as structured markdown."""
        lines = [
            f"# AlphaBrief — Daily Briefing",
            f"**{briefing.briefing_date.isoformat()}** | Generated {briefing.generated_at.strftime('%H:%M UTC')}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            briefing.summary,
            "",
            "---",
            "",
        ]
        for section_key in ["portfolio", "technical", "fundamental", "sentiment", "risk"]:
            lines.append(briefing.sections.get(section_key, ""))
            lines.append("")

        if briefing.all_alerts:
            lines.append("---")
            lines.append("")
            lines.append("## All Alerts")
            for a in briefing.all_alerts:
                lines.append(f"- {a}")
            lines.append("")

        lines.append("---")
        lines.append(f"*AlphaBrief v0.1.0 — {briefing.briefing_date.isoformat()}*")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_portfolio(p: PortfolioSummary) -> str:
        lines = ["## Portfolio", ""]
        lines.append(f"| Ticker | Shares | Price | Value | Cost Basis | P&L | P&L % | Weight |")
        lines.append(f"|--------|--------|-------|-------|------------|-----|-------|--------|")
        for h in p.holdings:
            lines.append(
                f"| {h.ticker} | {h.shares:.0f} | ${h.current_price:.2f} | ${h.market_value:,.2f} | "
                f"${h.cost_basis:,.2f} | ${h.pnl:+,.2f} | {h.pnl_pct:+.2f}% | {h.weight:.1f}% |"
            )
        lines.append("")
        lines.append(f"**Total Value:** ${p.total_value:,.2f}")
        lines.append(f"**Total Cost:** ${p.total_cost:,.2f}")
        lines.append(f"**Total P&L:** ${p.total_pnl:+,.2f} ({p.total_pnl_pct:+.2f}%)")
        lines.append(f"**Cash Reserve:** ${p.cash:,.2f}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_technical(briefing: DailyBriefing) -> str:
        lines = ["## Technical Analysis", ""]
        if not briefing.technical.signals:
            lines.append("No technical signals available.")
            return "\n".join(lines)

        lines.append("| Ticker | Indicator | Value | Signal | Detail |")
        lines.append("|--------|-----------|-------|--------|--------|")
        for sig in briefing.technical.signals:
            emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(sig.signal, "⚪")
            lines.append(
                f"| {sig.ticker} | {sig.indicator} | {sig.value} | {emoji} {sig.signal.upper()} | {sig.detail} |"
            )
        lines.append("")
        if briefing.technical.alerts:
            lines.append("**Alerts:**")
            for a in briefing.technical.alerts:
                lines.append(f"- {a}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_fundamental(briefing: DailyBriefing) -> str:
        lines = ["## Fundamental Changes (SEC Filings)", ""]
        if not briefing.fundamental.filings:
            lines.append("No SEC filings found in recent period.")
            return "\n".join(lines)

        for f in briefing.fundamental.filings:
            lines.append(f"### {f.ticker} — {f.filing_type} ({f.filing_date})")
            lines.append("")
            lines.append(f"{f.summary}")
            if f.key_changes:
                lines.append("")
                lines.append("**Key Changes:**")
                for kc in f.key_changes:
                    lines.append(f"- {kc}")
            if f.risk_factors:
                lines.append("")
                lines.append("**Risk Factors:**")
                for rf in f.risk_factors:
                    lines.append(f"- {rf}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_sentiment(briefing: DailyBriefing) -> str:
        lines = ["## News Sentiment", ""]
        lines.append(f"**Overall Mood:** {briefing.sentiment.overall_mood.upper()}")
        lines.append("")
        if not briefing.sentiment.scores:
            lines.append("No sentiment data available.")
            return "\n".join(lines)

        lines.append("| Ticker | Score | Direction | Sources | Top Headline |")
        lines.append("|--------|-------|-----------|---------|--------------|")
        for s in briefing.sentiment.scores:
            emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(s.direction, "⚪")
            headline = s.top_headlines[0][:80] if s.top_headlines else "—"
            lines.append(
                f"| {s.ticker} | {s.score:+.4f} | {emoji} {s.direction.upper()} | {s.source_count} | {headline} |"
            )
        lines.append("")
        if briefing.sentiment.alerts:
            lines.append("**Alerts:**")
            for a in briefing.sentiment.alerts:
                lines.append(f"- {a}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_risk(briefing: DailyBriefing) -> str:
        lines = ["## Risk Metrics", ""]
        r = briefing.risk
        lines.append(f"- **Portfolio Beta:** {r.portfolio_beta:.2f}")
        lines.append(f"- **Weighted Volatility (daily):** {r.weighted_volatility:.2f}%")
        lines.append(f"- **Concentration (Top 3):** {r.concentration_top3_pct:.1f}%")
        lines.append(f"- **Max Single Holding:** {r.max_single_weight:.1f}%")
        lines.append(f"- **Correlation Alert:** {'YES' if r.correlation_alert else 'No'}")
        lines.append(f"- **Estimated Sharpe (annual):** {r.sharpe_ratio_est:.2f}")
        lines.append("")
        if r.alerts:
            lines.append("**Alerts:**")
            for a in r.alerts:
                lines.append(f"- {a}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _write_summary(briefing: DailyBriefing) -> str:
        """Write a concise 2-paragraph executive summary."""
        p = briefing.portfolio
        summary = (
            f"**Portfolio** — {len(p.holdings)} holdings, valued at ${p.total_value:,.2f}. "
            f"P&L: ${p.total_pnl:+,.2f} ({p.total_pnl_pct:+.2f}%)."
        )

        # Key alerts summary
        high_priority = [a for a in briefing.all_alerts if "bullish" in a.lower() or "bearish" in a.lower()
                         or "high concentration" in a.lower() or "death cross" in a.lower()
                         or "golden cross" in a.lower()
                         or "overbought" in a.lower() or "oversold" in a.lower()]
        if high_priority:
            summary += "\n\n**Key Alerts:**\n"
            for a in high_priority[:5]:
                summary += f"- {a}\n"
        else:
            summary += "\n\nNo significant alerts today. Markets are relatively stable."

        sentiment = briefing.sentiment.overall_mood
        beta = briefing.risk.portfolio_beta
        summary += (
            f"\n\n**Sentiment:** {sentiment.upper()} | "
            f"**Beta:** {beta:.2f} | "
            f"**Sharpe:** {briefing.risk.sharpe_ratio_est:.2f} | "
            f"**Technical Signals:** {len(briefing.technical.signals)}"
        )
        return summary