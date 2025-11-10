import redis.asyncio as aioredis
from src.config import settings

redis_client: aioredis.Redis = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=False  # store raw bytes
)