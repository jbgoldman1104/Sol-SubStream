# common
import functools
import json
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import env
import socketio

import query_redis
import query_pg

# fastapi
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    Request,
)
# from pydantic import BaseSettings
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi_socketio import SocketManager

app = FastAPI(title='Solana DexViewer')
app.add_middleware( CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)

# ------------- Socket -------------  
mgr = socketio.AsyncRedisManager(f'redis://{env.REDIS_HOST}:{env.REDIS_PORT}/0')
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", logger=True, engineio_logger=True, client_manager=mgr)
sio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="socket.io")
app.mount("/socket.io", sio_app)


@sio.event(namespace='/socket.io/st')
async def connect(sid, environ):
    print(f'--- Connected ---: {sid} : {environ["REMOTE_ADDR"]}')
    # raise ConnectionRefusedError('authentication failed')

@sio.event(namespace='/socket.io/st')
async def disconnect(sid):
    print(f'--- Disconnected ---: {sid}')



# in {
#     "type": "SUBSCRIBE_PAIRS",
#     "data": {
#         "duration": 0,
#         "skip": 0,
#         "limit": 100,
#         "sort": "score",
#         "sort_dir": "desc",
#     }
# }

    
# {
#     "type": "SUBSCRIBE_TXS",
#     "data": {
#         "queryType": "simple",
#         "pairAddress": "842NwDnKYcfMRWAYqsD3hoTWXKKMi28gVABtmaupFcnS"
#     }
# }

# {
#     "type": "SUBSCRIBE_PRICE",
#     "data": {
#         "queryType": "simple",
#         "chartType": "1m",
#         "address": "7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJnm",
#         "currency": "pair"
#     }
# }

@sio.event(namespace='/socket.io/st')
async def subscribe(sid, data):
    print(f'--- Subscribe ---: {sid} : {data}')
    if not data: return False
    # data = json.loads(data)
    sio.enter_room(sid, data, namespace='/socket.io/st')
    # await mgr.send({"type": "message", "data": "subscribe successfull."}, room=data, namespace='/socket.io/st')
    await mgr.emit('reply_message', {"type":"123", "data": { "data1": 123}}, room=data, namespace='/socket.io/st')
    

@sio.event(namespace='/socket.io/st')
async def unsubscribe(sid, data):
    print(f'--- Unsubscribe ---: {sid} : {data}')
    if not data: return False
    # data = json.loads(data)
    sio.leave_room(sid, data, namespace='/socket.io/st')
    if not data.type: return False


# redis
# import redis

# import env
# r = redis.Redis(host = env.REDIS_HOST, port = env.REDIS_PORT)
# print("Redis Connected" if r.ping() else "Redis Not Connected")


from pathlib import Path
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )

@app.get("/trade/{pool}", response_class=HTMLResponse)
async def read_item(request: Request, pool: str):
    return templates.TemplateResponse(
        request=request, name="trade.html", context={"pool": pool}
    )
    

# ------------- HTTP -------------
@app.get("/api/st/query")
async def read_st(duration: int = 0, skip: int = 0, limit: int = 20, sort = "score", sort_dir = "desc"):
    return query_redis.query_st(duration, skip, limit, sort, sort_dir)

@app.get("/api/st/search")
async def search_st(q: str = "", skip: int = 0, limit: int = 20):
    return query_redis.search_pair(q, skip, limit)
    
@app.get("/api/tx/query")
async def read_tx(pool: str = "", sort: str = "blockTime", direction: str = "desc", skip: int = 0, limit: int  = 20):
    return query_redis.query_tx(pool, sort, direction, skip, limit)

@app.get("/api/tx/chart")
async def read_chart(pool: str = "", t_from: int = 0, t_to: int = 0, interval: int = 0):
    return query_redis.query_chart(pool, t_from, t_to, interval)

app.mount("/", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)