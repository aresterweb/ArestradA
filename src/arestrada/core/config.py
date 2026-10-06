from dataclasses import dataclass
import os

def b(name,default=False): return os.getenv(name,str(default)).lower() in ("1","true","yes","on")
@dataclass(frozen=True)
class Settings:
    symbol:str=os.getenv("SYMBOL","XAU/USD")
    api_key:str=os.getenv("TWELVEDATA_API_KEY","")
    bot_token:str=os.getenv("TELEGRAM_BOT_TOKEN","")
    owner_id:int=int(os.getenv("TELEGRAM_OWNER_ID","0") or 0)
    db_path:str=os.getenv("DATABASE_PATH","data/arestrada_v4.db")
    timezone:str=os.getenv("DISPLAY_TIMEZONE","Asia/Jakarta")
    news_status:str=os.getenv("NEWS_STATUS","UNKNOWN").upper()
    payment_enabled:bool=b("PAYMENT_ENABLED")
    pro_stars:int=int(os.getenv("PRO_STARS","250"))
    elite_stars:int=int(os.getenv("ELITE_STARS","500"))
    auto_alert:bool=b("AUTO_ALERT_ENABLED")
    news_fail_closed:bool=b("NEWS_FAIL_CLOSED",True)
    cache_seconds:int=int(os.getenv("CACHE_SECONDS","45"))
    api_timeout:int=int(os.getenv("API_TIMEOUT","12"))
    next_min_score:int=int(os.getenv("NEXT_CANDLE_MIN_SCORE","62"))
    trade_min_score:int=int(os.getenv("TRADE_MIN_SCORE","72"))
