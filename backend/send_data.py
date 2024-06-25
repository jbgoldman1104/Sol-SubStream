import env
import common
import asyncio
import json
import socketio

import query_redis
from benchmark import _b

mgr = socketio.AsyncRedisManager(f'redis://{env.REDIS_HOST}:{env.REDIS_PORT}/0', write_only=True)

async def query_send(ns, data):
    js = common.js(data)
    if not js or not js['data']: return {}

    if js['type'] == 'SUBSCRIBE_PRICE':
        await mgr.emit('PRICE_DATA', query_redis.query_wrap('', js), room=data, namespace=ns)
    elif js['type'] != 'TXS_DATA_REALTIME':
        await mgr.emit('message', query_redis.query_wrap('', js), room=data, namespace=ns)

    
async def send_data_thread():
    print('-- send_data process started. --')
    r = common.connect_redis()
    while True:
        prev = common.now()
        r.ltrim('L_UPDATED', 0, 0)
        cmd = r.brpop('L_UPDATED', timeout=0)[1].decode() # TODO timeout
        if cmd == 'QUIT': break
        
        # new_txs = r.xread( streams = {"NEW_TXS": 0}, block = 10000000 )
        
        tasks = []
        for ns in env.NSS:
            rs = r.zrevrange(f'SS_RO{ns}', 0, -1, withscores=True)
            # print(rs)
            rooms = set()
            for room in rs:
                if room and room[1] and room[1] > 0:
                    rooms.add(room[0].decode())
            for room in rooms:
                tasks.append(asyncio.create_task(query_send(ns, room)))

        _b(f'query_send {len(tasks)}')
        if not tasks: continue
        await asyncio.gather(*tasks)

        now = common.now()
        print(f'send: {now - prev}: {(env.UPDATE_INTERVAL + prev - now)}')
        if now - prev < env.UPDATE_INTERVAL:
            await asyncio.sleep((env.UPDATE_INTERVAL + prev - now) / 1000)

if __name__ == "__main__":
    asyncio.run(send_data_thread())
    # i = 0
    # while True:
    #     # asyncio.sleep(1000)
    #     print(f"Running{i}")
    #     i += 1
    # print(get_nft('123', "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1"))


