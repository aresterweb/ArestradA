from datetime import datetime,timezone,timedelta
from arestrada.market.candles import Candle
from arestrada.application import Analyzer
from arestrada.users.entitlements import allowed

def candles(n=80,age_min=15):
 now=datetime.now(timezone.utc)-timedelta(minutes=age_min*n)
 out=[]
 for i in range(n):
  p=2000+i*.2; out.append(Candle(now+timedelta(minutes=age_min*i),p,p+1,p-1,p+.3,1))
 return out

def test_entitlements():
 assert allowed('ELITE','AUTO_ALERT') and not allowed('FREE','AUTO_ALERT')

def test_analyzer_fail_closed_stale():
 cs=candles(); old=[Candle(c.ts-timedelta(days=2),c.open,c.high,c.low,c.close,c.volume) for c in cs]
 a=Analyzer('CLEAR').analyze({'15min':old})
 assert a['quality']=='STALE' and a['setup'].decision=='BLOCKED'
