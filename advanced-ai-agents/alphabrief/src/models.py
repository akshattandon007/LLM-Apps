"""Pydantic models for AlphaBrief agent data."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Holding(BaseModel):
    """A single portfolio holding."""

    ticker: str = Field(description="Stock ticker symbol")
    shares: float = Field(ge=0, description="Number of shares held")
    avg_cost: float = Field(default=0.0, ge=0, description="Average cost per share")
    current_price: float = Field(default=0.0, ge=0, description="Current market price")
    market_value: float = Field(default=0.0, description="Current market value (shares * price)")
    cost_basis: float = Field(default=0.0, description="Total cost basis (shares * avg_cost)")
    pnl: float = Field(default=0.0, description="Unrealised P&L in dollars")
    pnl_pct: float = Field(default=0.0, description="Unrealised P&L as percentage")
    day_change_pct: float = Field(default=0.0, description="Daily price change percentage")
    weight: float = Field(default=0.0, ge=0, le=100, description="Portfolio weight percentage")


class PortfolioSummary(BaseModel):
    """Aggregated portfolio snapshot."""

    report_date: date = Field(default_factory=date.today, alias="date")
    holdings: list[Holding] = Field(default_factory=list)
    total_value: float = Field(default=0.0)
    total_cost: float = Field(default=0.0)
    total_pnl: float = Field(default=0.0)
    total_pnl_pct: float = Field(default=0.0)
    cash: float = Field(default=0.0)


class TechnicalSignal(BaseModel):
    """A single technical indicator signal."""

    ticker: str
    indicator: str  # e.g. RSI, MACD, SMA_50, SMA_200
    value: float
    signal: str = Field(default="neutral", pattern="^(bullish|bearish|neutral)$")
    detail: str = Field(default="")


class TechnicalReport(BaseModel):
    """Technical analysis results for the portfolio."""

    signals: list[TechnicalSignal] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)


class FundamentalChange(BaseModel):
    """A notable change extracted from an SEC filing."""

    ticker: str
    filing_type: str  # 10-K, 10-Q, 8-K
    filing_date: date
    summary: str = Field(default="")
    key_changes: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)


class FundamentalReport(BaseModel):
    """Fundamental analysis results."""

    filings: list[FundamentalChange] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)


class SentimentScore(BaseModel):
    """Aggregated news sentiment for a ticker."""

    ticker: str
    score: float = Field(default=0.0, ge=-1.0, le=1.0, description="-1 (very negative) to +1 (very positive)")
    source_count: int = Field(default=0)
    top_headlines: list[str] = Field(default_factory=list)
    direction: str = Field(default="neutral", pattern="^(bullish|bearish|neutral)$")


class SentimentReport(BaseModel):
    """Sentiment analysis results."""

    scores: list[SentimentScore] = Field(default_factory=list)
    overall_mood: str = Field(default="neutral")
    alerts: list[str] = Field(default_factory=list)


class RiskMetrics(BaseModel):
    """Portfolio-level risk metrics."""

    portfolio_beta: float = Field(default=0.0)
    weighted_volatility: float = Field(default=0.0, description="Weighted avg daily volatility")
    concentration_top3_pct: float = Field(default=0.0, description="% of portfolio in top 3 holdings")
    max_single_weight: float = Field(default=0.0, description="Largest single holding weight %")
    correlation_alert: bool = Field(default=False, description="High correlation among holdings")
    sharpe_ratio_est: float = Field(default=0.0, description="Estimated Sharpe ratio (annualised)")
    alerts: list[str] = Field(default_factory=list)


class DailyBriefing(BaseModel):
    """The complete daily briefing synthesised by the coordinator."""

    briefing_date: date = Field(default_factory=date.today, alias="date")
    generated_at: datetime = Field(default_factory=datetime.now)
    portfolio: PortfolioSummary = Field(default_factory=PortfolioSummary)
    technical: TechnicalReport = Field(default_factory=TechnicalReport)
    fundamental: FundamentalReport = Field(default_factory=FundamentalReport)
    sentiment: SentimentReport = Field(default_factory=SentimentReport)
    risk: RiskMetrics = Field(default_factory=RiskMetrics)
    all_alerts: list[str] = Field(default_factory=list)
    summary: str = Field(default="No briefing generated.")
    sections: dict[str, str] = Field(default_factory=dict)