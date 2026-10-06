from dataclasses import dataclass
from arestrada.market.candles import Candle

@dataclass(frozen=True, slots=True)
class Swing:
    index:int; kind:str; price:float; confirmed_at_index:int

def confirmed_swings(candles:list[Candle], left:int=2, right:int=2)->list[Swing]:
    out=[]
    for i in range(left,len(candles)-right):
        h=candles[i].high; l=candles[i].low
        if all(h>candles[j].high for j in range(i-left,i)) and all(h>=candles[j].high for j in range(i+1,i+right+1)):
            out.append(Swing(i,"HIGH",h,i+right))
        if all(l<candles[j].low for j in range(i-left,i)) and all(l<=candles[j].low for j in range(i+1,i+right+1)):
            out.append(Swing(i,"LOW",l,i+right))
    return out
