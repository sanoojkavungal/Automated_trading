from __future__ import annotations

from decimal import Decimal

from bot.config import RiskConfig
from bot.core.state import ConsolidationBox, DailyPnL, PositionState


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def can_trade(self, daily_pnl: DailyPnL, box: ConsolidationBox) -> bool:
        if box.trades_taken >= self.config.max_trades_per_box:
            return False
        return daily_pnl.realized_pnl > -self.config.daily_loss_limit

    def calculate_position_size(
        self,
        equity: Decimal,
        entry_price: Decimal,
        stop_price: Decimal,
    ) -> Decimal:
        risk_budget = equity * self.config.risk_per_trade
        stop_distance = abs(entry_price - stop_price)
        if stop_distance <= 0:
            return Decimal("0")
        return risk_budget / stop_distance

    def update_daily_pnl(self, daily_pnl: DailyPnL, realized_pnl: Decimal) -> DailyPnL:
        daily_pnl.realized_pnl += realized_pnl
        return daily_pnl

    def build_position(
        self,
        side: str,
        entry_price: Decimal,
        stop_price: Decimal,
        take_profit_price: Decimal,
        size: Decimal,
    ) -> PositionState:
        return PositionState(
            side=side,
            entry_price=entry_price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            size=size,
        )
