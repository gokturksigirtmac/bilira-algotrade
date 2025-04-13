# interfaces/exchange_interface.py
from abc import ABC, abstractmethod

class ExchangeInterface(ABC):
    @abstractmethod
    async def get_market_data(self, ticker: str, interval: str, limit: int, timeout=10):
        pass

    @abstractmethod
    async def store_klines_individual_into_mongo(self, mongo_db, klines, ticker):
        pass

    @abstractmethod
    async def start_orderbook_stream(self, redis_client, exchange_realtime_data_url, exchange, ticker, redis_channel):
        pass

    @abstractmethod
    async def price_stream_from_exchange(self, exchange_realtime_data_url, exchange_name, ticker, interval, mongo_db):
        pass