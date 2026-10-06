import sqlite3,pathlib,json,datetime,uuid
SCHEMA="""
PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,telegram_user_id INTEGER UNIQUE NOT NULL,username TEXT,language TEXT DEFAULT 'id',timezone TEXT DEFAULT 'Asia/Jakarta',role TEXT DEFAULT 'USER',plan TEXT DEFAULT 'FREE',access_source TEXT DEFAULT 'DEFAULT',expires_at TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,last_seen_at TEXT);
CREATE TABLE IF NOT EXISTS access_grants(id INTEGER PRIMARY KEY,user_id INTEGER,source TEXT,features TEXT,duration TEXT,expires_at TEXT,granted_by INTEGER,revoked_at TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS predictions(id TEXT PRIMARY KEY,target_time TEXT NOT NULL,direction TEXT,score INTEGER,status TEXT DEFAULT 'LOCKED',strategy_version TEXT,snapshot_json TEXT,outcome TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(target_time,strategy_version));
CREATE TABLE IF NOT EXISTS setups(id TEXT PRIMARY KEY,decision TEXT,score INTEGER,grade TEXT,state TEXT,plan_json TEXT,strategy_version TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT);
CREATE TABLE IF NOT EXISTS setup_events(id INTEGER PRIMARY KEY,setup_id TEXT,event TEXT,detail TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY,telegram_payment_charge_id TEXT UNIQUE NOT NULL,user_id INTEGER,plan TEXT,stars INTEGER CHECK(stars>0),status TEXT,subscription_expiration_date INTEGER,is_recurring INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS subscriptions(id INTEGER PRIMARY KEY,user_id INTEGER,plan TEXT,status TEXT,start_at TEXT,expires_at TEXT,charge_id TEXT,auto_renew INTEGER DEFAULT 1,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS usage_counters(user_id INTEGER,day TEXT,feature TEXT,count INTEGER DEFAULT 0,PRIMARY KEY(user_id,day,feature));
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY,actor_id INTEGER,action TEXT,target TEXT,detail TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS invites(id INTEGER PRIMARY KEY,token_hash TEXT UNIQUE,role TEXT,plan TEXT,expires_at TEXT,used_by INTEGER,created_by INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS alert_preferences(user_id INTEGER PRIMARY KEY,enabled INTEGER DEFAULT 1,min_grade TEXT DEFAULT 'A',directions TEXT DEFAULT 'BUY,SELL',updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS alert_deliveries(id INTEGER PRIMARY KEY,user_id INTEGER,alert_key TEXT,alert_type TEXT,status TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(user_id,alert_key,alert_type));
"""

class DB:
 def __init__(self,path):pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True);self.path=path;self.init()
 def con(self):c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row;return c
 def init(self):
  with self.con() as c:c.executescript(SCHEMA)
 def audit(self,actor,action,target='',detail=None):
  with self.con() as c:c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(actor,action,str(target),json.dumps(detail or {},ensure_ascii=False)))
 def upsert_user(self,tid,username=None):
  with self.con() as c:
   c.execute("INSERT INTO users(telegram_user_id,username,last_seen_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(telegram_user_id) DO UPDATE SET username=CASE WHEN excluded.username IS NOT NULL AND excluded.username!='' THEN excluded.username ELSE users.username END,last_seen_at=CURRENT_TIMESTAMP",(tid,username))
   return dict(c.execute("SELECT * FROM users WHERE telegram_user_id=?",(tid,)).fetchone())
 def enforce_expiry(self,tid):
  with self.con() as c:
   row=c.execute("SELECT id,plan,expires_at FROM users WHERE telegram_user_id=?",(tid,)).fetchone()
   if not row or row["plan"] in ("FREE","INTERNAL"):
    return False
   if not row["expires_at"]:
    return False
   if row["expires_at"] <= datetime.datetime.now(datetime.timezone.utc).isoformat():
    c.execute("UPDATE users SET plan='FREE',access_source='DEFAULT',expires_at=NULL WHERE telegram_user_id=?",(tid,))
    c.execute("UPDATE subscriptions SET status='EXPIRED',updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND status='ACTIVE'",(row["id"],))
    return True
   return False

 def user(self,tid):
  with self.con() as c:r=c.execute("SELECT * FROM users WHERE telegram_user_id=?",(tid,)).fetchone();return dict(r) if r else None
 def recent_users(self,limit=10):
  with self.con() as c:return [dict(r) for r in c.execute("SELECT * FROM users ORDER BY COALESCE(last_seen_at,created_at) DESC LIMIT ?",(int(limit),)).fetchall()]
 def set_access(self,tid,plan,source="OWNER_GRANT",expires_at=None,actor=0):
  with self.con() as c:
   row=c.execute("SELECT id FROM users WHERE telegram_user_id=?",(tid,)).fetchone()
   if not row: raise ValueError('USER_NOT_FOUND')
   c.execute("UPDATE users SET plan=?,access_source=?,expires_at=? WHERE telegram_user_id=?",(plan,source,expires_at,tid))
   c.execute("INSERT INTO access_grants(user_id,source,features,duration,expires_at,granted_by) VALUES(?,?,?,?,?,?)",(row[0],source,'*','CUSTOM',expires_at,actor))
   c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(actor,"GRANT_ACCESS",str(tid),json.dumps({"plan":plan,"source":source,"expires_at":expires_at})))
 def grant_special(self,tid,duration='30d',actor=0):
  now=datetime.datetime.now(datetime.timezone.utc);d=(duration or '30d').lower()
  if d in ('lifetime','life','forever'): exp=None
  else:
   days={'7d':7,'30d':30,'90d':90,'1y':365}.get(d)
   if not days: raise ValueError('INVALID_DURATION')
   exp=(now+datetime.timedelta(days=days)).isoformat()
  self.set_access(tid,'SPECIAL','OWNER_GRANT',exp,actor);return exp
 def revoke_access(self,tid,actor=0):
  with self.con() as c:
   c.execute("UPDATE users SET plan='FREE',access_source='DEFAULT',expires_at=NULL WHERE telegram_user_id=?",(tid,))
   c.execute("UPDATE access_grants SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=(SELECT id FROM users WHERE telegram_user_id=?) AND revoked_at IS NULL",(tid,))
   c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(actor,'REVOKE_ACCESS',str(tid),'{}'))
 def set_role(self,tid,role,actor=0):
  role=(role or '').upper()
  if role not in ('USER','ADMIN','SUPPORT'): raise ValueError('INVALID_ROLE')
  with self.con() as c:
   if not c.execute("SELECT 1 FROM users WHERE telegram_user_id=?",(tid,)).fetchone(): raise ValueError('USER_NOT_FOUND')
   c.execute("UPDATE users SET role=? WHERE telegram_user_id=?",(role,tid))
   c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(actor,'SET_ROLE',str(tid),json.dumps({'role':role})))
 def get_setting(self,key,default=None):
  with self.con() as c:r=c.execute("SELECT value FROM system_settings WHERE key=?",(key,)).fetchone();return r[0] if r else default
 def set_setting(self,key,value,actor=0):
  with self.con() as c:
   c.execute("INSERT INTO system_settings(key,value,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP",(key,str(value)))
   c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(actor,'SET_SETTING',key,json.dumps({'value':str(value)})))
 def save_payment(self,charge,tid,plan,stars,expiry=None,recurring=False):
  now=datetime.datetime.now(datetime.timezone.utc); exp=datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc) if expiry else now+datetime.timedelta(days=30)
  with self.con() as c:
   c.execute("BEGIN IMMEDIATE");u=c.execute("SELECT id FROM users WHERE telegram_user_id=?",(tid,)).fetchone();uid=u[0] if u else None
   cur=c.execute("INSERT OR IGNORE INTO payments(telegram_payment_charge_id,user_id,plan,stars,status,subscription_expiration_date,is_recurring) VALUES(?,?,?,?,?,?,?)",(charge,uid,plan,stars,"PAID",expiry,int(recurring)))
   if cur.rowcount:
    c.execute("UPDATE users SET plan=?,access_source='PAYMENT',expires_at=? WHERE telegram_user_id=?",(plan,exp.isoformat(),tid));c.execute("INSERT INTO subscriptions(user_id,plan,status,start_at,expires_at,charge_id) VALUES(?,?, 'ACTIVE',?,?,?)",(uid,plan,now.isoformat(),exp.isoformat(),charge))
    c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(tid,'PAYMENT_SUCCESS',str(tid),json.dumps({'plan':plan,'stars':stars,'charge_id':charge})))
   return bool(cur.rowcount)
 def mark_alert(self,tid,key,typ,status='SENT'):
  with self.con() as c:
   try:c.execute("INSERT INTO alert_deliveries(user_id,alert_key,alert_type,status) VALUES((SELECT id FROM users WHERE telegram_user_id=?),?,?,?)",(tid,key,typ,status));return True
   except sqlite3.IntegrityError:return False
 def alert_users(self):
  with self.con() as c:
   return [dict(r) for r in c.execute("SELECT telegram_user_id,plan FROM users WHERE plan IN ('ELITE','SPECIAL','INTERNAL') AND (expires_at IS NULL OR expires_at>CURRENT_TIMESTAMP)").fetchall()]
 def stats(self):
  with self.con() as c:
   return {"users":c.execute("SELECT count(*) FROM users").fetchone()[0],"paid":c.execute("SELECT count(*) FROM users WHERE plan IN ('PRO','ELITE')").fetchone()[0],"special":c.execute("SELECT count(*) FROM users WHERE plan='SPECIAL'").fetchone()[0],"stars":c.execute("SELECT coalesce(sum(stars),0) FROM payments WHERE status='PAID'").fetchone()[0]}
