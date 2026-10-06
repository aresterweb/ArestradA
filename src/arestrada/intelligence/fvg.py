def detect(candles):
 out=[]
 for i in range(2,len(candles)):
  a,c=candles[i-2],candles[i]
  if c.low>a.high: out.append({"direction":"BULLISH","low":a.high,"high":c.low,"index":i})
  elif c.high<a.low: out.append({"direction":"BEARISH","low":c.high,"high":a.low,"index":i})
 return out[-10:]
