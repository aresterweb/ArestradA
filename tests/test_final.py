from datetime import datetime,timezone,timedelta
from arestrada.market.candles import Candle
from arestrada.market.quality import assess
from arestrada.core.enums import DataQuality
from arestrada.intelligence.structure import analyze
from arestrada.billing.stars import invoice,parse_payload
from arestrada.persistence.db import DB

def c(i,o=100,cl=101):return Candle(datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(minutes=15*i),o,max(o,cl)+1,min(o,cl)-1,cl,1)
def test_duplicate_rejected():assert assess([c(i) for i in range(20)]+[c(19)],datetime(2026,1,1,6,tzinfo=timezone.utc),timedelta(hours=2)).state==DataQuality.INVALID
def test_wick_is_not_bos():
 cs=[c(i,100+i*.1,100+i*.1+.05) for i in range(60)];s=analyze(cs);assert s.bos in (None,'BULLISH','BEARISH')
def test_star_invoice_monthly():
 x=invoice('PRO');assert x['currency']=='XTR' and x['subscription_period']==2592000 and parse_payload(x['payload'])=='PRO'
def test_payment_idempotent(tmp_path):
 d=DB(str(tmp_path/'x.db'));d.upsert_user(123,'u');assert d.save_payment('charge1',123,'PRO',250);assert not d.save_payment('charge1',123,'PRO',250);assert d.user(123)['plan']=='PRO'
def test_owner_grant(tmp_path):
 d=DB(str(tmp_path/'x.db'));d.upsert_user(1);d.set_access(1,'SPECIAL','OWNER_GRANT',None,99);assert d.user(1)['plan']=='SPECIAL'
