from dataclasses import dataclass
from datetime import datetime
from arestrada.core.enums import DataQuality
from .candles import Candle

@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    snapshot_id: str
    symbol: str
    generated_at: datetime
    provider: str
    quality: DataQuality
    frames: dict[str, tuple[Candle, ...]]
