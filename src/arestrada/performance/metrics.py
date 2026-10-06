def accuracy(rows):
 resolved=[r for r in rows if r in ("WIN","LOSS")]; return None if not resolved else 100*sum(r=="WIN" for r in resolved)/len(resolved)
def setup_metrics(rs):
 w=sum(x=="WIN" for x in rs);l=sum(x=="LOSS" for x in rs);b=sum(x=="BREAKEVEN" for x in rs);n=w+l
 return {"win_rate":None if not n else 100*w/n,"wins":w,"losses":l,"breakeven":b,"resolved":len(rs)}
