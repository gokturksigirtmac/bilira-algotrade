import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

# Redis config
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = None

async def init_redis():
    global redis_client
    try:
       redis_client = await redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )
    except redis.ConnectionError as e:
        raise Exception(f"Could not connect to Redis: {e}")
    except redis.TimeoutError as e:
        raise Exception(f"Redis connection timed out: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    if redis_client is None:
        raise Exception("Redis client is not initialized properly.")
    return redis_client
