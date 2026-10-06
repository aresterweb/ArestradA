import json, os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import parse_qs

from .bot import TelegramBot
from .renderers import dashboard,pulse,analysis,next_m15,stats_view,account,upgrade,owner_panel,owner_special_help,owner_staff_help,owner_news_controls,owner_emergency_controls
from ..core.config import Settings
from ..persistence.db import DB
from ..market.twelvedata import TwelveDataProvider
from ..application import Analyzer
from ..decision.next_candle import predict
from ..market.snapshots import MarketSnapshot
from ..market.quality import assess
from ..billing.stars import invoice,parse_payload

S=Settings(); DBX=DB(S.db_path)
BOT=TelegramBot(S.bot_token, lambda *_: None)
PROVIDER=TwelveDataProvider(S.api_key,S.api_timeout)
SECRET=os.getenv('TELEGRAM_WEBHOOK_SECRET','')

def frames(): return {tf:PROVIDER.candles(S.symbol,tf,200) for tf in ('5min','15min','1h','4h','1day')}

def effective_news_status():
    status=DBX.get_setting('news_override_status')
    until=DBX.get_setting('news_override_until')
    if status:
        if until:
            try:
                if datetime.now(timezone.utc)>=datetime.fromisoformat(until):
                    DBX.set_setting('news_override_status','UNKNOWN',S.owner_id);DBX.set_setting('news_override_until','',S.owner_id);return 'UNKNOWN'
            except Exception:return 'UNKNOWN'
        return status.upper()
    return S.news_status

def get_analysis(): return Analyzer(effective_news_status(),S.news_fail_closed,S.trade_min_score).analyze(frames())

def get_next_m15():
    fs=frames();m15=fs.get('15min',[]);q=assess(m15,datetime.now(timezone.utc),timedelta(seconds=1800));snap=MarketSnapshot('telegram-live',S.symbol,datetime.now(timezone.utc),'TwelveData',q.state,{'M15':tuple(m15)});pred=predict(snap)
    target=(m15[-1].ts+timedelta(minutes=15)).astimezone(ZoneInfo(S.timezone or 'Asia/Jakarta')).strftime('%d %b %Y %H:%M %Z') if m15 else '—'
    return next_m15(pred,target,q.state.value,q.reason),pred,target

def safe_send(chat,res):
    if isinstance(res,tuple):BOT.send(chat,res[0],res[1])
    elif res:BOT.send(chat,res)
def _is_owner(chat):return bool(S.owner_id and chat==S.owner_id)

def _owner_users():
    rows=DBX.recent_users(10);lines=['OWNER • USERS','━━━━━━━━━━━━━━━━━━']
    for r in rows:
        tid=int(r['telegram_user_id'])
        if tid==S.owner_id:
            lines.append(f"OWNER • ID {tid} • {r['plan']} • OWNER")
        else:
            name=('@'+r['username']) if r.get('username') else str(tid)
            lines.append(f"{name} • ID {tid} • {r['plan']} • {r['role']}")
    return '\n'.join(lines) if rows else 'OWNER • USERS\nNo users yet.'
def _owner_special():
    with DBX.con() as c:rows=c.execute("SELECT telegram_user_id,username,plan,access_source,expires_at FROM users WHERE plan='SPECIAL' OR access_source='OWNER_GRANT' ORDER BY id DESC LIMIT 10").fetchall()
    lines=['OWNER • SPECIAL','━━━━━━━━━━━━━━━━━━'];lines.extend((('@'+r['username']) if r['username'] else str(r['telegram_user_id']))+f" • until {r['expires_at'] or 'LIFETIME'}" for r in rows)
    text='\n'.join(lines) if rows else 'OWNER • SPECIAL\nNo SPECIAL members.'
    return text+'\n\n'+owner_special_help()
def _owner_staff():
    with DBX.con() as c:rows=c.execute("SELECT telegram_user_id,username,role,plan FROM users WHERE role!='USER' ORDER BY id DESC LIMIT 10").fetchall()
    lines=['OWNER • STAFF','━━━━━━━━━━━━━━━━━━'];lines.extend((('@'+r['username']) if r['username'] else str(r['telegram_user_id']))+f" • {r['role']} • {r['plan']}" for r in rows)
    if not rows:lines.append('No delegated ADMIN/SUPPORT accounts yet.')
    return '\n'.join(lines)+'\n\n'+owner_staff_help()
def _owner_revenue():
    s=DBX.stats();
    with DBX.con() as c:count=c.execute("SELECT count(*) FROM payments WHERE status='PAID'").fetchone()[0]
    return f"OWNER • REVENUE\n━━━━━━━━━━━━━━━━━━\nPaid transactions • {count}\nPaid users • {s.get('paid',0)}\nStars received • {s.get('stars',0)}"
def _owner_performance():
    with DBX.con() as c:total=c.execute("SELECT count(*) FROM predictions").fetchone()[0];resolved=c.execute("SELECT count(*) FROM predictions WHERE outcome IS NOT NULL").fetchone()[0];setups=c.execute("SELECT count(*) FROM setups").fetchone()[0]
    return f"OWNER • PERFORMANCE\n━━━━━━━━━━━━━━━━━━\nPredictions logged • {total}\nResolved • {resolved}\nSetups logged • {setups}\n\nNo performance claim is shown without resolved official records."
def _owner_strategy():return f"OWNER • STRATEGY\n━━━━━━━━━━━━━━━━━━\nPrimary • ARS-XAU-4.0.0\nNext M15 minimum • {S.next_min_score}\nTrade minimum • {S.trade_min_score}\nNews fail-closed • {'ON' if S.news_fail_closed else 'OFF'}"
def _owner_system():return f"OWNER • SYSTEM\n━━━━━━━━━━━━━━━━━━\nMarket provider key • {'SET' if S.api_key else 'MISSING'}\nTelegram token • {'SET' if S.bot_token else 'MISSING'}\nPayments capability • {'ARMED' if S.payment_enabled else 'DISABLED'}\nAuto alert capability • {'ARMED' if S.auto_alert else 'DISABLED'}\nNews status • {effective_news_status()}\nSafety • FAIL-CLOSED"
def payments_open():return bool(S.payment_enabled and DBX.get_setting('payments_paused','0')!='1')
def alerts_open():return bool(S.auto_alert and DBX.get_setting('alerts_paused','0')!='1')
def _owner_payments():return f"OWNER • PAYMENTS\n━━━━━━━━━━━━━━━━━━\nStars capability • {'ARMED' if S.payment_enabled else 'DISABLED'}\nRuntime payments • {'ON' if payments_open() else 'OFF'}\nPRO • ⭐ {S.pro_stars} / 30 days\nELITE • ⭐ {S.elite_stars} / 30 days\n\nEnable capability only after test checkout succeeds. Payment charge IDs are stored idempotently."
def _owner_audit():
    with DBX.con() as c:rows=c.execute("SELECT action,target,created_at FROM audit_logs ORDER BY id DESC LIMIT 8").fetchall()
    return 'OWNER • AUDIT\nNo audit events yet.' if not rows else 'OWNER • AUDIT\n━━━━━━━━━━━━━━━━━━\n'+'\n'.join(f"{r['created_at']} • {r['action']} • {r['target']}" for r in rows)
def _owner_emergency():return owner_emergency_controls(payments_open(),alerts_open())
def _data_status():
    try:a=get_analysis();return f"ARESTRADA • DATA STATUS\n━━━━━━━━━━━━━━━━━━\nXAU/USD\nData • {a['quality']}\nReason • {a['quality_reason']}\nNews • {a['news']}\n\nInvalid/stale data blocks predictions."
    except Exception:return 'ARESTRADA • DATA STATUS\nData verification unavailable.\nSignals remain blocked.'
def _news_status():
    try:a=get_analysis();return f"ARESTRADA • NEWS SAFETY\n━━━━━━━━━━━━━━━━━━\nStatus • {a['news']}\nReason • {a.get('news_reason','—')}\n\nUNKNOWN is not treated as CLEAR."
    except Exception:return 'ARESTRADA • NEWS SAFETY\nStatus • UNKNOWN\nConservative safety mode remains active.'
def _timer():
    tz=ZoneInfo(S.timezone or 'Asia/Jakarta');now=datetime.now(tz)
    def left(minutes):
        base=now.replace(second=0,microsecond=0);add=minutes-(base.minute%minutes) if base.minute%minutes else minutes;nxt=base+timedelta(minutes=add);sec=max(0,int((nxt-now).total_seconds()));return f"{sec//60:02d}:{sec%60:02d}"
    return f"ARESTRADA • CANDLE TIMER\n━━━━━━━━━━━━━━━━━━\nM5 • {left(5)}\nM15 • {left(15)}\nH1 • {left(60)}\nTimezone • {S.timezone or 'Asia/Jakarta'}"

def handle(chat,text,msg):
    fr=msg.get('from',{}) if isinstance(msg,dict) else {};u=DBX.upsert_user(chat,fr.get('username'));DBX.enforce_expiry(chat);u=DBX.user(chat)
    if _is_owner(chat) and (u['plan']!='INTERNAL' or u['access_source']!='OWNER'):DBX.set_access(chat,'INTERNAL','OWNER',None,chat);u=DBX.user(chat)
    text=(text or '').strip();low=text.lower();owner=_is_owner(chat)
    if low in ('/start','/menu','menu'):return dashboard(u['plan'],owner)
    if low in ('pulse','/pulse','⚡ market pulse'):
        try:return pulse(get_analysis())
        except Exception:return 'ANALYSIS UNAVAILABLE\nNo signal generated.\nMarket data could not be verified.'
    if low in ('next','/next','/nextm15','🔮 next m15','🔮 next candle','next candle'):
        try:return get_next_m15()[0]
        except Exception:return 'NEXT M15 UNAVAILABLE\nNo prediction generated.\nMarket data could not be verified.'
    if low in ('analysis','/analysis','📈 analysis','🕯 m15 analysis','m15 analysis','/m15','📈 signal','signal'):
        try:return analysis(get_analysis())
        except Exception:return 'ANALYSIS UNAVAILABLE\nNo signal generated.'
    if low in ('account','/account','👤 account'):return account(u)
    if low in ('upgrade','/upgrade','⭐ upgrade'):
        if u['plan'] in ('ELITE','SPECIAL','INTERNAL'):return 'Your account already has full premium access.'
        return upgrade(S.pro_stars,S.elite_stars)
    if low.startswith('buy:'):
        plan=text.split(':',1)[1].upper();prices={'PRO':S.pro_stars,'ELITE':S.elite_stars}
        if not payments_open():return 'Payments are currently disabled.'
        if plan not in prices:return 'Invalid plan.'
        BOT.invoice(chat,invoice(plan,prices));return None
    if low in ('stats','/stats','📊 stats','📊 performance','performance'):return stats_view(DBX.stats()) if owner else 'ARESTRADA • PERFORMANCE\nOfficial performance will be shown after enough predictions are resolved.'
    if low in ('🟢 data status','data status','/data'):return _data_status()
    if low in ('📰 news safety','news safety','/news'):return _news_status()
    if low in ('⏱ candle timer','candle timer','/timer'):return _timer()
    if low in ('ℹ help','help','/help'):return 'ARESTRADA • HELP\n━━━━━━━━━━━━━━━━━━\n/start • Main menu\n/m15 • M15 analysis\n/nextm15 • Next M15\n/data • Data status\n/news • News safety\n/timer • Candle timer\n/account • Account'
    if low in ('owner','/owner','🛡 owner panel'):return owner_panel(DBX.stats()) if owner else 'Access denied.'
    if low.startswith('/special '):
        if not owner:return 'Access denied.'
        p=text.split()
        if len(p)!=3:return 'Usage: /special <telegram_id> <7d|30d|90d|1y|lifetime>'
        try:tid=int(p[1]);exp=DBX.grant_special(tid,p[2],chat);return f"SPECIAL granted to {tid}\nExpires • {exp or 'LIFETIME'}"
        except ValueError as e:return f"SPECIAL grant failed • {e}"
    if low.startswith('/revoke '):
        if not owner:return 'Access denied.'
        try:tid=int(text.split()[1]);DBX.revoke_access(tid,chat);return f"Access revoked for {tid}."
        except Exception:return 'Usage: /revoke <telegram_id>'
    if low.startswith('/staff '):
        if not owner:return 'Access denied.'
        p=text.split()
        if len(p)!=3:return 'Usage: /staff <telegram_id> <ADMIN|SUPPORT|USER>'
        try:tid=int(p[1]);
        except Exception:return 'Invalid Telegram ID.'
        if tid==S.owner_id:return 'OWNER role cannot be changed here.'
        try:DBX.set_role(tid,p[2],chat);return f"Role updated • {tid} → {p[2].upper()}"
        except ValueError as e:return f"Role update failed • {e}"
    if low.startswith('owner:'):
        if not owner:return 'Access denied.'
        parts=low.split(':');action=parts[1] if len(parts)>1 else ''
        if action=='back':return dashboard(u['plan'],True)
        if action=='users':return _owner_users()
        if action=='special':return _owner_special()
        if action=='staff':return _owner_staff()
        if action=='revenue':return _owner_revenue()
        if action=='performance':return _owner_performance()
        if action=='strategy':return _owner_strategy()
        if action=='signals':
            try:return analysis(get_analysis())
            except Exception:return 'OWNER • LIVE ANALYSIS\nAnalysis unavailable.'
        if action=='system':return _owner_system()
        if action=='payments':return _owner_payments()
        if action=='news':
            if len(parts)>=4:
                status=parts[2].upper();mins=int(parts[3]);
                if status not in ('CLEAR','CAUTION','BLOCKED','UNKNOWN'):return 'Invalid news status.'
                until='' if mins<=0 else (datetime.now(timezone.utc)+timedelta(minutes=mins)).isoformat();DBX.set_setting('news_override_status',status,chat);DBX.set_setting('news_override_until',until,chat)
            return owner_news_controls(effective_news_status())
        if action=='audit':return _owner_audit()
        if action=='toggle' and len(parts)>=3:
            what=parts[2]
            if what=='payments':DBX.set_setting('payments_paused','0' if DBX.get_setting('payments_paused','0')=='1' else '1',chat)
            elif what=='alerts':DBX.set_setting('alerts_paused','0' if DBX.get_setting('alerts_paused','0')=='1' else '1',chat)
            return _owner_emergency()
        if action=='emergency':return _owner_emergency()
        return owner_panel(DBX.stats())
    if low=='/paysupport':return 'Payment support: contact ArestradA support and include your Telegram payment receipt ID. Never send passwords or wallet seed phrases.'
    if low=='/terms':return 'ArestradA provides market analysis and decision support only. No profit is guaranteed. Trading involves risk. Premium subscriptions use Telegram Stars and renew every 30 days until cancelled.'
    if low=='/privacy':return 'ArestradA stores the minimum account, usage and payment metadata needed to operate the service. Credentials and wallet private keys are never requested.'
    return dashboard(u['plan'],owner)

def _process_payment(chat,sp):
    plan=parse_payload(sp.get('invoice_payload',''));prices={'PRO':S.pro_stars,'ELITE':S.elite_stars}
    if plan and sp.get('currency')=='XTR' and sp.get('total_amount')==prices.get(plan):
        created=DBX.save_payment(sp['telegram_payment_charge_id'],chat,plan,prices[plan],sp.get('subscription_expiration_date'),sp.get('is_recurring',False))
        if created:BOT.send(chat,f"Payment confirmed. {plan} access is now active.")

def process(update):
    if 'pre_checkout_query' in update:
        q=update['pre_checkout_query'];plan=parse_payload(q.get('invoice_payload',''));prices={'PRO':S.pro_stars,'ELITE':S.elite_stars};ok=bool(payments_open() and plan and q.get('currency')=='XTR' and q.get('total_amount')==prices.get(plan));p={'pre_checkout_query_id':q['id'],'ok':'true' if ok else 'false'}
        if not ok:p['error_message']='Invalid, changed, or disabled invoice'
        BOT.call('answerPreCheckoutQuery',p);return
    if 'callback_query' in update:
        q=update['callback_query'];BOT.call('answerCallbackQuery',{'callback_query_id':q['id']});msg=dict(q.get('message',{}));msg['from']=q.get('from',{});chat=msg.get('chat',{}).get('id');text=q.get('data','')
    else:
        msg=update.get('message',{});chat=msg.get('chat',{}).get('id');text=msg.get('text','');sp=msg.get('successful_payment')
        if sp and chat:_process_payment(chat,sp)
    if chat:safe_send(chat,handle(chat,text,msg))

def run_auto_alert():
    if not alerts_open():return {'ok':False,'reason':'AUTO_ALERT_DISABLED_OR_PAUSED'}
    try:
        a=get_analysis();setup=a['setup'];fs=frames();m15=fs.get('15min',[]);key=(m15[-1].ts.isoformat() if m15 else datetime.now(timezone.utc).strftime('%Y%m%d%H%M'))
        if setup.decision not in ('BUY','SELL'):return {'ok':True,'sent':0,'decision':setup.decision}
        text='🟢 ARESTRADA • SETUP ALERT\n\n'+analysis(a);sent=0
        for u in DBX.alert_users():
            tid=u['telegram_user_id']
            if DBX.mark_alert(tid,key,'SETUP','QUEUED'):
                try:BOT.send(tid,text);sent+=1
                except Exception:pass
        return {'ok':True,'sent':sent,'decision':setup.decision}
    except Exception as e:return {'ok':False,'reason':type(e).__name__}

def reply(start,status,body,ctype='text/plain; charset=utf-8'):
    data=body.encode('utf-8');start(status,[('Content-Type',ctype),('Content-Length',str(len(data))),('Cache-Control','no-store')]);return [data]

def application(environ,start_response):
    path=environ.get('PATH_INFO','/')
    if environ.get('REQUEST_METHOD')=='GET':
        if path in ('/','/health'):return reply(start_response,'200 OK','ARESTRADA V4 WEBHOOK HEALTHY')
        if path=='/cron/m15':
            qs=parse_qs(environ.get('QUERY_STRING',''));token=environ.get('HTTP_X_ARESTRADA_CRON_SECRET','') or (qs.get('token') or [''])[0]
            if not S.cron_secret or token!=S.cron_secret:return reply(start_response,'403 Forbidden','Forbidden')
            return reply(start_response,'200 OK',json.dumps(run_auto_alert()),'application/json')
        return reply(start_response,'404 Not Found','Not found')
    if environ.get('REQUEST_METHOD')!='POST':return reply(start_response,'405 Method Not Allowed','Method not allowed')
    if SECRET and environ.get('HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN','')!=SECRET:return reply(start_response,'403 Forbidden','Forbidden')
    try:
        n=int(environ.get('CONTENT_LENGTH') or 0)
        if n<=0 or n>1048576:return reply(start_response,'400 Bad Request','Bad request')
        update=json.loads(environ['wsgi.input'].read(n).decode('utf-8'));process(update);return reply(start_response,'200 OK','OK')
    except Exception as e:
        print('webhook error:',type(e).__name__,flush=True);return reply(start_response,'500 Internal Server Error','Error')
