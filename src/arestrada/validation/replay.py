def replay(candles,warmup,callback):
 # Sequential slices guarantee callback cannot see future candles.
 return [callback(candles[:i]) for i in range(warmup,len(candles)+1)]
