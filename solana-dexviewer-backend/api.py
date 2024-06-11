# common
import functools
import json
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
# from typing import Dict
# from typing import Iterable
# from typing import List
# from typing import Tuple
# from typing import Union
import query_redis
import query_pg
from homepage import html_content

# fastapi
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import FastAPI
# from pydantic import BaseSettings
from fastapi.responses import HTMLResponse

app = FastAPI(title='Solana DexViewer')

# redis
# import redis

# import env
# r = redis.Redis(host = env.REDIS_HOST, port = env.REDIS_PORT)
# print("Redis Connected" if r.ping() else "Redis Not Connected")

@app.get("/", response_class=HTMLResponse)
async def homepage():
    return HTMLResponse(content = html_content)

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

@app.get("/st/query")
async def read_st(duration: int = 0, sort = "score", skip: int = 0, limit: int = 10):
    return query_redis.query_st(duration, sort, skip, limit)

@app.get("/tx/query")
def read_tx(pair: str = "", sort: str = "blockTime", direction: str = "desc", skip: int = 0, limit: int  = 10):
    return query_redis.query_tx(pair, sort, direction, skip, limit)


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8009)