import json, urllib.parse, urllib.request
from datetime import datetime, timezone
from .provider import MarketDataProvider
from .candles import Candle
class TwelveDataProvider(MarketDataProvider):
 def __init__(self,key,timeout=12): self.key,self.timeout=key,timeout
 def candles(self,symbol,interval,outputsize=200):
  if not self.key: raise RuntimeError("TWELVEDATA_API_KEY missing")
  q=urllib.parse.urlencode({"symbol":symbol,"interval":interval,"outputsize":outputsize,"apikey":self.key,"format":"JSON"})
  with urllib.request.urlopen("https://api.twelvedata.com/time_series?"+q,timeout=self.timeout) as r: data=json.load(r)
  if data.get("status")=="error": raise RuntimeError(data.get("message","provider error"))
  out=[]
  for v in reversed(data.get("values",[])):
   dt=datetime.fromisoformat(v["datetime"]).replace(tzinfo=timezone.utc)
   out.append(Candle(dt,float(v["open"]),float(v["high"]),float(v["low"]),float(v["close"]),float(v.get("volume") or 0)))
  return out
