# common
import functools
import json
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import query_redis
import query_pg

# fastapi
from fastapi import (
    BackgroundTasks,
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,
    WebSocketDisconnect,
    status,
    Request,
)
# from pydantic import BaseSettings
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

app = FastAPI(title='Solana DexViewer')
from pathlib import Path
BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR/'static'))), name="static")
templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))
app.add_middleware( CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)

# redis
# import redis

# import env
# r = redis.Redis(host = env.REDIS_HOST, port = env.REDIS_PORT)
# print("Redis Connected" if r.ping() else "Redis Not Connected")

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
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


# ------------- Socket -------------
class Connection:
    def __init__(self):
        pass
    
class ConnectionManager:
    def __init__(self):
        self.conns: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.conns.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.conns.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.conns:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            # await manager.broadcast(f"Client #{client_id} left the chat")


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)