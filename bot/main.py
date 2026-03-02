from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from bot.config import CONFIG
from bot.core.logger import setup_logging
from bot.core.state import Candle, EngineState
from bot.core.utils import append_csv
from bot.data.binance_stream import BinanceTradeStream
from bot.data.candle_builder import TradeCandleBuilder
from bot.data.delta_price_feed import DeltaPriceFeed
from bot.execution.order_manager import OrderManager
from bot.execution.risk_manager import RiskManager
from bot.strategy.absorption import AbsorptionDetector
from bot.strategy.consolidation import ConsolidationDetector
from bot.strategy.signal_engine import SignalEngine


logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(self) -> None:
        self.state = EngineState()
        self.candles_5m: list[Candle] = []
        self.candles_15m: list[Candle] = []
        self.builder = TradeCandleBuilder()

        self.binance_stream = BinanceTradeStream(
            websocket_url=CONFIG.binance.websocket_url,
            reconnect_backoff_seconds=CONFIG.runtime.reconnect_backoff_seconds,
        )
        self.delta_price_feed = DeltaPriceFeed(
            base_url=CONFIG.delta.base_url,
            product_id=CONFIG.delta.product_id,
        )
        self.consolidation = ConsolidationDetector(
            lookback=CONFIG.strategy.consolidation_window,
            atr_period=CONFIG.strategy.atr_period,
            mean_window=CONFIG.strategy.atr_mean_window,
        )
        self.absorption = AbsorptionDetector(
            atr_period=CONFIG.strategy.atr_period,
            delta_mean_window=CONFIG.strategy.delta_mean_window,
        )
        self.signal_engine = SignalEngine()
        self.risk = RiskManager(CONFIG.risk)
        self.order_manager = OrderManager(CONFIG.delta, dry_run=CONFIG.runtime.dry_run)

    async def run(self) -> None:
        async for trade in self.binance_stream.stream():
            events = self.builder.update(trade)
            for event in events:
                if event.timeframe == "15m":
                    await self._on_15m_close(event.candle)
                elif event.timeframe == "5m":
                    await self._on_5m_close(event.candle)

    async def _on_15m_close(self, candle: Candle) -> None:
        self.candles_15m.append(candle)
        result = self.consolidation.detect(self.candles_15m)
        if result.is_valid and result.box:
            self.state.current_box = result.box
            logger.info("Consolidation box active high=%s low=%s", result.box.high, result.box.low)

    async def _on_5m_close(self, candle: Candle) -> None:
        self.candles_5m.append(candle)
        box = self.state.current_box
        if box is None:
            return

        if not self._price_near_box(candle.close, box.low, box.high, box.atr_15m):
            return

        absorption = self.absorption.detect(self.candles_5m, box)
        if absorption is not None:
            self.signal_engine.register_absorption(absorption)
            logger.info("Absorption detected side=%s time=%s", absorption.side, absorption.timestamp)
            return

        entry = self.signal_engine.consume_entry_trigger(candle, box)
        if entry is None:
            return

        if entry.signal_id == self.state.last_signal_id:
            return

        if not self.risk.can_trade(self.state.daily_pnl, box):
            logger.warning("Risk gate blocked new trade")
            return

        if not await self._spread_is_safe(binance_price=candle.close):
            logger.warning("Spread filter blocked trade")
            return

        equity = Decimal("10000")
        size = self.risk.calculate_position_size(equity, entry.entry_price, entry.stop_price)
        if size <= 0:
            logger.warning("Invalid position size; skipping")
            return

        result = await self.order_manager.execute_entry(entry, size)
        self.state.last_signal_id = entry.signal_id
        box.trades_taken += 1
        self.state.open_position = self.risk.build_position(
            side=entry.side,
            entry_price=entry.entry_price,
            stop_price=entry.stop_price,
            take_profit_price=entry.take_profit_price,
            size=size,
        )

        append_csv(
            f"{CONFIG.runtime.log_dir}/trades.csv",
            {
                "signal_id": entry.signal_id,
                "side": entry.side,
                "entry_price": entry.entry_price,
                "stop_price": entry.stop_price,
                "take_profit": entry.take_profit_price,
                "size": size,
                "result": result,
            },
        )
        logger.info("Trade executed %s", result)

    async def _spread_is_safe(self, binance_price: Decimal) -> bool:
        delta_price = await self.delta_price_feed.get_mark_price()
        spread = binance_price - delta_price
        return abs(spread) <= CONFIG.strategy.spread_threshold

    @staticmethod
    def _price_near_box(price: Decimal, low: Decimal, high: Decimal, atr_15m: Decimal) -> bool:
        threshold = CONFIG.strategy.proximity_atr_multiplier * atr_15m
        return abs(price - low) <= threshold or abs(price - high) <= threshold

    async def aclose(self) -> None:
        await asyncio.gather(
            self.delta_price_feed.aclose(),
            self.order_manager.aclose(),
            return_exceptions=True,
        )


async def _main() -> None:
    setup_logging(CONFIG.runtime.log_dir)
    engine = TradingEngine()
    try:
        await engine.run()
    finally:
        await engine.aclose()


if __name__ == "__main__":
    asyncio.run(_main())
