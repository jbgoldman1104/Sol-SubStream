# common
import functools
import json
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import env
import common
import socketio
import asyncio
from benchmark import _b
import threading

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

r = common.connect_redis()


app = FastAPI(title='Solana DexViewer')
app.add_middleware( CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)

# ------------- Socket -------------  
mgr = socketio.AsyncRedisManager(f'redis://{env.REDIS_HOST}:{env.REDIS_PORT}/0')
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", logger=False, engineio_logger=False, client_manager=mgr)
# sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", logger=True, engineio_logger=True)
sio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="socket.io")
app.mount("/socket.io", sio_app)

def enter(sid, new, ns):
    prev = r.hget('H_SR', sid)
    if prev:
        print(f'{sio} leave {prev}')
        sio.leave_room(sid, prev, ns)
        r.zincrby(f'SS_RO{ns}', -1, prev)
        r.hdel('H_SR', sid)
    if new:
        print(f'{sio} enter {new}')
        sio.enter_room(sid, new, ns)
        r.zincrby(f'SS_RO{ns}', 1, new)
        r.hset('H_SR', sid, new)
    
def leave(sid, ns):
    prev = r.hget('H_SR', sid)
    if prev:
        print(f'{sio} leave {prev}')
        sio.leave_room(sid, prev, ns)
        r.zincrby(f'SS_RO{ns}', -1, prev)
        r.hdel('H_SR', sid)
    # if not data: return False

@sio.event(namespace=env.NS_ST)
async def connect(sid, environ):
    print(f'--- Connected ---: {sid} : {environ["REMOTE_ADDR"]}')
    # raise ConnectionRefusedError('authentication failed')

@sio.event(namespace=env.NS_ST)
async def disconnect(sid):
    print(f'--- Disconnected ---: {sid}')
    for ns in env.NSS:
        leave(sid, ns)
            
@sio.event(namespace=env.NS_ST)
async def subscribe(sid, data):
    print(f'--- Subscribe ST ---: {sid} : {data}')
    enter(sid, json.dumps(data), env.NS_ST)
    
@sio.event(namespace=env.NS_ST)
async def unsubscribe(sid, data):
    print(f'--- Unsubscribe ST ---: {sid} : {data}')
    leave(sid, data, env.NS_ST)
    

@sio.event(namespace=env.NS_TX)
async def connect(sid, environ):
    print(f'--- Connected TX ---: {sid} : {environ["REMOTE_ADDR"]}')
    # raise ConnectionRefusedError('authentication failed')

@sio.event(namespace=env.NS_TX)
async def disconnect(sid):
    print(f'--- Disconnected TX ---: {sid}')
    for ns in env.NSS:
        leave(sid, ns)
            
@sio.event(namespace=env.NS_TX)
async def subscribe(sid, data):
    print(f'--- Subscribe TX ---: {sid} : {data}')
    enter(sid, json.dumps(data), env.NS_TX)
    
@sio.event(namespace=env.NS_TX)
async def unsubscribe(sid, data):
    print(f'--- Unsubscribe TX ---: {sid} : {data}')
    leave(sid, data, env.NS_TX)

@sio.event(namespace=env.NS_TX)
async def data(sid, data):
    print(f'--- Data TX ---: {sid} : {data}')
    return query_redis.query_wrap('', data)
    


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
    return query_redis.query_price_historical(pool, t_from, t_to, interval)

app.mount("/", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")



async def query_send(ns, data):
    # mgr.emit('PAIRS_DATA', query_redis.query_wrap(ns, data), room=data, namespace=env.NS_ST)
    sio.emit('PAIRS_DATA', query_redis.query_wrap(ns, data), room=data, namespace=env.NS_ST)

# async def send_data_thread():
#     prev = 0
#     while True:
#         r.ltrim('L_UPDATED', 0, 0)
#         cmd = r.brpop('L_UPDATED')[1].decode()
#         if cmd == 'QUIT': break
#         now = common.now()
#         if now - prev < 3000:
#             asyncio.sleep((prev - now) / 1000)
#         prev = now
#         # mgr.initialize()
#         # data = '{"type":"SUBSCRIBE_RANK","data":{"duration":0,"sort":"score","sort_dir":"desc","skip":0,"limit":50}}'
#         # mgr.emit('message', query_redis.query_wrap('', room), room='123123123', namespace=env.NS_ST)
#         # await sio.emit('PAIRS_DATA', query_redis.query_wrap('', data), room=data, namespace=env.NS_ST)
#         # if not mgr.rooms: continue
#         if not sio.rooms: continue
        
#         tasks = []
#         for ns in env.NSS:
#             rooms = sio.rooms[ns]
#             if rooms:
#                 rooms = rooms.keys()
#                 for room in rooms:
#                     if not room: continue
#                     if not room.startswith("{"):
#                         tasks.append(asyncio.create_task(query_send(ns, room)))
#         _b(f'query_send {len(tasks)}')
#         if not tasks: continue
#         asyncio.gather(tasks)


# def background_worker(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()
# loop = asyncio.new_event_loop()
# threading.Thread(target=background_worker, args=(loop,), daemon=True).start()
# async def async_background_task():
#     while True:
#         print("Background task is running")
#         room = '{"type":"SUBSCRIBE_RANK","data":{"duration":0,"sort":"score","sort_dir":"desc","skip":0,"limit":50}}'
#         await mgr.emit('PAIRS_DATA', query_redis.query_wrap('', room), room=room, namespace=env.NS_ST)
#         await asyncio.sleep(5)
# asyncio.run_coroutine_threadsafe(async_background_task(), loop)


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    # await send_proc