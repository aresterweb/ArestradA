def ema(values: list[float], period: int) -> list[float]:
    if period <= 0 or len(values) < period: return []
    k=2/(period+1); out=[sum(values[:period])/period]
    for v in values[period:]: out.append(v*k+out[-1]*(1-k))
    return out

def true_ranges(highs,lows,closes):
    if not closes: return []
    out=[highs[0]-lows[0]]
    for i in range(1,len(closes)):
        out.append(max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])))
    return out

def atr(highs,lows,closes,period=14):
    tr=true_ranges(highs,lows,closes)
    if len(tr)<period: return []
    a=sum(tr[:period])/period; out=[a]
    for x in tr[period:]: a=(a*(period-1)+x)/period; out.append(a)
    return out
