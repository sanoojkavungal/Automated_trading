from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from bot.core.state import Candle, ConsolidationBox
from bot.strategy.indicators import atr


@dataclass
class AbsorptionSignal:
    side: str
    trigger_high: Decimal
    trigger_low: Decimal
    stop_anchor: Decimal
    timestamp: str


class AbsorptionDetector:
    def __init__(self, atr_period: int = 14, delta_mean_window: int = 20) -> None:
        self.atr_period = atr_period
        self.delta_mean_window = delta_mean_window

    def detect(self, candles_5m: Sequence[Candle], box: ConsolidationBox) -> AbsorptionSignal | None:
        if len(candles_5m) < max(self.atr_period + 1, self.delta_mean_window + 1):
            return None

        candle = candles_5m[-1]
        range_5m = candle.high - candle.low
        atr_5m = atr(candles_5m, self.atr_period)
        deltas = [abs(c.delta) for c in candles_5m[-self.delta_mean_window :]]
        avg_delta = sum(deltas) / Decimal(len(deltas))

        bullish = (
            candle.delta < -Decimal("2") * avg_delta
            and range_5m < Decimal("0.8") * atr_5m
            and (candle.close >= box.low or (candle.low < box.low and candle.close >= box.low))
        )
        bearish = (
            candle.delta > Decimal("2") * avg_delta
            and range_5m < Decimal("0.8") * atr_5m
            and (candle.close <= box.high or (candle.high > box.high and candle.close <= box.high))
        )

        if bullish:
            return AbsorptionSignal(
                side="buy",
                trigger_high=candle.high,
                trigger_low=candle.low,
                stop_anchor=candle.low,
                timestamp=candle.close_time.isoformat(),
            )
        if bearish:
            return AbsorptionSignal(
                side="sell",
                trigger_high=candle.high,
                trigger_low=candle.low,
                stop_anchor=candle.high,
                timestamp=candle.close_time.isoformat(),
            )
        return None
