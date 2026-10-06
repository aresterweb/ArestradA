from dataclasses import dataclass
@dataclass(frozen=True)
class NewsGuard: status:str; blocked:bool; reason:str
def evaluate(status:str,fail_closed=True):
 s=(status or "UNKNOWN").upper()
 if s=="BLOCKED":return NewsGuard(s,True,"HIGH_IMPACT_NEWS_WINDOW")
 if s=="UNKNOWN" and fail_closed:return NewsGuard(s,True,"NEWS_STATUS_UNVERIFIED")
 return NewsGuard(s,False,"OK" if s=="CLEAR" else "CAUTION")
