from __future__ import annotations

import logging
from decimal import Decimal

import httpx


logger = logging.getLogger(__name__)


class DeltaPriceFeed:
    def __init__(self, base_url: str, product_id: int, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.product_id = product_id
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def get_mark_price(self) -> Decimal:
        endpoint = f"{self.base_url}/v2/tickers/{self.product_id}"
        response = await self._client.get(endpoint)
        response.raise_for_status()
        payload = response.json()
        mark_price = payload["result"]["mark_price"]
        return Decimal(str(mark_price))

    async def aclose(self) -> None:
        await self._client.aclose()
