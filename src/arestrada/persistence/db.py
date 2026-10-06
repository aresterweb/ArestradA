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
"""
class DB:
 def __init__(self,path):pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True);self.path=path;self.init()
 def con(self):c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row;return c
 def init(self):
  with self.con() as c:c.executescript(SCHEMA)
 def upsert_user(self,tid,username=None):
  with self.con() as c:
   c.execute("INSERT INTO users(telegram_user_id,username,last_seen_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(telegram_user_id) DO UPDATE SET username=excluded.username,last_seen_at=CURRENT_TIMESTAMP",(tid,username));return dict(c.execute("SELECT * FROM users WHERE telegram_user_id=?",(tid,)).fetchone())
 def user(self,tid):
  with self.con() as c:r=c.execute("SELECT * FROM users WHERE telegram_user_id=?",(tid,)).fetchone();return dict(r) if r else None
 def set_access(self,tid,plan,source="OWNER_GRANT",expires_at=None,actor=0):
  with self.con() as c:
   c.execute("UPDATE users SET plan=?,access_source=?,expires_at=? WHERE telegram_user_id=?",(plan,source,expires_at,tid));c.execute("INSERT INTO audit_logs(actor_id,action,target,detail) VALUES(?,?,?,?)",(actor,"GRANT_ACCESS",str(tid),json.dumps({"plan":plan,"source":source,"expires_at":expires_at})))
 def save_payment(self,charge,tid,plan,stars,expiry=None,recurring=False):
  now=datetime.datetime.now(datetime.timezone.utc); exp=datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc) if expiry else now+datetime.timedelta(days=30)
  with self.con() as c:
   c.execute("BEGIN IMMEDIATE");u=c.execute("SELECT id FROM users WHERE telegram_user_id=?",(tid,)).fetchone();uid=u[0] if u else None
   cur=c.execute("INSERT OR IGNORE INTO payments(telegram_payment_charge_id,user_id,plan,stars,status,subscription_expiration_date,is_recurring) VALUES(?,?,?,?,?,?,?)",(charge,uid,plan,stars,"PAID",expiry,int(recurring)))
   if cur.rowcount:
    c.execute("UPDATE users SET plan=?,access_source='PAYMENT',expires_at=? WHERE telegram_user_id=?",(plan,exp.isoformat(),tid));c.execute("INSERT INTO subscriptions(user_id,plan,status,start_at,expires_at,charge_id) VALUES(?,?, 'ACTIVE',?,?,?)",(uid,plan,now.isoformat(),exp.isoformat(),charge))
   return bool(cur.rowcount)
 def stats(self):
  with self.con() as c:
   return {"users":c.execute("SELECT count(*) FROM users").fetchone()[0],"paid":c.execute("SELECT count(*) FROM users WHERE plan IN ('PRO','ELITE')").fetchone()[0],"special":c.execute("SELECT count(*) FROM users WHERE plan='SPECIAL'").fetchone()[0],"stars":c.execute("SELECT coalesce(sum(stars),0) FROM payments WHERE status='PAID'").fetchone()[0]}
