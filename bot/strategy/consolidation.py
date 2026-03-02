from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from bot.core.state import Candle, ConsolidationBox
from bot.core.utils import utc_now
from bot.strategy.indicators import atr


@dataclass
class ConsolidationResult:
    is_valid: bool
    box: ConsolidationBox | None


class ConsolidationDetector:
    def __init__(self, lookback: int = 12, atr_period: int = 14, mean_window: int = 30) -> None:
        self.lookback = lookback
        self.atr_period = atr_period
        self.mean_window = mean_window

    def detect(self, candles_15m: Sequence[Candle]) -> ConsolidationResult:
        required = max(self.lookback, self.mean_window + self.atr_period)
        if len(candles_15m) < required:
            return ConsolidationResult(False, None)

        current_atr = atr(candles_15m, self.atr_period)
        atr_series: list[Decimal] = []
        for i in range(len(candles_15m) - self.mean_window, len(candles_15m)):
            sample = candles_15m[: i + 1]
            atr_series.append(atr(sample, self.atr_period))
        mean_atr = sum(atr_series) / Decimal(len(atr_series))

        box_slice = candles_15m[-self.lookback :]
        hh = max(c.high for c in box_slice)
        ll = min(c.low for c in box_slice)
        range_15m = hh - ll

        close_inside = all(ll <= c.close <= hh for c in box_slice)
        is_consolidating = (
            current_atr < Decimal("0.7") * mean_atr
            and range_15m < Decimal("1.5") * current_atr
            and close_inside
        )
        if not is_consolidating:
            return ConsolidationResult(False, None)

        return ConsolidationResult(
            True,
            ConsolidationBox(high=hh, low=ll, atr_15m=current_atr, created_at=utc_now()),
        )
