from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from decimal import Decimal

import httpx


@dataclass
class DeltaOrder:
    side: str
    size: Decimal
    order_type: str
    product_id: int


class DeltaClient:
    def __init__(self, base_url: str, api_key: str, api_secret: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.client = httpx.AsyncClient(timeout=timeout)

    def _signed_headers(self, method: str, path: str, body: str) -> dict[str, str]:
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        message = f"{method}{timestamp}{path}{body}".encode("utf-8")
        signature = hmac.new(self.api_secret, message, hashlib.sha256).hexdigest()
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json",
        }

    async def place_market_order(self, order: DeltaOrder) -> dict:
        path = "/v2/orders"
        payload = {
            "product_id": order.product_id,
            "size": float(order.size),
            "side": order.side,
            "order_type": order.order_type,
        }
        body = json.dumps(payload, separators=(",", ":"))
        headers = self._signed_headers("POST", path, body)
        response = await self.client.post(f"{self.base_url}{path}", headers=headers, content=body)
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        await self.client.aclose()
