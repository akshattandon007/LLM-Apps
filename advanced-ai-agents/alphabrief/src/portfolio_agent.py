"""Portfolio Agent — fetches holdings data, prices, and calculates P&L.

Module-level _client singleton pattern for injectable test mocks.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from .models import Holding, PortfolioSummary

logger = logging.getLogger(__name__)

_client: Optional["FakeYFinanceish"] = None


def set_client(client) -> None:
    """Inject a test double.  The real module uses yfinance directly."""
    global _client
    _client = client


def reset_client() -> None:
    global _client
    _client = None


class PortfolioAgent:
    """Tracks portfolio holdings, fetches live prices, computes P&L."""

    def __init__(self, tickers: Optional[list[str]] = None, shares: Optional[list[float]] = None,
                 avg_costs: Optional[list[float]] = None) -> None:
        self.tickers: list[str] = tickers or []
        self.shares: list[float] = shares or [0.0] * len(self.tickers)
        self.avg_costs: list[float] = avg_costs or [0.0] * len(self.tickers)

    @staticmethod
    def _fetch_prices(tickers: list[str]) -> dict[str, float]:
        """Fetch current price for each ticker via yfinance or mock."""
        if _client is not None:
            return _client.get_prices(tickers)
        import yfinance as yf
        prices: dict[str, float] = {}
        for t in tickers:
            try:
                ticker = yf.Ticker(t)
                hist = ticker.history(period="2d")
                if hist.empty:
                    logger.warning("No price data for %s", t)
                    prices[t] = 0.0
                else:
                    prices[t] = round(float(hist["Close"].iloc[-1]), 2)
            except Exception as exc:
                logger.warning("Failed to fetch price for %s: %s", t, exc)
                prices[t] = 0.0
        return prices

    @staticmethod
    def _fetch_day_change(tickers: list[str]) -> dict[str, float]:
        """Fetch daily % change for each ticker."""
        if _client is not None:
            return _client.get_day_changes(tickers)
        import yfinance as yf
        changes: dict[str, float] = {}
        for t in tickers:
            try:
                ticker = yf.Ticker(t)
                hist = ticker.history(period="5d")
                if len(hist) >= 2:
                    prev_close = float(hist["Close"].iloc[-2])
                    curr_close = float(hist["Close"].iloc[-1])
                    changes[t] = round(((curr_close - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
                else:
                    changes[t] = 0.0
            except Exception as exc:
                logger.warning("Failed day change for %s: %s", t, exc)
                changes[t] = 0.0
        return changes

    def run(self) -> PortfolioSummary:
        """Fetch prices and build a full portfolio snapshot."""
        if not self.tickers:
            return PortfolioSummary()

        prices = self._fetch_prices(self.tickers)
        day_changes = self._fetch_day_change(self.tickers)
        total_value = 0.0
        total_cost = 0.0
        holdings: list[Holding] = []

        for t, shr, ac in zip(self.tickers, self.shares, self.avg_costs):
            price = prices.get(t, 0.0)
            mv = round(shr * price, 2)
            cb = round(shr * ac, 2)
            pnl = round(mv - cb, 2)
            pnl_pct = round(((pnl / cb) * 100), 2) if cb else 0.0
            total_value += mv
            total_cost += cb
            holdings.append(Holding(
                ticker=t, shares=shr, avg_cost=round(ac, 2),
                current_price=price, market_value=mv, cost_basis=cb,
                pnl=pnl, pnl_pct=pnl_pct,
                day_change_pct=day_changes.get(t, 0.0),
                weight=0.0,  # calculated below
            ))

        # calculate weights
        for h in holdings:
            h.weight = round((h.market_value / total_value) * 100, 2) if total_value else 0.0

        total_pnl_pct = round(((total_value - total_cost) / total_cost) * 100, 2) if total_cost else 0.0
        return PortfolioSummary(
            holdings=holdings,
            total_value=round(total_value, 2),
            total_cost=round(total_cost, 2),
            total_pnl=round(total_value - total_cost, 2),
            total_pnl_pct=total_pnl_pct,
        )