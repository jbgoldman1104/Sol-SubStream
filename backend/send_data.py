import env
import common
import asyncio
import json
import socketio

import query_redis
from benchmark import _b

r = common.connect_redis()

mgr = socketio.AsyncRedisManager(f'redis://{env.REDIS_HOST}:{env.REDIS_PORT}/0', write_only=False)

async def query_send(ns, data):
    # mgr.send(query_redis.query_wrap(ns, data), room=data, namespace=env.NS_ST)
    # room = '{"type":"SUBSCRIBE_RANK","data":{"duration":0,"sort":"score","sort_dir":"desc","skip":0,"limit":50}}'
    await mgr.emit('message', query_redis.query_wrap('', data), room=data, namespace=ns)

    
async def send_data_thread():
    prev = 0
    while True:
        r.ltrim('L_UPDATED', 0, 0)
        cmd = r.brpop('L_UPDATED', timeout=env.UPDATE_INTERVAL)[1].decode() # TODO timeout
        if cmd == 'QUIT': break
        now = common.now()
        print(f'send: {now - prev}: {(env.UPDATE_INTERVAL + prev - now)}')
        if now - prev < env.UPDATE_INTERVAL:
            await asyncio.sleep((env.UPDATE_INTERVAL + prev - now) / 1000)
        prev = common.now()
        # await asyncio.create_task(query_send('ns', 'room'))
        # continue
        # room = '{"type":"SUBSCRIBE_PAIRS","data":{"duration":0,"sort":"score","sort_dir":"desc","skip":0,"limit":50}}'
        # mgr.emit('message', query_redis.query_wrap('', room), room='123123123', namespace=env.NS_ST)
        # rooms1 = mgr.get_rooms('*', env.NS_ST)
        # if not mgr.rooms: continue
        
        tasks = []
        for ns in env.NSS:
        #     rooms = mgr.rooms[ns]
        #     if rooms:
        #         rooms = rooms.keys()
        #         for room in rooms:
        #             if not room: continue
        #             if not room.startswith("{"):
                        # tasks.append(asyncio.create_task(query_send(ns, room)))

            rs = r.zrevrange(f'SS_RO{ns}', 0, -1, withscores=True)
            print(rs)
            rooms = set()

            for room in rs:
                if room and room[1] and room[1] > 0:
                    rooms.add(room[0].decode())
            for room in rooms:
                tasks.append(asyncio.create_task(query_send(ns, room)))

        _b(f'query_send {len(tasks)}')
        if not tasks: continue
        asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(send_data_thread())
    # await asyncio.create_task()
    # print(get_nft('123', "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1"))


