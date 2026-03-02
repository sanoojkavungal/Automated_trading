from __future__ import annotations

import logging
from decimal import Decimal

from bot.config import DeltaConfig
from bot.execution.delta_client import DeltaClient, DeltaOrder
from bot.strategy.signal_engine import EntrySignal


logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, delta_config: DeltaConfig, dry_run: bool) -> None:
        self.delta_config = delta_config
        self.dry_run = dry_run
        self.delta_client = DeltaClient(
            base_url=delta_config.base_url,
            api_key=delta_config.api_key,
            api_secret=delta_config.api_secret,
        )

    async def execute_entry(self, signal: EntrySignal, size: Decimal) -> dict:
        if self.dry_run:
            logger.info("DRY RUN order: side=%s size=%s entry=%s", signal.side, size, signal.entry_price)
            return {"dry_run": True, "side": signal.side, "size": str(size)}

        order = DeltaOrder(
            side="buy" if signal.side == "buy" else "sell",
            size=size,
            order_type="market_order",
            product_id=self.delta_config.product_id,
        )
        return await self.delta_client.place_market_order(order)

    async def aclose(self) -> None:
        await self.delta_client.aclose()
