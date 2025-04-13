import os
import asyncio
import logging
import threading

from dotenv import load_dotenv

from db.redis_client import init_redis
from db.mongo import init_mongo, get_mongo_db

from exchanges.exchange_interface import ExchangeInterface
from exchanges.binance import BinanceExchange

from api import ws_orderbook
from api import ws_signal

from fastapi import FastAPI
from redis.asyncio import Redis

load_dotenv()

EXCHANGE_NAME = os.getenv("EXCHANGE_NAME")
TICKER = os.getenv("DEFAULT_TICKER")
INTERVAL = os.getenv("DEFAULT_INTERVAL")
LIMIT = os.getenv("DEFAULT_LIMIT")
EXCHANGE_REALTIME_DATA_URL = os.getenv("EXCHANGE_REALTIME_DATA_URL")
BINANCE_ORDERBOOK_CHANNEL = os.getenv("BINANCE_ORDERBOOK_CHANNEL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
APP_NAME = os.getenv("APP_NAME", "Bilira - Algotrading App")
BINANCE_PRICE_CHANNEL = os.getenv("BINANCE_PRICE_CHANNEL", "binance_price")
BUY_SELL_SIGNAL_CHANNEL = os.getenv("BUY_SELL_SIGNAL_CHANNEL", "buy_sell_signal")
SHORT_TERM_SMA = os.getenv("SHORT_TERM_SMA")
LONG_TERM_SMA = os.getenv("LONG_TERM_SMA")

app = FastAPI()
app.include_router(ws_orderbook.router)
app.include_router(ws_signal.router)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(APP_NAME)

async def main_app(exchange: ExchangeInterface):
    print("✅ ENV:", dict(os.environ))
    # Init connections
    redis_client = await init_redis()
    logger.info("✅ Redis initialized successfully.")

    await init_mongo()
    mongo_client, mongo_db = get_mongo_db()
    logger.info("✅ MongoDB initialized successfully.")

    market_data = await exchange.get_market_data(ticker=TICKER, interval=INTERVAL, limit=int(LIMIT), timeout=10)
    
    exchange.store_klines_individual_into_mongo(
        mongo_db=mongo_db,
        klines=market_data,
        ticker=TICKER,
    )

    loop = asyncio.get_event_loop()

    orderbook_stream_background_tasks_thread = threading.Thread(target=orderbook_stream_background_tasks, 
                                                                name="orderbook_thread", 
                                                                args=(exchange, redis_client, loop))
    orderbook_stream_background_tasks_thread.start()


    price_stream_background_tasks_thread = threading.Thread(target=price_stream_background_tasks,
                                                             name="price_stream_thread", 
                                                             args=(exchange, mongo_db, redis_client, loop))
    price_stream_background_tasks_thread.start()

    print("Current loop:", asyncio.get_event_loop())
    print("Orderbook stream thread started:", orderbook_stream_background_tasks_thread.is_alive())

def orderbook_stream_background_tasks(exchange: ExchangeInterface, redis_client: Redis, loop):
    try:
        print("🚀 Starting async orderbook stream...")
        asyncio.run_coroutine_threadsafe(exchange.start_orderbook_stream(
            redis_client=redis_client,
            exchange_realtime_data_url=EXCHANGE_REALTIME_DATA_URL,
            exchange=EXCHANGE_NAME,
            ticker=TICKER,
            redis_channel=BINANCE_ORDERBOOK_CHANNEL
        ), loop=loop)
    except Exception as e:
        print(f"❌ ERROR in orderbook stream thread: {e}")

def price_stream_background_tasks(exchange: ExchangeInterface, mongo_db, redis_client: Redis, loop):
    try:
        print("🚀 Starting async price stream...")
        asyncio.run_coroutine_threadsafe(
            exchange.price_stream_from_exchange(
                exchange_realtime_data_url=EXCHANGE_REALTIME_DATA_URL,
                exchange_name=EXCHANGE_NAME,
                ticker=TICKER,
                interval=INTERVAL,
                mongo_db=mongo_db,
                redis_client=redis_client
            ), loop=loop
        )
    except Exception as e:
        print(f"❌ ERROR in price stream thread: {e}")

@app.on_event("startup")
async def on_startup():
    logger.info(f"🚀 Starting {APP_NAME}...")

    exchange_name = EXCHANGE_NAME.lower()

    if exchange_name == "binance":
        exchange = BinanceExchange()
    else:
        raise ValueError(f"❌ Unsupported exchange: {exchange_name}")

    await main_app(exchange)
    logger.info(f"✅ {APP_NAME} started successfully.")
