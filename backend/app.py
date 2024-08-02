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

async def enter(sid, param, ns):
    if not param: return
    room = param if type(param) == str else json.dumps(param)
    if param["type"] == "SUBSCRIBE_PAIRS":
        await leave(sid, None, ns)
    # elif param["type"] == "SUBSCRIBE_TXS":
    #     leave(sid, )
    k = f'S_SR{sid}'
    # if r.sismember(k, room): return
    if room in mgr.get_rooms(sid, ns): return
    r.sadd(k, sid)
    await sio.enter_room(sid, room, ns)
    r.zincrby(f'SS_RO{ns}', 1, room)
    print(f'-- {sio} enter {ns} : {room} --')
        
async def leave(sid, param, ns):
    k = f'S_SR{sid}'
    if not param:
        for prev_room in r.smembers(k):
            await sio.leave_room(sid, prev_room, ns)
            r.zincrby(f'SS_RO{ns}', -1, prev_room)
            print(f'-- {sio} leave {ns} : {prev_room} --')
    else:
        room = param if type(param) == str else json.dumps(param)
        # if r.sismember(k, room):
        await sio.leave_room(sid, room, ns)
        r.zincrby(f'SS_RO{ns}', -1, room)
        print(f'-- {sio} leave {ns} : {room} --')


@sio.event(namespace=env.NS_ST)
async def connect(sid, environ):
    print(f'--- Connected ST ---: {sid} : {environ["REMOTE_ADDR"]}')
    # raise ConnectionRefusedError('authentication failed')

@sio.event(namespace=env.NS_ST)
async def disconnect(sid):
    print(f'--- Disconnected ST ---: {sid}')
    # for ns in env.NSS:
    #     leave(sid, None, ns)
    for room in mgr.get_rooms(sid, env.NS_ST):
        await leave(sid, room, env.NS_ST)
            
@sio.event(namespace=env.NS_ST)
async def subscribe(sid, data):
    print(f'--- Subscribe ST ---: {sid} : {data}')
    # leave(sid, None, env.NS_ST)
    for room in mgr.get_rooms(sid, env.NS_ST):
        if room != None and room.startswith("{"):
            await leave(sid, room, env.NS_ST)
    await enter(sid, data, env.NS_ST)
    js = common.js(data)
    if not js or not js['data']: return {}
    return query_redis.query_wrap('', js)
    
@sio.event(namespace=env.NS_ST)
async def unsubscribe(sid, data):
    print(f'--- Unsubscribe ST ---: {sid} : {data}')
    await leave(sid, data, env.NS_ST)
    
@sio.event(namespace=env.NS_ST)
async def data(sid, data):
    print(f'--- Data ST ---: {sid} : {data}')
    js = common.js(data)
    if not js or not js['data']: return {}
    return query_redis.query_wrap('', js)

@sio.event(namespace=env.NS_TX)
async def connect(sid, environ):
    print(f'--- Connected TX ---: {sid} : {environ["REMOTE_ADDR"]}')
    # raise ConnectionRefusedError('authentication failed')

@sio.event(namespace=env.NS_TX)
async def disconnect(sid):
    print(f'--- Disconnected TX ---: {sid}')
    for ns in env.NSS:
        await leave(sid, None, ns)
            
@sio.event(namespace=env.NS_TX)
async def subscribe(sid, data):
    print(f'--- Subscribe TX ---: {sid} : {data}')
    await enter(sid, data, env.NS_TX)
    js = common.js(data)
    if not js or not js['data']: return {}
    return query_redis.query_wrap('', js)
    
@sio.event(namespace=env.NS_TX)
async def unsubscribe(sid, data):
    print(f'--- Unsubscribe TX ---: {sid} : {data}')
    await leave(sid, data, env.NS_TX)

@sio.event(namespace=env.NS_TX)
async def data(sid, data):
    print(f'--- Data TX ---: {sid} : {data}')
    js = common.js(data)
    if not js or not js['data']: return {}
    return query_redis.query_wrap('', js)
    


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
async def read_tx(address: str = "", sort: str = "blockTime", direction: str = "desc", skip: int = 0, limit: int  = 20):
    return query_redis.query_tx_historical(address, sort, direction, skip, limit)

@app.get("/api/tx/chart")
async def read_chart(address: str = "", address_type="pair", type="15m", time_from: int = 0, time_to: int = 0, interval: int = 0):
    return query_redis.query_price_historical(address, address_type, type, time_from, time_to)

@app.get("/api/tx/holders")
async def read_holders(address: str = "", address_type="pair", skip: int = 0, limit: int = 10):
    return query_redis.query_holders(address, address_type, skip, limit)


app.mount("/", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    print('app process started.')
