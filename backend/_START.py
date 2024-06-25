
import env
import manage_tx_cache
import query_pg
import query_redis
import input_pg
import asyncio

import subprocess

import delete_all
import init

from pathlib import Path
BASE_DIR = Path(__file__).parent
PROJ_DIR = BASE_DIR.parent

async def start():
    delete_all.delete_all()
    init.init_redis()

    # inputRedisThread = asyncio.create_task(input_redis.update_thread())
    # # manageCacheThread = asyncio.create_task(manage_tx_cache.update_cache_thread())
    # await initThread
    # await inputRedisThread
    # await manageCacheThread
    processes = []
    for script in [
        str(Path(BASE_DIR, 'input_redis.py')), 
        str(Path(BASE_DIR, 'token_info.py')), 
        str(Path(BASE_DIR, 'send_data.py')), 
        str(Path(BASE_DIR, 'app.py')),
        ]:
        process = subprocess.Popen(["python3", script])
        processes.append(process)
    
    # processes.append(subprocess.Popen(["cd", str(Path(PROJ_DIR, 'substreams-sink-service'))]))
    
    # Wait for all processes to complete
    for process in processes:
        process.wait()
    
if __name__ == "__main__":
    asyncio.run(start())