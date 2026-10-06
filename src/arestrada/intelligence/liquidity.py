def analyze(candles,lookback=20):
 if len(candles)<lookback+1:return {"event":None}
 prev=candles[-lookback-1:-1]; c=candles[-1]; hi=max(x.high for x in prev); lo=min(x.low for x in prev)
 if c.low<lo and c.close>lo:return {"event":"SSL_SWEEP","level":lo}
 if c.high>hi and c.close<hi:return {"event":"BSL_SWEEP","level":hi}
 if c.close>hi:return {"event":"BSL_BREAK","level":hi}
 if c.close<lo:return {"event":"SSL_BREAK","level":lo}
 return {"event":None,"bsl":hi,"ssl":lo}
