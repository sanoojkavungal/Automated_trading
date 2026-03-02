from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from bot.core.state import Candle, ConsolidationBox
from bot.strategy.absorption import AbsorptionSignal


@dataclass
class EntrySignal:
    signal_id: str
    side: str
    entry_price: Decimal
    stop_price: Decimal
    take_profit_price: Decimal


class SignalEngine:
    def __init__(self) -> None:
        self._pending_absorption: Optional[AbsorptionSignal] = None

    def register_absorption(self, signal: AbsorptionSignal) -> None:
        self._pending_absorption = signal

    def consume_entry_trigger(self, latest_5m: Candle, box: ConsolidationBox) -> EntrySignal | None:
        if self._pending_absorption is None:
            return None

        pending = self._pending_absorption
        if pending.side == "buy" and latest_5m.close > pending.trigger_high:
            self._pending_absorption = None
            return EntrySignal(
                signal_id=f"buy-{pending.timestamp}",
                side="buy",
                entry_price=latest_5m.close,
                stop_price=pending.stop_anchor,
                take_profit_price=box.high,
            )
        if pending.side == "sell" and latest_5m.close < pending.trigger_low:
            self._pending_absorption = None
            return EntrySignal(
                signal_id=f"sell-{pending.timestamp}",
                side="sell",
                entry_price=latest_5m.close,
                stop_price=pending.stop_anchor,
                take_profit_price=box.low,
            )
        return None
