import os
import asyncio
import json
import websockets
from dotenv import load_dotenv

load_dotenv()

REDIS_CHANNEL = os.getenv("REDIS_CHANNEL_REALTIME_EXCHANGE_DATA")

async def start_price_stream(url: str, exchange: str, ticker: str, redis_client, interval="1m"):
    exchange_url = f"wss://stream.binance.com:9443/ws/{ticker.lower()}@trade"
    while True:
        try:
            print(f"Connecting to Binance WS: {BINANCE_WS_URL}")
            async with websockets.connect(BINANCE_WS_URL) as websocket:
                print("Connected to Binance WebSocket.")

                async for message in websocket:
                    data = json.loads(message)
                    price = data.get("p")  # price is a string

                    if price:
                        payload = json.dumps({
                            "symbol": ticker.upper(),
                            "price": float(price),
                            "timestamp": data.get("T")
                        })

                        # Publish to Redis channel
                        await publish(REDIS_CHANNEL, payload)
        except Exception as e:
            print(f"Error: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
    
async def store_klines_individual(redis_client, klines, symbol):
    for kline in klines:
        timestamp = kline[0]
        key = f"klines:{symbol}:{timestamp}"
        value = json.dumps(kline)
        try:
            await redis_client.set(key, value)
            print(f"Stored kline for {symbol} at {timestamp}")
        except Exception as e:
            print(f"Error storing kline for {symbol} at {timestamp}: {e}")
            continue
