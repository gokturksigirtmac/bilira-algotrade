import os
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

CHANNEL_NAME = os.getenv("BUY_SELL_SIGNAL_CHANNEL", "buy_sell_signal")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

@router.websocket("/ws/signal")
async def websocket_endpoint(websocket: WebSocket):
    try:
        print("✅ Accepting WebSocket...")
        await websocket.accept()

        print("🔌 Connecting to Redis...")
        redis = Redis.from_url(REDIS_URL, decode_responses=True)

        pubsub = redis.pubsub()
        print(f"📡 Subscribing to channel: {CHANNEL_NAME}")
        await pubsub.subscribe(CHANNEL_NAME)

        print(f"👂 Waiting for messages from {CHANNEL_NAME}...")
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