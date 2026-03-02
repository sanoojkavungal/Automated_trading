from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from bot.core.state import Candle
from bot.core.utils import floor_timeframe
from bot.data.binance_stream import AggTrade


@dataclass
class CandleCloseEvent:
    timeframe: str
    candle: Candle


class TradeCandleBuilder:
    def __init__(self) -> None:
        self._current_5m: Optional[Candle] = None
        self._current_15m: Optional[Candle] = None

    def update(self, trade: AggTrade) -> list[CandleCloseEvent]:
        events: list[CandleCloseEvent] = []
        events.extend(self._update_timeframe(trade, 5, "5m"))
        events.extend(self._update_timeframe(trade, 15, "15m"))
        return events

    def _update_timeframe(self, trade: AggTrade, minutes: int, name: str) -> list[CandleCloseEvent]:
        start = floor_timeframe(trade.event_time, minutes)
        close_time = start + timedelta(minutes=minutes)
        target = self._current_5m if minutes == 5 else self._current_15m
        events: list[CandleCloseEvent] = []

        if target is None or target.open_time != start:
            if target is not None:
                events.append(CandleCloseEvent(timeframe=name, candle=target))
            target = Candle(
                timeframe=name,
                open_time=start,
                close_time=close_time,
                open=trade.price,
                high=trade.price,
                low=trade.price,
                close=trade.price,
            )

        target.high = max(target.high, trade.price)
        target.low = min(target.low, trade.price)
        target.close = trade.price
        target.volume += trade.quantity
        if trade.buyer_is_maker:
            target.sell_volume += trade.quantity
        else:
            target.buy_volume += trade.quantity
        target.delta = target.buy_volume - target.sell_volume

        if minutes == 5:
            self._current_5m = target
        else:
            self._current_15m = target
        return events
