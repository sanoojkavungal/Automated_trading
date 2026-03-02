from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import os


@dataclass(frozen=True)
class BinanceConfig:
    symbol: str = os.getenv("BINANCE_SYMBOL", "btcusdt")
    websocket_url: str = os.getenv(
        "BINANCE_WS_URL", "wss://fstream.binance.com/ws/btcusdt@aggTrade"
    )


@dataclass(frozen=True)
class DeltaConfig:
    base_url: str = os.getenv("DELTA_BASE_URL", "https://api.delta.exchange")
    api_key: str = os.getenv("DELTA_API_KEY", "")
    api_secret: str = os.getenv("DELTA_API_SECRET", "")
    product_id: int = int(os.getenv("DELTA_PRODUCT_ID", "84"))  # BTCUSD perpetual example


@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade: Decimal = Decimal(os.getenv("RISK_PER_TRADE", "0.01"))
    daily_loss_limit: Decimal = Decimal(os.getenv("DAILY_LOSS_LIMIT", "0.03"))
    max_trades_per_box: int = int(os.getenv("MAX_TRADES_PER_BOX", "2"))


@dataclass(frozen=True)
class StrategyConfig:
    consolidation_window: int = 12
    atr_period: int = 14
    atr_mean_window: int = 30
    delta_mean_window: int = 20
    proximity_atr_multiplier: Decimal = Decimal("0.2")
    spread_threshold: Decimal = Decimal(os.getenv("SPREAD_THRESHOLD", "30"))


@dataclass(frozen=True)
class RuntimeConfig:
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    log_dir: str = os.getenv("LOG_DIR", "bot/logs")
    reconnect_backoff_seconds: float = float(os.getenv("RECONNECT_BACKOFF_SECONDS", "3"))


@dataclass(frozen=True)
class AppConfig:
    binance: BinanceConfig = BinanceConfig()
    delta: DeltaConfig = DeltaConfig()
    risk: RiskConfig = RiskConfig()
    strategy: StrategyConfig = StrategyConfig()
    runtime: RuntimeConfig = RuntimeConfig()


CONFIG = AppConfig()
