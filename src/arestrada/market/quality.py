from dataclasses import dataclass
from datetime import datetime,timedelta
from statistics import median
from arestrada.core.enums import DataQuality
from .candles import Candle
@dataclass(frozen=True,slots=True)
class QualityReport: state:DataQuality; reason:str; details:tuple=()
def assess(candles:list[Candle],now:datetime,max_age:timedelta)->QualityReport:
 if not candles:return QualityReport(DataQuality.INVALID,"NO_CANDLES")
 if now-candles[-1].ts>max_age:return QualityReport(DataQuality.STALE,"LATEST_CANDLE_STALE")
 if len(candles)<20:return QualityReport(DataQuality.INVALID,"INSUFFICIENT_CANDLES",(len(candles),))
 if any(candles[i].ts>=candles[i+1].ts for i in range(len(candles)-1)):return QualityReport(DataQuality.INVALID,"NON_MONOTONIC_OR_DUPLICATE")
 ranges=[c.high-c.low for c in candles[-50:] if c.high>c.low]
 if not ranges:return QualityReport(DataQuality.INVALID,"ZERO_RANGES")
 med=median(ranges)
 if med and (candles[-1].high-candles[-1].low)>med*12:return QualityReport(DataQuality.DEGRADED,"ABNORMAL_LAST_RANGE")
 return QualityReport(DataQuality.VALID,"OK")
