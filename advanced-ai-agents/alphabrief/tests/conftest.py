"""Test fixtures — mock data providers for all 5 agent types.

Each mock class is injected via the module-level set_client() functions.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd


def inject_mocks() -> None:
    """Inject all mock clients at once.  Called by --simulate mode."""
    from src import portfolio_agent, technical_agent, fundamental_agent, sentiment_agent, risk_agent

    mf = FakeYFinance()
    portfolio_agent.set_client(mf)
    technical_agent.set_client(mf)
    risk_agent.set_client(mf)

    fundamental_agent.set_client(FakeSEC())
    sentiment_agent.set_client(FakeNews())


# ---------------------------------------------------------------------------
# Mock price / hist data for yfinance-like clients
# ---------------------------------------------------------------------------

_MOCK_PRICES = {
    "AAPL": 198.50, "MSFT": 425.30, "GOOGL": 175.80,
    "AMZN": 178.20, "NVDA": 880.00, "SPY": 525.00,
    "TSLA": 245.60, "META": 510.20,
}


def _make_mock_hist(num_days: int = 252, base_price: float = 100.0,
                    ticker: str = "DUMMY") -> pd.DataFrame:
    """Generate a synthetic price series with realistic-ish movement."""
    np.random.seed(hash(ticker) % 2**31)
    returns = np.random.normal(0.0002, 0.015, num_days)
    prices = base_price * np.cumprod(1 + returns)
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(num_days)]
    return pd.DataFrame(
        {"Close": prices, "Open": prices * 0.998, "High": prices * 1.015, "Low": prices * 0.985, "Volume": 10_000_000},
        index=pd.DatetimeIndex(dates),
    )


class FakeYFinance:
    """Mock for yfinance.Ticker.history() and price lookups."""

    _hist_cache: dict[str, pd.DataFrame] = {}

    def get_prices(self, tickers: list[str]) -> dict[str, float]:
        return {t: _MOCK_PRICES.get(t, 100.0) for t in tickers}

    def get_day_changes(self, tickers: list[str]) -> dict[str, float]:
        changes = {
            "AAPL": 1.2, "MSFT": -0.5, "GOOGL": 0.8,
            "AMZN": -0.3, "NVDA": 2.5, "TSLA": -1.1, "META": 0.4,
        }
        return {t: changes.get(t, 0.0) for t in tickers}

    def get_hist(self, ticker: str, period: str = "6mo") -> pd.DataFrame:
        if ticker not in self._hist_cache:
            base = _MOCK_PRICES.get(ticker, 100.0)
            self._hist_cache[ticker] = _make_mock_hist(252, base, ticker)
        df = self._hist_cache[ticker]
        period_days = {"1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "2y": 504}
        n = period_days.get(period, 252)
        return df.tail(min(n, len(df))).copy()


# ---------------------------------------------------------------------------
# Mock SEC EDGAR data
# ---------------------------------------------------------------------------

_CIK_MAP = {
    "AAPL": "0000320193", "MSFT": "0000789019", "GOOGL": "0001652044",
    "AMZN": "0001018724", "NVDA": "0001045810",
}


class FakeSEC:
    """Mock for SEC EDGAR filings."""

    def get_cik(self, ticker: str) -> Optional[str]:
        return _CIK_MAP.get(ticker.upper())

    def get_filings(self, cik: str, filing_types: Optional[list[str]] = None) -> list[dict]:
        filing_types = filing_types or ["10-K", "10-Q", "8-K"]
        all_filings = {
            "10-K": [
                {"form": "10-K", "date": "2025-02-20", "primary_doc": "aapl-20240928.htm",
                 "description": "Annual report for fiscal year 2024",
                 "url": "https://sec.gov/archives/edgar/data/320193/aapl-20240928.htm"},
            ],
            "10-Q": [
                {"form": "10-Q", "date": "2025-05-10", "primary_doc": "aapl-20250329.htm",
                 "description": "Quarterly report Q2 2025",
                 "url": "https://sec.gov/archives/edgar/data/320193/aapl-20250329.htm"},
            ],
            "8-K": [
                {"form": "8-K", "date": "2025-06-01", "primary_doc": "aapl-8k-20250601.htm",
                 "description": "Current report — earnings release",
                 "url": "https://sec.gov/archives/edgar/data/320193/aapl-8k-20250601.htm"},
                {"form": "8-K", "date": "2025-06-15", "primary_doc": "aapl-8k-20250615.htm",
                 "description": "Current report — dividend declared",
                 "url": "https://sec.gov/archives/edgar/data/320193/aapl-8k-20250615.htm"},
            ],
        }
        results: list[dict] = []
        for ft in filing_types:
            results.extend(all_filings.get(ft, []))
        return results[:10]


# ---------------------------------------------------------------------------
# Mock News data
# ---------------------------------------------------------------------------

class FakeNews:
    """Mock for news headline fetcher."""

    _headlines: dict[str, list[str]] = {
        "AAPL": [
            "Apple Reports Record Q2 Earnings, Revenue Beats Estimates",
            "Apple Announces New AI Features at WWDC 2025",
            "Apple Stock Rallies on Strong iPhone Sales",
            "Apple Faces EU Antitrust Fine Over App Store Practices",
        ],
        "MSFT": [
            "Microsoft Azure Growth Accelerates, Cloud Revenue Surges",
            "Microsoft Acquires AI Startup for $2B",
            "Microsoft Windows Sales Decline in Q2",
        ],
        "GOOGL": [
            "Google Search Revenue Maintains Growth Trajectory",
            "Alphabet Faces DOJ Antitrust Ruling",
            "Google Cloud Achieves Profitability Milestone",
        ],
        "AMZN": [
            "Amazon AWS Revenue Growth Slows, Misses Estimates",
            "Amazon Announces Prime Day Dates for July",
            "Amazon Faces Antitrust Lawsuit in Multiple States",
            "Amazon Stock Downgraded on Valuation Concerns",
        ],
        "NVDA": [
            "Nvidia Surges on AI Chip Demand, Data Center Revenue Skyrockets",
            "Nvidia Unveils Next-Gen Blackwell GPU Architecture",
            "Nvidia Stock Soars to All-Time High",
            "Nvidia Faces Export Restrictions Impact on China Sales",
        ],
    }

    def get_headlines(self, ticker: str) -> list[str]:
        return self._headlines.get(ticker.upper(), ["No recent news for this ticker"])