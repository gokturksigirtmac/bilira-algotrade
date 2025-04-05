import asyncio
import os
import logging
from db.redis_client import init_redis
from dotenv import load_dotenv
from services.data_streamer import store_klines_individual_into_redis
from db.mongo import init_mongo, store_klines_individual_into_mongo
from exchanges.exchange_interface import ExchangeInterface
from exchanges.binance import BinanceExchange

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(os.getenv("APP_NAME", "Bilira - Algotrading App"))

exchange = os.getenv("EXCHANGE")
ticker = os.getenv("DEFAULT_TICKER")
interval = os.getenv("DEFAULT_INTERVAL", "1m")
limit = os.getenv("DEFAULT_LIMIT", 1000)

async def main(exchange: ExchangeInterface):
    logger.info(f"Starting {os.getenv('APP_NAME')}...")

    # Init connections
    redis_client = await init_redis()
    logger.info("Redis initialized successfully.")

    mongo_client, db = await init_mongo()
    logger.info("MongoDB initialized successfully.")

    market_data = await exchange.get_market_data(ticker=ticker, interval=interval, limit=limit, timeout=10)

    await store_klines_individual_into_mongo(
        mongo_db=db,
        klines=market_data,
        ticker=ticker,
    )

    await store_klines_individual_into_redis(
        redis_client=redis_client,
        klines=market_data,
        ticker=ticker,
    )

if __name__ == "__main__":
    try:
        # We can handle exchange dynamicaly, for this case we are getting from .env file
        exchange = exchange.lower()
        match exchange:
            case "binance":
                exchange = BinanceExchange()
            case _:
                logger.warning("Shutting down app.")
                raise ValueError(f"Unsupported exchange: {exchange}")
        asyncio.run(main(exchange))

    except KeyboardInterrupt:
        logger.warning("Shutting down app.")