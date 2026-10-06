from arestrada.features.advanced import feature_set
def context(candles):
 f=feature_set(candles); a=f["atr14"]
 if not a or len(candles)<30:return "UNDEFINED"
 recent=max(x.high for x in candles[-20:])-min(x.low for x in candles[-20:])
 if recent/a<4:return "CHOPPY"
 e20,e50=f["ema20"],f["ema50"]
 if e20 and e50 and abs(e20-e50)>a*.5:return "TRENDING"
 return "RANGING"
