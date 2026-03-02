from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import csv
from pathlib import Path
from typing import Mapping, Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def floor_timeframe(ts: datetime, minutes: int) -> datetime:
    minute = (ts.minute // minutes) * minutes
    return ts.replace(minute=minute, second=0, microsecond=0)


def append_csv(path: str, row: Mapping[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    exists = p.exists()
    with p.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow({k: str(v) if isinstance(v, Decimal) else v for k, v in row.items()})
