from arestrada.features.indicators import atr
def zones(candles):
 vals=atr([c.high for c in candles],[c.low for c in candles],[c.close for c in candles],14); a=vals[-1] if vals else 0
 if not a:return []
 out=[]
 for i in range(2,len(candles)-1):
  b=candles[i]; nxt=candles[i+1]; base=b.high-b.low
  if base<=.8*a and nxt.close-b.close>1.1*a: out.append({"type":"DEMAND","low":b.low,"high":b.high,"status":"FRESH","index":i})
  if base<=.8*a and b.close-nxt.close>1.1*a: out.append({"type":"SUPPLY","low":b.low,"high":b.high,"status":"FRESH","index":i})
 return out[-10:]
