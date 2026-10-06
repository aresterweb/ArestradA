from datetime import datetime,timezone,timedelta
from .market.quality import assess
from .features.advanced import feature_set
from .intelligence.structure import analyze as structure
from .intelligence.liquidity import analyze as liquidity
from .intelligence.context import context
from .intelligence.fvg import detect as fvg
from .intelligence.supply_demand import zones
from .decision.trading_setup import evaluate
from .risk.planner import plan
from .news.guard import evaluate as news_guard
class Analyzer:
 def __init__(self,news="UNKNOWN",news_fail_closed=True,trade_min=72):self.news=news;self.news_fail_closed=news_fail_closed;self.trade_min=trade_min
 def analyze(self,frames):
  m15=frames.get("15min") or frames.get("M15") or []
  q=assess(m15,datetime.now(timezone.utc),timedelta(seconds=1800)); f=feature_set(m15);s=structure(m15);liq=liquidity(m15);ctx=context(m15);zs=zones(m15);fg=fvg(m15);ng=news_guard(self.news,self.news_fail_closed)
  mtf={}
  for tf,cs in frames.items():
   if len(cs)>=20:mtf[tf]=structure(cs).state
  setup=evaluate(q.state.value,s,liq,ctx,f,"BLOCKED" if ng.blocked else ng.status,zs,fg,self.trade_min)
  risk=plan(setup.decision,m15[-1].close,f.get("atr14"),s.protected) if m15 else None
  return {"quality":q.state.value,"quality_reason":q.reason,"bias":s.state,"mtf":mtf,"context":ctx,"structure":s,"liquidity":liq,"fvg":fg,"zones":zs,"features":f,"setup":setup,"risk":risk,"news":ng.status,"news_reason":ng.reason}
