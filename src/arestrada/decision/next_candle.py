from dataclasses import dataclass
from arestrada.core.enums import Direction, DataQuality
from arestrada.market.snapshots import MarketSnapshot

@dataclass(frozen=True, slots=True)
class Prediction:
    direction: Direction
    confluence: int
    reason: str

def predict(snapshot:MarketSnapshot)->Prediction:
    if snapshot.quality in (DataQuality.STALE,DataQuality.INVALID):
        return Prediction(Direction.NO_PREDICTION,0,"DATA_GUARD")
    m15=snapshot.frames.get("M15",())
    if len(m15)<3: return Prediction(Direction.NO_PREDICTION,0,"INSUFFICIENT_M15")
    bodies=[c.close-c.open for c in m15[-3:]]
    score=sum(1 if x>0 else -1 if x<0 else 0 for x in bodies)
    if abs(score)<2: return Prediction(Direction.NEUTRAL,50,"MIXED_RECENT_PRESSURE")
    return Prediction(Direction.UP if score>0 else Direction.DOWN,60,"BASELINE_PRESSURE_ONLY")
