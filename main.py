import asyncio
import os
import logging
from cache.redis_client import init_redis
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(os.getenv("APP_NAME", "Algotrading App"))

async def main():
    logger.info("Starting Algotrading App...")

    # Init connections
    await init_redis()
    logger.info("Redis initialized successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Shutting down app.")
