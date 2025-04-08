import os
import asyncio
import logging
import threading

from dotenv import load_dotenv

from db.redis_client import init_redis
from db.mongo import init_mongo

from services.data_streamer import store_klines_individual_into_redis

from exchanges.exchange_interface import ExchangeInterface
from exchanges.binance import BinanceExchange

from api import ws_orderbook

from fastapi import FastAPI
from redis.asyncio import Redis

load_dotenv()

EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "binance")
TICKER = os.getenv("DEFAULT_TICKER")
INTERVAL = os.getenv("DEFAULT_INTERVAL", "1m")
LIMIT = os.getenv("DEFAULT_LIMIT", 1000)
EXCHANGE_REALTIME_DATA_URL = os.getenv("EXCANGE_REALTIME_DATA_URL")
BINANCE_ORDERBOOK_CHANNEL = os.getenv("BINANCE_ORDERBOOK_CHANNEL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
APP_NAME = os.getenv("APP_NAME", "Bilira - Algotrading App")

app = FastAPI()
app.include_router(ws_orderbook.router)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(APP_NAME)

async def main_app(exchange: ExchangeInterface):
    # Init connections
    redis_client = await init_redis()
    logger.info("Redis initialized successfully.")

    mongo_client, db = await init_mongo()
    logger.info("MongoDB initialized successfully.")

    orderbook_stream_background_tasks_thread = threading.Thread(target=orderbook_stream_background_tasks, 
                                                                name="orderbook_thread", 
                                                                args=(exchange, redis_client))
    orderbook_stream_background_tasks_thread.start()
    print("Orderbook publisher thread started:", orderbook_stream_background_tasks_thread.is_alive())

    market_data = await exchange.get_market_data(ticker=TICKER, interval=INTERVAL, limit=LIMIT, timeout=10)

    await exchange.store_klines_individual_into_mongo(
        mongo_db=db,
        klines=market_data,
        ticker=TICKER,
    )

    await store_klines_individual_into_redis(
        redis_client=redis_client,
        klines=market_data,
        ticker=TICKER,
    )

def orderbook_stream_background_tasks(exchange: ExchangeInterface, redis_client: Redis):
    try:
        print("🚀 Starting async orderbook stream...")
        print("✅ Inside start_orderbook_stream — Binance WS connection will begin")
        asyncio.run(exchange.start_orderbook_stream(
            redis_client=redis_client,
            exchange_realtime_data_url=EXCHANGE_REALTIME_DATA_URL,
            exchange=EXCHANGE_NAME,
            ticker=TICKER,
            redis_channel=BINANCE_ORDERBOOK_CHANNEL
        ))
    except Exception as e:
        print(f"❌ ERROR in orderbook stream thread: {e}")

@app.on_event("startup")
async def on_startup():
    logger.info(f"🚀 Starting {APP_NAME}...")

    exchange_name = EXCHANGE_NAME.lower()

    if exchange_name == "binance":
        exchange = BinanceExchange()
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}")

    await main_app(exchange)
    logger.info(f"✅ {APP_NAME} started successfully.")
