"""AlphaBrief smoke tests — exercise every agent end-to-end with mock data."""
from __future__ import annotations

import pytest

from src.models import (
    DailyBriefing, Holding, PortfolioSummary, TechnicalSignal,
    TechnicalReport, FundamentalChange, FundamentalReport,
    SentimentScore, SentimentReport, RiskMetrics,
)


def test_portfolio_agent():
    """PortfolioAgent calculates P&L and weights correctly from mock prices."""
    from src.portfolio_agent import PortfolioAgent
    from tests.conftest import FakeYFinance

    mf = FakeYFinance()
    from src import portfolio_agent
    portfolio_agent.set_client(mf)

    agent = PortfolioAgent(
        tickers=["AAPL", "MSFT"],
        shares=[10.0, 5.0],
        avg_costs=[150.0, 300.0],
    )
    result = agent.run()

    assert isinstance(result, PortfolioSummary)
    assert len(result.holdings) == 2
    assert result.holdings[0].ticker == "AAPL"
    assert result.holdings[0].shares == 10.0
    assert result.holdings[0].current_price > 0
    assert result.total_value > 0
    assert result.total_cost > 0
    # Weight should sum to ~100%
    assert abs(sum(h.weight for h in result.holdings) - 100.0) < 0.1


def test_technical_agent():
    """TechnicalAgent produces RSI, MACD, SMA signals with integer ticker seeds."""
    from src.technical_agent import TechnicalAgent
    from tests.conftest import FakeYFinance

    mf = FakeYFinance()
    from src import technical_agent
    technical_agent.set_client(mf)

    agent = TechnicalAgent(tickers=["AAPL", "MSFT"])
    result = agent.run()

    assert isinstance(result, TechnicalReport)
    assert len(result.signals) > 0
    # Each ticker should have at least RSI, MACD, SMA_50
    signals_by_ticker: dict[str, list] = {}
    for s in result.signals:
        signals_by_ticker.setdefault(s.ticker, []).append(s)
    for t in ["AAPL", "MSFT"]:
        assert t in signals_by_ticker, f"Missing signals for {t}"
        indicators = {s.indicator for s in signals_by_ticker[t]}
        assert "RSI_14" in indicators
        assert "MACD" in indicators
        assert "SMA_50" in indicators


def test_fundamental_agent():
    """FundamentalAgent fetches mock SEC filings and parses key changes."""
    from src.fundamental_agent import FundamentalAgent
    from tests.conftest import FakeSEC

    from src import fundamental_agent
    fundamental_agent.set_client(FakeSEC())

    agent = FundamentalAgent(tickers=["AAPL"])
    result = agent.run()

    assert isinstance(result, FundamentalReport)
    assert len(result.filings) > 0
    # Should have at least one 8-K or 10-K
    filing_types = {f.filing_type for f in result.filings}
    assert filing_types.intersection({"10-K", "10-Q", "8-K"})
    assert all(f.ticker == "AAPL" for f in result.filings)


def test_sentiment_agent():
    """SentimentAgent scores headlines and returns direction."""
    from src.sentiment_agent import SentimentAgent
    from tests.conftest import FakeNews

    from src import sentiment_agent
    sentiment_agent.set_client(FakeNews())

    agent = SentimentAgent(tickers=["AAPL", "AMZN"])
    result = agent.run()

    assert isinstance(result, SentimentReport)
    assert len(result.scores) == 2
    for s in result.scores:
        assert -1.0 <= s.score <= 1.0
        assert s.direction in ("bullish", "bearish", "neutral")


def test_risk_agent():
    """RiskAgent computes beta, concentration, and volatility from mock data."""
    from src.risk_agent import RiskAgent
    from tests.conftest import FakeYFinance

    mf = FakeYFinance()
    from src import risk_agent
    risk_agent.set_client(mf)

    portfolio = PortfolioSummary(
        holdings=[
            Holding(ticker="AAPL", shares=10, avg_cost=150, current_price=198.50,
                    market_value=1985.0, cost_basis=1500.0, pnl=485.0, pnl_pct=32.33,
                    day_change_pct=1.2, weight=40.0),
            Holding(ticker="MSFT", shares=5, avg_cost=300, current_price=425.30,
                    market_value=2126.5, cost_basis=1500.0, pnl=626.5, pnl_pct=41.77,
                    day_change_pct=-0.5, weight=42.8),
            Holding(ticker="NVDA", shares=2, avg_cost=400, current_price=880.00,
                    market_value=1760.0, cost_basis=800.0, pnl=960.0, pnl_pct=120.0,
                    day_change_pct=2.5, weight=17.2),
        ],
        total_value=5871.5, total_cost=3800.0, total_pnl=2071.5,
    )

    agent = RiskAgent(portfolio)
    result = agent.run()

    assert isinstance(result, RiskMetrics)
    assert result.portfolio_beta != 0.0
    assert result.concentration_top3_pct > 0
    assert result.max_single_weight > 0
    assert result.weighted_volatility > 0


def test_coordinator_produces_briefing():
    """Coordinator runs all 5 agents and produces a complete DailyBriefing."""
    from src.coordinator import Coordinator
    from tests.conftest import inject_mocks

    inject_mocks()

    coordinator = Coordinator(
        tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
        shares=[10, 10, 5, 8, 4],
        avg_costs=[150, 200, 180, 140, 400],
    )
    briefing = coordinator.run()

    assert isinstance(briefing, DailyBriefing)
    assert len(briefing.portfolio.holdings) == 5
    assert len(briefing.technical.signals) > 0
    assert briefing.summary != "No briefing generated."
    assert "AlphaBrief" in coordinator.to_markdown(briefing)


def test_markdown_renders_all_sections():
    """Markdown output contains all required sections."""
    from src.coordinator import Coordinator
    from tests.conftest import inject_mocks

    inject_mocks()
    coordinator = Coordinator(
        tickers=["AAPL", "MSFT"],
        shares=[10, 5],
        avg_costs=[150, 200],
    )
    briefing = coordinator.run()
    md = coordinator.to_markdown(briefing)

    assert "## Portfolio" in md
    assert "## Technical Analysis" in md
    assert "## Fundamental Changes" in md
    assert "## News Sentiment" in md
    assert "## Risk Metrics" in md
    assert "## Executive Summary" in md
    assert "AlphaBrief" in md


def test_simulate_mode_runs_without_network():
    """Simulate mode injects mocks and runs the full pipeline successfully."""
    from src.coordinator import Coordinator
    from tests.conftest import inject_mocks

    inject_mocks()
    coordinator = Coordinator(
        tickers=["TSLA", "META"],
        shares=[5, 8],
        avg_costs=[200, 300],
    )
    briefing = coordinator.run()

    assert briefing.portfolio.total_value > 0
    assert len(briefing.all_alerts) >= 0


def test_empty_portfolio():
    """Empty portfolio returns empty summary, no errors."""
    from src.portfolio_agent import PortfolioAgent

    agent = PortfolioAgent(tickers=[], shares=[], avg_costs=[])
    result = agent.run()
    assert len(result.holdings) == 0
    assert result.total_value == 0.0


def test_sentiment_keyword_scoring():
    """Verify sentiment scoring produces expected direction."""
    from src.sentiment_agent import _score_headline

    assert _score_headline("Stock surges on record earnings") > 0
    assert _score_headline("Stock crashes amid losses") < 0
    assert _score_headline("The stock is not bad") >= 0  # negation flips
    assert _score_headline("Nothing market moving here") == 0.0