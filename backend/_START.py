
import env
import manage_tx_cache
import query_pg
import query_redis
import input_pg
import input_redis
import init
import asyncio


async def start():
    initThread = asyncio.create_task(init.init_redis())
    inputRedisThread = asyncio.create_task(input_redis.update_thread())
    # manageCacheThread = asyncio.create_task(manage_tx_cache.update_cache_thread())
    await initThread
    await inputRedisThread
    # await manageCacheThread
    
    
if __name__ == "__main__":
    asyncio.run(start())