from abc import ABC, abstractmethod
class MarketDataProvider(ABC):
 @abstractmethod
 def candles(self,symbol,interval,outputsize=200): ...
