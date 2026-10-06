from dataclasses import dataclass
@dataclass(frozen=True)
class SetupDecision: decision:str; score:int; grade:str; reasons:tuple; counter:tuple; margin:int=0; gate:str="PASS"
def grade(s):return "A+" if s>=90 else "A" if s>=80 else "B+" if s>=72 else "B" if s>=65 else "C"
def evaluate(quality,structure,liquidity,context,features,news="UNKNOWN",zones=(),fvgs=(),min_score=72):
 if quality in ("STALE","INVALID"):return SetupDecision("BLOCKED",0,"C",("Data Guard",),(),0,"DATA")
 if news in ("BLOCKED","UNKNOWN"):return SetupDecision("BLOCKED",0,"C",("News Guard",),(),0,"NEWS")
 if context=="CHOPPY":return SetupDecision("WAIT",40,"C",("Choppy market",),(),0,"CONTEXT")
 bull=bear=0;br=[];sr=[]
 def add(d,w,r):
  nonlocal bull,bear
  if d=="B":bull+=w;br.append(r)
  else:bear+=w;sr.append(r)
 if structure.state=="BULLISH":add("B",20,"Bullish market structure")
 elif structure.state=="BEARISH":add("S",20,"Bearish market structure")
 ev=liquidity.get("event")
 if ev=="SSL_SWEEP":add("B",15,"Sell-side liquidity swept")
 if ev=="BSL_SWEEP":add("S",15,"Buy-side liquidity swept")
 r=features.get("rsi14")
 if r is not None:
  if r>55:add("B",10,"Positive momentum")
  elif r<45:add("S",10,"Negative momentum")
 e20,e50=features.get("ema20"),features.get("ema50")
 if e20 and e50:add("B" if e20>e50 else "S",15,"EMA trend context")
 price=features.get("price")
 for z in zones[-4:]:
  if price is not None and z["low"]<=price<=z["high"]:add("B" if z["type"]=="DEMAND" else "S",15,"Price inside fresh S/D zone")
 if structure.bos:add("B" if structure.bos=="BULLISH" else "S",10,"Confirmed BOS")
 if structure.choch:add("B" if structure.choch=="BULLISH" else "S",5,"CHOCH warning/confirmation")
 top=max(bull,bear);margin=abs(bull-bear);score=min(100,top)
 if score<min_score or margin<15:return SetupDecision("WAIT",score,grade(score),tuple(br if bull>=bear else sr),tuple(sr if bull>=bear else br),margin,"QUALITY")
 d="BUY" if bull>bear else "SELL";return SetupDecision(d,score,grade(score),tuple(br if d=="BUY" else sr),tuple(sr if d=="BUY" else br),margin)
