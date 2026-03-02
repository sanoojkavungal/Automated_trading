from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Candle:
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")
    buy_volume: Decimal = Decimal("0")
    sell_volume: Decimal = Decimal("0")
    delta: Decimal = Decimal("0")


@dataclass
class ConsolidationBox:
    high: Decimal
    low: Decimal
    atr_15m: Decimal
    created_at: datetime
    trades_taken: int = 0


@dataclass
class PositionState:
    side: str
    entry_price: Decimal
    stop_price: Decimal
    take_profit_price: Decimal
    size: Decimal
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DailyPnL:
    date_key: str
    realized_pnl: Decimal = Decimal("0")


@dataclass
class EngineState:
    current_box: Optional[ConsolidationBox] = None
    open_position: Optional[PositionState] = None
    last_signal_id: Optional[str] = None
    daily_pnl: DailyPnL = field(
        default_factory=lambda: DailyPnL(date_key=datetime.now(timezone.utc).date().isoformat())
    )
