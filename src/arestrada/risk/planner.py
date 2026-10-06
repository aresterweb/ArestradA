def plan(decision,price,atr,protected=None):
 if decision not in ("BUY","SELL") or not atr:return None
 if decision=="BUY":
  sl=min(price-1.2*atr,protected-.15*atr) if protected else price-1.2*atr; risk=price-sl
  return {"entry":price,"sl":sl,"tp1":price+1.5*risk,"tp2":price+2*risk,"rr1":1.5,"rr2":2.0}
 sl=max(price+1.2*atr,protected+.15*atr) if protected else price+1.2*atr; risk=sl-price
 return {"entry":price,"sl":sl,"tp1":price-1.5*risk,"tp2":price-2*risk,"rr1":1.5,"rr2":2.0}
