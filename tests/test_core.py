from datetime import datetime, timezone, timedelta
import pytest
from arestrada.market.candles import Candle
from arestrada.market.quality import assess
from arestrada.core.enums import DataQuality, Direction
from arestrada.market.snapshots import MarketSnapshot
from arestrada.decision.next_candle import predict

def c(minute,o=100,h=102,l=99,cl=101): return Candle(datetime(2026,1,1,0,minute,tzinfo=timezone.utc),o,h,l,cl)

def test_malformed_ohlc_rejected():
    with pytest.raises(ValueError): c(0,100,99,98,101)

def test_stale_data():
    q=assess([c(0)],datetime(2026,1,1,1,0,tzinfo=timezone.utc),timedelta(minutes=20))
    assert q.state==DataQuality.STALE

def test_stale_never_predicts():
    s=MarketSnapshot("s","XAU/USD",datetime.now(timezone.utc),"test",DataQuality.STALE,{"M15":(c(0),c(15),c(30))})
    assert predict(s).direction==Direction.NO_PREDICTION
