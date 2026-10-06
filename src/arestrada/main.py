import argparse
from .core.config import Settings
from .persistence.db import DB
from .market.twelvedata import TwelveDataProvider
from .application import Analyzer
from .telegram.renderers import dashboard,pulse,analysis,account,upgrade
from .telegram.bot import TelegramBot
from .billing.stars import invoice,parse_payload

def frames(s,p): return {tf:p.candles(s.symbol,tf,200) for tf in ("5min","15min","1h","4h","1day")}
def main():
 a=argparse.ArgumentParser();a.add_argument("--health",action="store_true");a.add_argument("--once",action="store_true");a.add_argument("--poll",action="store_true");x=a.parse_args();s=Settings();db=DB(s.db_path)
 if x.health:
  print("ARESTRADA V4 HEALTHY\nDB: OK\nSafety: fail-closed\nProvider key:","SET" if s.api_key else "MISSING","\nTelegram:","SET" if s.bot_token else "MISSING","\nPayments:","ENABLED" if s.payment_enabled else "DISABLED");return
 p=TwelveDataProvider(s.api_key,s.api_timeout);an=Analyzer(s.news_status,s.news_fail_closed,s.trade_min_score)
 def get(): return an.analyze(frames(s,p))
 if x.once: print(pulse(get()));return
 if x.poll:
  if not s.bot_token: raise SystemExit("TELEGRAM_BOT_TOKEN missing")
  bot=None
  def handler(chat,text,msg):
   nonlocal bot
   fr=msg.get("from",{}) if isinstance(msg,dict) else {};u=db.upsert_user(chat,fr.get("username"))
   if chat==s.owner_id and u['plan']!='INTERNAL': db.set_access(chat,'INTERNAL','OWNER',None,chat);u=db.user(chat)
   if text in ("/start","/menu","menu"): return dashboard(u['plan'])
   if text in ("pulse","/pulse","⚡ market pulse"):
    try:return pulse(get())
    except Exception:return "ANALYSIS UNAVAILABLE\nNo signal generated.\nMarket data could not be verified."
   if text in ("analysis","/analysis"):
    try:return analysis(get())
    except Exception:return "ANALYSIS UNAVAILABLE\nNo signal generated."
   if text in ("account","/account"): return account(u)
   if text in ("upgrade","/upgrade"): return upgrade(s.pro_stars,s.elite_stars)
   if text.startswith("buy:"):
    plan=text.split(":",1)[1];prices={"PRO":s.pro_stars,"ELITE":s.elite_stars}
    if not s.payment_enabled:return "Payments are currently disabled."
    if plan not in prices:return "Invalid plan."
    bot.invoice(chat,invoice(plan,prices));return None
   if text=="stats" and chat==s.owner_id:return str(db.stats())
   if text=="/paysupport":return "Payment support: contact ArestradA support and include your Telegram payment receipt ID. Never send passwords or wallet seed phrases."
   if text=="/terms":return "ArestradA provides market analysis and decision support only. No profit is guaranteed. Trading involves risk. Premium access renews every 30 days until cancelled."
   if text=="/privacy":return "ArestradA stores the minimum account, usage and payment metadata needed to operate the service. Credentials and wallet private keys are never requested."
   return dashboard(u['plan'])
  def pre(q):
   if not s.payment_enabled:return False,"Payments disabled"
   plan=parse_payload(q.get("invoice_payload",""));prices={"PRO":s.pro_stars,"ELITE":s.elite_stars}
   ok=bool(plan and q.get("currency")=="XTR" and q.get("total_amount")==prices.get(plan));return ok,"Invalid or changed invoice"
  def paid(chat,sp):
   plan=parse_payload(sp.get("invoice_payload",""));prices={"PRO":s.pro_stars,"ELITE":s.elite_stars}
   if plan and sp.get("currency")=="XTR" and sp.get("total_amount")==prices[plan]:db.save_payment(sp["telegram_payment_charge_id"],chat,plan,prices[plan],sp.get("subscription_expiration_date"),sp.get("is_recurring",False))
  bot=TelegramBot(s.bot_token,handler,pre,paid);bot.poll()
if __name__=="__main__":main()
