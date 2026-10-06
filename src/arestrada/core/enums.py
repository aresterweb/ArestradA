from enum import StrEnum

class DataQuality(StrEnum):
    VALID="VALID"; DEGRADED="DEGRADED"; STALE="STALE"; INVALID="INVALID"
class Direction(StrEnum):
    UP="UP"; DOWN="DOWN"; NEUTRAL="NEUTRAL"; NO_PREDICTION="NO_PREDICTION"
class TradeDecision(StrEnum):
    BUY="BUY"; SELL="SELL"; WAIT="WAIT"; BLOCKED="BLOCKED"
