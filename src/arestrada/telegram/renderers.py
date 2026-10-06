def menu():
 return {"inline_keyboard":[[{"text":"⚡ Market Pulse","callback_data":"pulse"}],[{"text":"🔮 Next M15","callback_data":"next"},{"text":"📈 Analysis","callback_data":"analysis"}],[{"text":"📊 Stats","callback_data":"stats"},{"text":"👤 Account","callback_data":"account"}],[{"text":"⭐ Upgrade","callback_data":"upgrade"}]]}
def dashboard(plan="FREE"):
 return (f"""ARESTRADA
Market Intelligence
━━━━━━━━━━━━━━━━━━
XAU/USD
● Safety-first analysis

Plan • {plan}""",menu())
def pulse(a):
 mtf="\n".join(f"{k.upper():5} {v}" for k,v in a.get("mtf",{}).items())
 return f"""ARESTRADA • MARKET PULSE
━━━━━━━━━━━━━━━━━━
XAU/USD

BIAS • {a['bias']}
Context • {a['context']}
{mtf}

Setup • {a['setup'].decision}
Quality • {a['setup'].score}/100
Data • {a['quality']} ({a['quality_reason']})
News • {a['news']}

Analysis only"""
def analysis(a):
 s=a['setup'];rs='\n'.join('• '+x for x in s.reasons) or '• No qualified evidence';ct='\n'.join('− '+x for x in s.counter) or '• None'
 risk=a.get('risk');rp='No trade plan' if not risk else f"Entry {risk['entry']:.2f}\nSL {risk['sl']:.2f}\nTP1 {risk['tp1']:.2f} • 1.5R\nTP2 {risk['tp2']:.2f} • 2.0R"
 return f"""ARESTRADA • FULL ANALYSIS
━━━━━━━━━━━━━━━━━━
Bias {a['bias']} • {a['context']}
BOS {a['structure'].bos or '-'} • CHOCH {a['structure'].choch or '-'}
Liquidity {a['liquidity'].get('event') or 'NONE'}

DECISION • {s.decision}
Grade {s.grade} • Confluence {s.score}/100

Evidence
{rs}

Counter Evidence
{ct}

RISK PLAN
{rp}

Data {a['quality']} • News {a['news']}
Analysis only"""
def account(u):
 return f"MY ACCOUNT\n━━━━━━━━━━━━━━━━━━\nUser {u['telegram_user_id']}\nPlan • {u['plan']}\nAccess • {u['access_source']}\nExpires • {u.get('expires_at') or '—'}"
def upgrade(pro,elite):
 return (f"UPGRADE ARESTRADA\n━━━━━━━━━━━━━━━━━━\nPRO • ⭐ {pro} / 30 days\nELITE • ⭐ {elite} / 30 days\n\nSubscriptions renew every 30 days until cancelled.",{"inline_keyboard":[[{"text":f"⭐ PRO • {pro}","callback_data":"buy:PRO"}],[{"text":f"⭐ ELITE • {elite}","callback_data":"buy:ELITE"}]]})
