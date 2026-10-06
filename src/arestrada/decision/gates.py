from dataclasses import dataclass
from arestrada.core.enums import DataQuality, TradeDecision

@dataclass(frozen=True, slots=True)
class GateResult:
    passed: bool
    decision: TradeDecision
    reason: str

def data_gate(q:DataQuality)->GateResult:
    if q in (DataQuality.STALE,DataQuality.INVALID):
        return GateResult(False,TradeDecision.BLOCKED,f"DATA_{q}")
    return GateResult(True,TradeDecision.WAIT,"PASS")
