from dataclasses import dataclass
from .swings import confirmed_swings
from arestrada.features.advanced import feature_set
@dataclass(frozen=True)
class Structure:
 state:str; bos:str|None; choch:str|None; protected:float|None; strength:int=0; external:str="UNDEFINED"
def analyze(candles):
 s=confirmed_swings(candles,2,2); highs=[x for x in s if x.kind=="HIGH"]; lows=[x for x in s if x.kind=="LOW"]
 if len(highs)<2 or len(lows)<2:return Structure("UNDEFINED",None,None,None,0)
 hh=highs[-1].price>highs[-2].price; hl=lows[-1].price>lows[-2].price
 lh=highs[-1].price<highs[-2].price; ll=lows[-1].price<lows[-2].price
 state="BULLISH" if hh and hl else "BEARISH" if lh and ll else "RANGING"
 f=feature_set(candles);atr=f.get("atr14") or 0;c=candles[-1]; body=abs(c.close-c.open)
 bullbreak=c.close>highs[-1].price and (not atr or body>=.25*atr)
 bearbreak=c.close<lows[-1].price and (not atr or body>=.25*atr)
 bos="BULLISH" if bullbreak else "BEARISH" if bearbreak else None
 choch="BEARISH" if state=="BULLISH" and bearbreak else "BULLISH" if state=="BEARISH" and bullbreak else None
 protected=lows[-1].price if state=="BULLISH" else highs[-1].price if state=="BEARISH" else None
 strength=min(100,40+(20 if state!="RANGING" else 0)+(20 if bos else 0)+(20 if body and atr and body>=.5*atr else 0))
 return Structure(state,bos,choch,protected,strength,state)
