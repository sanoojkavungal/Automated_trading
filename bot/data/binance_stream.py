from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncIterator

import websockets


logger = logging.getLogger(__name__)


@dataclass
class AggTrade:
    event_time: datetime
    price: Decimal
    quantity: Decimal
    buyer_is_maker: bool


class BinanceTradeStream:
    def __init__(self, websocket_url: str, reconnect_backoff_seconds: float = 3.0) -> None:
        self.websocket_url = websocket_url
        self.reconnect_backoff_seconds = reconnect_backoff_seconds

    async def stream(self) -> AsyncIterator[AggTrade]:
        while True:
            try:
                logger.info("Connecting to Binance stream: %s", self.websocket_url)
                async with websockets.connect(self.websocket_url, ping_interval=20, ping_timeout=20) as ws:
                    async for message in ws:
                        payload = json.loads(message)
                        yield AggTrade(
                            event_time=datetime.fromtimestamp(payload["T"] / 1000, tz=timezone.utc),
                            price=Decimal(payload["p"]),
                            quantity=Decimal(payload["q"]),
                            buyer_is_maker=bool(payload["m"]),
                        )
            except (websockets.WebSocketException, OSError, KeyError, ValueError) as exc:
                logger.exception("Binance stream failed, reconnecting: %s", exc)
                await asyncio.sleep(self.reconnect_backoff_seconds)
