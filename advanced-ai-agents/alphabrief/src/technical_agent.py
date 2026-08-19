"""Technical Agent — calculates RSI, MACD, moving averages, flags divergences.

Module-level _client singleton pattern for injectable test mocks.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .models import TechnicalSignal, TechnicalReport

logger = logging.getLogger(__name__)

_client: Optional["FakeYFinanceish"] = None


def set_client(client) -> None:
    global _client
    _client = client


def reset_client() -> None:
    global _client
    _client = None


class TechnicalAgent:
    """Computes technical indicators and generates trading signals."""

    def __init__(self, tickers: list[str]) -> None:
        self.tickers = tickers

    @staticmethod
    def _fetch_hist(ticker: str, period: str = "6mo") -> pd.DataFrame:
        """Fetch historical OHLCV data.  Mock-aware."""
        if _client is not None:
            return _client.get_hist(ticker, period)
        import yfinance as yf
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        return df

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> float:
        if len(series) < period + 1:
            return 50.0
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rs = rs.fillna(1.0)
        return round(float(100.0 - (100.0 / (1.0 + rs)).iloc[-1]), 2)

    @staticmethod
    def _macd(series: pd.Series) -> tuple[float, float, str]:
        if len(series) < 26:
            return 0.0, 0.0, "neutral"
        ema12 = series.ewm(span=12, adjust=False).mean()
        ema26 = series.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal = macd_line.ewm(span=9, adjust=False).mean()
        macd_val = round(float(macd_line.iloc[-1]), 4)
        signal_val = round(float(signal.iloc[-1]), 4)
        hist = round(macd_val - signal_val, 4)
        direction = "bullish" if macd_val > signal_val else "bearish"
        return macd_val, signal_val, direction

    @staticmethod
    def _sma(series: pd.Series, period: int) -> float:
        if len(series) < period:
            return round(float(series.mean()), 2)
        return round(float(series.tail(period).mean()), 2)

    def _analyze_ticker(self, ticker: str) -> list[TechnicalSignal]:
        signals: list[TechnicalSignal] = []
        df = self._fetch_hist(ticker)
        if df.empty or "Close" not in df.columns:
            return signals

        close = df["Close"]

        # RSI
        rsi_val = self._rsi(close)
        if rsi_val >= 70:
            rsi_sig = "bearish"
            detail = f"Overbought (RSI={rsi_val})"
        elif rsi_val <= 30:
            rsi_sig = "bullish"
            detail = f"Oversold (RSI={rsi_val})"
        else:
            rsi_sig = "neutral"
            detail = f"Neutral (RSI={rsi_val})"
        signals.append(TechnicalSignal(ticker=ticker, indicator="RSI_14", value=rsi_val, signal=rsi_sig, detail=detail))

        # MACD
        macd_val, signal_val, macd_dir = self._macd(close)
        signals.append(TechnicalSignal(
            ticker=ticker, indicator="MACD", value=macd_val,
            signal=macd_dir,
            detail=f"MACD={macd_val}, Signal={signal_val}, Histogram={round(macd_val - signal_val, 4)}"
        ))

        # SMA 50
        sma50 = self._sma(close, 50)
        current = round(float(close.iloc[-1]), 2)
        sma50_sig = "bullish" if current > sma50 else "bearish"
        signals.append(TechnicalSignal(
            ticker=ticker, indicator="SMA_50", value=sma50,
            signal=sma50_sig,
            detail=f"Price={current} vs SMA50={sma50}"
        ))

        # SMA 200 (if enough data)
        if len(close) >= 200:
            sma200 = self._sma(close, 200)
            sma200_sig = "bullish" if current > sma200 else "bearish"
            signals.append(TechnicalSignal(
                ticker=ticker, indicator="SMA_200", value=sma200,
                signal=sma200_sig,
                detail=f"Price={current} vs SMA200={sma200}"
            ))
            # Golden/death cross check
            sma50_hist = close.rolling(50).mean()
            sma200_hist = close.rolling(200).mean()
            if len(sma50_hist) >= 2 and len(sma200_hist) >= 2:
                prev50 = sma50_hist.iloc[-2]
                prev200 = sma200_hist.iloc[-2]
                curr50 = sma50_hist.iloc[-1]
                curr200 = sma200_hist.iloc[-1]
                if prev50 <= prev200 and curr50 > curr200:
                    signals.append(TechnicalSignal(
                        ticker=ticker, indicator="GOLDEN_CROSS", value=round(float(curr50), 2),
                        signal="bullish",
                        detail="Golden cross formed: SMA50 crossed above SMA200"
                    ))
                elif prev50 >= prev200 and curr50 < curr200:
                    signals.append(TechnicalSignal(
                        ticker=ticker, indicator="DEATH_CROSS", value=round(float(curr50), 2),
                        signal="bearish",
                        detail="Death cross formed: SMA50 crossed below SMA200"
                    ))

        return signals

    def run(self) -> TechnicalReport:
        signals: list[TechnicalSignal] = []
        alerts: list[str] = []
        for t in self.tickers:
            try:
                sigs = self._analyze_ticker(t)
                signals.extend(sigs)
                for s in sigs:
                    if s.signal != "neutral":
                        alerts.append(f"[{t}] {s.indicator}: {s.signal.upper()} — {s.detail}")
            except Exception as exc:
                logger.warning("Technical analysis failed for %s: %s", t, exc)
                alerts.append(f"[{t}] Technical analysis error: {exc}")
        return TechnicalReport(signals=signals, alerts=alerts)