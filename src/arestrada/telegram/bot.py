import json,urllib.request,urllib.parse,time
class TelegramBot:
 def __init__(self,token,handler,precheckout=None,payment=None):self.base=f"https://api.telegram.org/bot{token}/";self.handler=handler;self.precheckout=precheckout;self.payment=payment
 def call(self,m,p=None):
  data=urllib.parse.urlencode(p or {}).encode();req=urllib.request.Request(self.base+m,data=data)
  with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
 def send(self,chat,text,markup=None):
  p={"chat_id":chat,"text":text};
  if markup:p["reply_markup"]=json.dumps(markup)
  return self.call("sendMessage",p)
 def invoice(self,chat,fields):p={"chat_id":chat,**fields};return self.call("sendInvoice",p)
 def poll(self):
  off=0;delay=2
  while True:
   try:
    rs=self.call("getUpdates",{"timeout":25,"offset":off,"allowed_updates":json.dumps(["message","pre_checkout_query","callback_query"]) }).get("result",[]);delay=2
    for u in rs:
     off=u["update_id"]+1
     if "pre_checkout_query" in u:
      q=u["pre_checkout_query"];ok,msg=self.precheckout(q) if self.precheckout else (False,"Payments disabled");self.call("answerPreCheckoutQuery",{"pre_checkout_query_id":q["id"],"ok":"true" if ok else "false",**({} if ok else {"error_message":msg})});continue
     if "callback_query" in u:
      q=u["callback_query"];self.call("answerCallbackQuery",{"callback_query_id":q["id"]});m=q.get("message",{});chat=m.get("chat",{}).get("id");text=q.get("data","")
     else:
      m=u.get("message",{});chat=m.get("chat",{}).get("id");text=m.get("text","")
      if m.get("successful_payment") and self.payment:self.payment(chat,m["successful_payment"])
     if chat:
      res=self.handler(chat,text,m)
      if isinstance(res,tuple):self.send(chat,res[0],res[1])
      elif res:self.send(chat,res)
   except Exception as e:print("telegram retry:",type(e).__name__);time.sleep(delay);delay=min(30,delay*2)
