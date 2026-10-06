import json,time
PLANS={"PRO":250,"ELITE":500}
def payload(plan):return f"ARESTRADA:{plan}:30D"
def parse_payload(p):
 x=p.split(":");return x[1] if len(x)==3 and x[0]=="ARESTRADA" and x[2]=="30D" and x[1] in PLANS else None
def invoice(plan,prices=None):
 stars=(prices or PLANS)[plan]
 return {"title":f"ArestradA {plan}","description":f"{plan} access • recurring every 30 days", "payload":payload(plan),"currency":"XTR","prices":json.dumps([{"label":f"{plan} 30 days","amount":stars}]),"subscription_period":2592000}
