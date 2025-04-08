import os
import json
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# MongoDB config from .env
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB_NAME = os.getenv("MONGO_DB", "algotrading")

mongo_client = None
db = None

async def init_mongo():
    global mongo_client, db
    mongo_client = AsyncIOMotorClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
    """
       - Drop the database to ensure fresh, clean, consistent and reliable data because
       may we are not know stored data, also, we can get easily reliable data from exchange
       for each restart.
       - If we are ensure all of them, we can remove this part. Of course there is various 
       ways to do this, but i choosed this way for the case. It can modify according to 
       business logic.
    """
    await mongo_client.drop_database(MONGO_DB_NAME)
    print(f"[MongoDB] Dropped database: {MONGO_DB_NAME}")
    
    # Assign and return the database
    db = mongo_client[MONGO_DB_NAME]
    print(f"[MongoDB] Connected to database: {MONGO_DB_NAME}")
    print("[MongoDB] Connected successfully!")
    return mongo_client, db
