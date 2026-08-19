"""Sentiment Agent — fetches news headlines and computes directional sentiment.

Module-level _client singleton pattern for injectable test mocks.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import date
from typing import Optional

import httpx

from .models import SentimentScore, SentimentReport

logger = logging.getLogger(__name__)

_client: Optional["FakeNewsish"] = None
_httpx_client: Optional[httpx.Client] = None


def set_client(client) -> None:
    global _client
    _client = client


def reset_client() -> None:
    global _client
    _client = None


# Simple keyword-based sentiment lexicon
_BULLISH_WORDS = {
    "upgrade", "upgraded", "outperform", "beat", "beats", "surge", "surges",
    "surged", "rally", "rallies", "bullish", "positive", "growth", "grow",
    "profit", "profitable", "innovation", "breakthrough", "soar", "soars",
    "momentum", "strong", "strength", "record", "expansion", "expand",
    "dividend", "buyback", "launch", "partnership", "synergy",
}
_BEARISH_WORDS = {
    "downgrade", "downgraded", "underperform", "miss", "misses", "plunge",
    "plunges", "plunged", "crash", "crashes", "bearish", "negative",
    "decline", "declines", "loss", "losses", "lawsuit", "investigation",
    "fine", "penalty", "probe", "probed", "volatile", "uncertainty",
    "weak", "weakness", "deteriorate", "downturn", "selloff", "sell-off",
    "cut", "cuts", "layoff", "layoffs", "restructuring",
}
_NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "doesn't", "don't", "didn't", "won't", "wouldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't", "doesnt", "dont", "didnt", "wont", "wouldnt", "shouldnt"}


def _get_http() -> httpx.Client:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.Client(timeout=30.0)
    return _httpx_client


def _score_headline(headline: str) -> float:
    """Score a headline from -1 to +1 using keyword matching with simple negation handling."""
    words = re.findall(r"[a-zA-Z]+", headline.lower())
    score = 0.0
    count = 0
    negate = False
    for w in words:
        if w in _NEGATION_WORDS:
            negate = True
            continue
        if w in _BULLISH_WORDS:
            score += -1.0 if negate else 1.0
            count += 1
        elif w in _BEARISH_WORDS:
            score += 1.0 if negate else -1.0
            count += 1
        negate = False
    if count == 0:
        return 0.0
    return round(max(-1.0, min(1.0, score / count)), 4)


class SentimentAgent:
    """Aggregates news sentiment for each portfolio ticker."""

    def __init__(self, tickers: list[str]) -> None:
        self.tickers = tickers
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")

    def _fetch_headlines(self, ticker: str) -> list[str]:
        """Fetch recent news headlines for a ticker."""
        if _client is not None:
            return _client.get_headlines(ticker)

        headlines: list[str] = []

        # Try NewsAPI first
        if self.newsapi_key:
            try:
                http = _get_http()
                resp = http.get(
                    "https://newsapi.org/v2/everything",
                    params={"q": ticker, "pageSize": 10, "sortBy": "publishedAt", "language": "en"},
                    headers={"X-Api-Key": self.newsapi_key},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for article in data.get("articles", []):
                        title = article.get("title", "")
                        if title:
                            headlines.append(title)
                    if headlines:
                        return headlines
            except Exception as exc:
                logger.warning("NewsAPI failed for %s: %s", ticker, exc)

        # Fallback: finnhub
        finnhub_key = os.getenv("FINNHUB_KEY", "")
        if finnhub_key:
            try:
                http = _get_http()
                resp = http.get(
                    f"https://finnhub.io/api/v1/company-news",
                    params={"symbol": ticker, "from": "2025-01-01", "to": date.today().isoformat()},
                    headers={"X-Finnhub-Token": finnhub_key},
                )
                if resp.status_code == 200:
                    articles = resp.json()
                    for article in articles[:10]:
                        headline = article.get("headline", "")
                        if headline:
                            headlines.append(headline)
            except Exception as exc:
                logger.warning("Finnhub failed for %s: %s", ticker, exc)
        return headlines

    def run(self) -> SentimentReport:
        scores: list[SentimentScore] = []
        alerts: list[str] = []
        total_score = 0.0
        for ticker in self.tickers:
            try:
                headlines = self._fetch_headlines(ticker)
                if not headlines:
                    logger.info("No headlines found for %s — neutral", ticker)
                    scores.append(SentimentScore(ticker=ticker, score=0.0, source_count=0, direction="neutral"))
                    alerts.append(f"[{ticker}] No news data — sentiment set to neutral")
                    continue
                total = 0.0
                for h in headlines:
                    total += _score_headline(h)
                avg_score = round(total / len(headlines), 4)
                direction = "bullish" if avg_score > 0.15 else ("bearish" if avg_score < -0.15 else "neutral")
                top = headlines[:5]
                scores.append(SentimentScore(
                    ticker=ticker, score=avg_score, source_count=len(headlines),
                    top_headlines=top, direction=direction,
                ))
                total_score += avg_score
                if direction != "neutral":
                    alerts.append(f"[{ticker}] Sentiment {direction.upper()} (score={avg_score}, {len(headlines)} sources)")
            except Exception as exc:
                logger.warning("Sentiment analysis failed for %s: %s", ticker, exc)
                alerts.append(f"[{ticker}] Sentiment error: {exc}")
                scores.append(SentimentScore(ticker=ticker, score=0.0, source_count=0, direction="neutral"))

        overall = "neutral"
        if scores:
            avg_overall = total_score / len(scores)
            overall = "bullish" if avg_overall > 0.1 else ("bearish" if avg_overall < -0.1 else "neutral")
        return SentimentReport(scores=scores, overall_mood=overall, alerts=alerts)