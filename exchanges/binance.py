import os
import json
import asyncio
import requests
import websockets

import pandas as pd

from redis import Redis

from dotenv import load_dotenv

from .exchange_interface import ExchangeInterface

from services.buy_sell_signal import generate_signal, record_crossovers_into_mongodb, record_crossovers_into_redis

load_dotenv()

binance_klines_base_url = os.getenv("BINANCE_KLINES_BASE_URL", "https://api.binance.com")
binance_klines_endpoint = os.getenv("BINANCE_KLINES_ENDPOINT", "/api/v3/klines")
SHORT_TERM_SMA = os.getenv("SHORT_TERM_SMA")
LONG_TERM_SMA = os.getenv("LONG_TERM_SMA")
CROSSOVER_SIGNAL_CHANNEL = os.getenv("BUY_SELL_SIGNAL_CHANNEL", "buy_sell_signal")

"""
 - Here is the BinanceExchange class that implements the ExchangeInterface.
 - It provides methods to fetch market data, store kline data into MongoDB,
and start a WebSocket stream for order book data.
 - Through to strategy pattern we can easily add new exchanges in the future.
 - I was used this pattern because of its flexibility and extensibility.
 - I was used only exchange of Binance for the case.
"""
class BinanceExchange(ExchangeInterface):
    def __init__(self):
        self=self

    async def get_market_data(self, ticker: str, interval: str, limit: int, timeout=10):
        url = f"{binance_klines_base_url}{binance_klines_endpoint}"

        params = {
            "symbol": str(ticker).upper(),
            "interval": str(interval),
            "limit": limit
        }

        print(f"📡 Fetching market data from Binance: {url} | Params: {params}")

        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as http_err:
            raise Exception(f"❌ [HTTP Error] Status code: {response.status_code} | Message: {response.text}") from http_err
        
        except requests.exceptions.RequestException as req_err:
            raise Exception(f"❌ [Request Error] Unable to fetch data from Binance: {req_err}") from req_err

    def store_klines_individual_into_mongo(self, mongo_db, klines, ticker):
        for kline in klines:
            timestamp = kline[0]
            value = json.dumps(kline)
            try:
                mongo_db.klines.insert_one({
                    "ticker": ticker,
                    "timestamp": timestamp,
                    "kline": value
                })

            except Exception as e:
                print(f"❌ Error storing kline for {ticker} at {timestamp}: {e}")
                continue

    async def start_orderbook_stream(self, redis_client, exchange_realtime_data_url, exchange, ticker, redis_channel):
        url = f"{exchange_realtime_data_url}/{ticker.lower()}@depth"
        print(f"🛰 Connecting to Binance WS URL: {url}")

        while True:
            try:
                print(f"🔌 Connecting to Binance WebSocket: {url}")
                async with websockets.connect(url, ping_interval=20, ping_timeout=10, max_queue=None) as websocket:
                    print("✅ Connected to Binance WebSocket")

                    async for message in websocket:

                        data = json.loads(message)
                        
                        payload = {
                            "exchange": exchange,
                            "symbol": ticker.upper(),
                            "event_time": data.get("E"),
                            "bids": data.get("b"),
                            "asks": data.get("a")
                        }

                        await redis_client.publish(redis_channel, json.dumps(payload))

            except Exception as e:
                print(f"❌ Error in stream loop: {e}")
                print("🔁 Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def price_stream_from_exchange(self, exchange_realtime_data_url: str, exchange_name: str, ticker: str, interval: str = "1m", mongo_db=None, redis_client:Redis=None):
        exchange_url = f"{exchange_realtime_data_url}/{ticker.lower()}@kline_{interval}"
        while True:
            try:
                print(f"Connecting to {exchange_name} WS: {exchange_url}")
                async with websockets.connect(exchange_url, ping_interval=20, ping_timeout=10, max_queue=None) as ws:
                    print(f"📡 Connected to {exchange_url}")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        k = data['k']

                        if k["x"]:  # Only store when candle is closed
                            document = {
                                "ticker": k["s"],
                                "timestamp": k["t"],
                                "kline": json.dumps([
                                    k["t"], k["o"], k["h"], k["l"], k["c"], k["v"], k["T"]
                                ])
                            }
                            print(f"📊 Kline data: {document}")
                            
                            mongo_db.klines.insert_one(document)

                            await self.process_klines(mongo_db=mongo_db, redis_client=redis_client)
                            print(f"📈 Kline data stored in MongoDB: {document}")

            except Exception as e:
                print(f"Error: {e}")
                print("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def process_klines(self, mongo_db, redis_client):
        cursor = mongo_db.klines.find().sort("timestamp", -1).limit(int(LONG_TERM_SMA))
        klines = await cursor.to_list(length=int(LONG_TERM_SMA))

        closing_prices = [float(json.loads(doc["kline"])[4]) for doc in klines]
        df = pd.DataFrame(closing_prices, columns=['close'])
        print(f"📊 Closing prices: {df['close'].tail()}")
        crossovers = generate_signal(df, int(SHORT_TERM_SMA), int(LONG_TERM_SMA))
        print(f"📈 Generated crossovers: {crossovers}")
        await record_crossovers_into_mongodb(crossovers, mongo_db)
        await record_crossovers_into_redis(redis_client, CROSSOVER_SIGNAL_CHANNEL, crossovers)
        print("🚀 Kline data stored in MongoDB and signal generated.")