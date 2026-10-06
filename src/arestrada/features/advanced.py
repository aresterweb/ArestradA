from .indicators import ema, atr
def rsi(closes,n=14):
 if len(closes)<n+1:return None
 ds=[b-a for a,b in zip(closes[-n-1:-1],closes[-n:])]
 g=sum(max(x,0) for x in ds)/n;l=sum(max(-x,0) for x in ds)/n
 return 100.0 if l==0 else 100-(100/(1+g/l))
def candle_metrics(c):
 rng=max(c.high-c.low,1e-12); body=abs(c.close-c.open)
 return {"body_ratio":body/rng,"upper_wick":c.high-max(c.open,c.close),"lower_wick":min(c.open,c.close)-c.low,"bull":c.close>c.open}
def feature_set(cs):
 closes=[c.close for c in cs]; return {"ema20":(ema(closes,20)[-1] if ema(closes,20) else None),"ema50":(ema(closes,50)[-1] if ema(closes,50) else None),"rsi14":rsi(closes,14),"atr14":(atr([c.high for c in cs],[c.low for c in cs],closes,14)[-1] if atr([c.high for c in cs],[c.low for c in cs],closes,14) else None),"candle":candle_metrics(cs[-1]) if cs else {},"price":closes[-1] if closes else None}
