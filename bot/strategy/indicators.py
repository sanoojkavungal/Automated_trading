from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from bot.core.state import Candle


def true_range(current: Candle, prev_close: Decimal | None) -> Decimal:
    if prev_close is None:
        return current.high - current.low
    return max(
        current.high - current.low,
        abs(current.high - prev_close),
        abs(current.low - prev_close),
    )


def atr(candles: Sequence[Candle], period: int) -> Decimal:
    if len(candles) < period + 1:
        return Decimal("0")
    trs: list[Decimal] = []
    for idx in range(-period, 0):
        curr = candles[idx]
        prev = candles[idx - 1].close
        trs.append(true_range(curr, prev))
    return sum(trs) / Decimal(period)


def rolling_mean(values: Sequence[Decimal], window: int) -> Decimal:
    if len(values) < window:
        return Decimal("0")
    subset = values[-window:]
    return sum(subset) / Decimal(window)
