import redis.asyncio as aioredis

from shared_config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB

redis_client: aioredis.Redis = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=False  # store raw bytes
)
