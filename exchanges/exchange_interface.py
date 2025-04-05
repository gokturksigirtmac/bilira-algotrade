# interfaces/exchange_interface.py
from abc import ABC, abstractmethod

class ExchangeInterface(ABC):
    @abstractmethod
    async def get_market_data(self, ticker: str, interval: str, limit: int):
        pass