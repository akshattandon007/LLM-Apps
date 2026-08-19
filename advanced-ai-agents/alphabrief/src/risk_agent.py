"""Risk Agent — computes portfolio beta, concentration, correlation, and volatility.

Module-level _client singleton pattern for injectable test mocks.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np
import pandas as pd

from .models import PortfolioSummary, RiskMetrics

logger = logging.getLogger(__name__)

_client: Optional["FakeYFinanceish"] = None


def set_client(client) -> None:
    global _client
    _client = client


def reset_client() -> None:
    global _client
    _client = None


class RiskAgent:
    """Calculates portfolio-level risk metrics."""

    def __init__(self, portfolio: PortfolioSummary) -> None:
        self.portfolio = portfolio
        self.tickers = [h.ticker for h in portfolio.holdings]

    @staticmethod
    def _fetch_hist(ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical data.  Mock-aware."""
        if _client is not None:
            return _client.get_hist(ticker, period)
        import yfinance as yf
        t = yf.Ticker(ticker)
        return t.history(period=period)

    def run(self) -> RiskMetrics:
        holdings = self.portfolio.holdings
        if not holdings:
            return RiskMetrics(alerts=["Portfolio is empty — no risk metrics available"])

        alerts: list[str] = []

        # Concentration risk
        sorted_by_weight = sorted(holdings, key=lambda h: h.weight, reverse=True)
        top3_weight = sum(h.weight for h in sorted_by_weight[:3])
        max_weight = sorted_by_weight[0].weight if sorted_by_weight else 0.0

        concentration_msg = f"Top 3 holdings: {top3_weight:.1f}%, max single: {max_weight:.1f}%"
        if top3_weight > 70:
            alerts.append(f"[CONCENTRATION] {concentration_msg} — high concentration risk")
        elif top3_weight > 50:
            alerts.append(f"[CONCENTRATION] {concentration_msg} — moderate concentration risk")

        # Beta and volatility computation
        betas: list[float] = []
        volatilities: list[float] = []
        returns_data: dict[str, pd.Series] = {}

        for h in holdings:
            df = self._fetch_hist(h.ticker)
            if df.empty or "Close" not in df.columns:
                continue
            close = df["Close"]
            if len(close) < 20:
                continue

            # Volatility (daily % change std)
            daily_ret = close.pct_change().dropna()
            vol = float(daily_ret.std()) * 100.0  # as percentage
            volatilities.append(vol)
            returns_data[h.ticker] = daily_ret

            # Beta vs SPY (proxy for market)
            spy_df = self._fetch_hist("SPY", "1y")
            if not spy_df.empty and "Close" in spy_df.columns:
                spy_ret = spy_df["Close"].pct_change().dropna()
                # align lengths
                min_len = min(len(daily_ret), len(spy_ret))
                if min_len > 20:
                    asset_r = daily_ret.tail(min_len).values
                    market_r = spy_ret.tail(min_len).values
                    cov = np.cov(asset_r, market_r)[0, 1]
                    var_m = np.var(market_r)
                    beta = round(float(cov / var_m), 4) if var_m > 0 else 1.0
                    betas.append(beta)

        # Weighted volatility
        total_weight = sum(h.weight for h in holdings)
        weighted_vol = 0.0
        if total_weight > 0 and len(volatilities) == len(holdings):
            for h, vol in zip(holdings, volatilities):
                weighted_vol += (h.weight / total_weight) * vol

        # Portfolio beta (weighted average)
        portfolio_beta = 0.0
        if betas and total_weight > 0:
            for h, beta in zip(holdings, betas):
                portfolio_beta += (h.weight / total_weight) * beta
            portfolio_beta = round(portfolio_beta, 4)

        # Correlation check
        correlation_alert = False
        if len(returns_data) >= 2:
            try:
                combined = pd.DataFrame(returns_data)
                corr_matrix = combined.corr()
                # flag if any pair has avg correlation > 0.85
                upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                high_corr_pairs = []
                for col in upper.columns:
                    for idx in upper.index:
                        val = upper.loc[idx, col]
                        if not np.isnan(val) and abs(val) > 0.85:
                            high_corr_pairs.append(f"{idx}-{col}: {val:.2f}")
                if high_corr_pairs:
                    correlation_alert = True
                    alerts.append(f"[CORRELATION] High correlation detected: {'; '.join(high_corr_pairs[:3])}")
            except Exception:
                pass

        # Sharpe ratio estimate (using 5% risk-free, avg daily return)
        sharpe = 0.0
        if volatilities and weighted_vol > 0:
            # Average daily return across holdings weighted
            avg_daily_return = 0.0
            for h, df_ticker in zip(holdings, [self._fetch_hist(h.ticker) for h in holdings]):
                if not df_ticker.empty and "Close" in df_ticker.columns:
                    daily_ret = df_ticker["Close"].pct_change().dropna()
                    avg_daily_return += (h.weight / total_weight) * float(daily_ret.mean())
            # Annualise: 252 trading days
            annual_return = avg_daily_return * 252
            annual_vol = weighted_vol * math.sqrt(252) / 100.0  # convert back to decimal
            risk_free = 0.05
            if annual_vol > 0:
                sharpe = round((annual_return - risk_free) / annual_vol, 2)

        return RiskMetrics(
            portfolio_beta=portfolio_beta,
            weighted_volatility=round(weighted_vol, 4),
            concentration_top3_pct=round(top3_weight, 1),
            max_single_weight=round(max_weight, 1),
            correlation_alert=correlation_alert,
            sharpe_ratio_est=sharpe,
            alerts=alerts,
        )