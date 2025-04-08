import os
import json
import asyncio
import requests
import websockets

from dotenv import load_dotenv

from .exchange_interface import ExchangeInterface

from redis.asyncio import Redis

load_dotenv()

binance_klines_base_url = os.getenv("BINANCE_KLINES_BASE_URL", "https://api.binance.com")
binance_klines_endpoint = os.getenv("BINANCE_KLINES_ENDPOINT", "/api/v3/klines")
class BinanceExchange(ExchangeInterface):
    def __init__(self):
        self=self

    async def get_market_data(self, ticker: str, interval: str, limit: int, timeout=10):
        url = f"{binance_klines_base_url}{binance_klines_endpoint}"

        params = {
            "symbol": ticker,
            "interval": interval,
            "limit": limit
        }

        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as http_err:
            raise Exception(f"[HTTP Error] Status code: {response.status_code} | Message: {response.text}") from http_err
        
        except requests.exceptions.RequestException as req_err:
            raise Exception(f"[Request Error] Unable to fetch data from Binance: {req_err}") from req_err

    async def store_klines_individual_into_mongo(self, mongo_db, klines, ticker):
        for kline in klines:
            timestamp = kline[0]
            value = json.dumps(kline)
            try:
                await mongo_db.klines.insert_one({
                    "ticker": ticker,
                    "timestamp": timestamp,
                    "kline": value
                })
                print(f"Stored kline for {ticker} at {timestamp}")
            except Exception as e:
                print(f"Error storing kline for {ticker} at {timestamp}: {e}")
                continue

    async def start_orderbook_stream(self, redis_client, exchange_realtime_data_url, exchange, ticker, redis_channel):
        url = f"{exchange_realtime_data_url}/{ticker.lower()}@depth"
        print(f"🛰 Connecting to Binance WS URL: {url}")

        while True:
            try:
                print(f"🔌 Connecting to Binance WebSocket: {url}")
                async with websockets.connect(url) as websocket:
                    print("✅ Connected to Binance WebSocket")

                    async for message in websocket:
                        print("📨 Received message from Binance")
                        data = json.loads(message)
                        
                        payload = {
                            "exchange": exchange,
                            "symbol": ticker.upper(),
                            "event_time": data.get("E"),
                            "bids": data.get("b"),
                            "asks": data.get("a")
                        }

                        print(f"📤 Publishing to Redis: {redis_channel} -> {payload}")
                        await redis_client.publish(redis_channel, json.dumps(payload))

            except Exception as e:
                print(f"❌ Error in stream loop: {e}")
                print("🔁 Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
    