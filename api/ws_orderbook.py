import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import os
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

router = APIRouter()

CHANNEL_NAME = os.getenv("BINANCE_ORDERBOOK_CHANNEL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

@router.websocket("/ws/orderbook")
async def websocket_endpoint(websocket: WebSocket):
    try:
        print("✅ Accepting WebSocket...")
        await websocket.accept()

        print("🔌 Connecting to Redis...")
        redis = Redis.from_url(REDIS_URL, decode_responses=True)

        pubsub = redis.pubsub()
        print(f"📡 Subscribing to channel: {CHANNEL_NAME}")
        await pubsub.subscribe(CHANNEL_NAME)

        print("👂 Waiting for messages...")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                print(f"📨 Message from Redis: {message['data']}")
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("❗️Client disconnected")
    except Exception as e:
        print(f"❌ ERROR in websocket handler: {e}")
        await websocket.close()
    finally:
        await pubsub.unsubscribe(CHANNEL_NAME)
        await redis.close()
        print("🔌 Redis connection closed")
