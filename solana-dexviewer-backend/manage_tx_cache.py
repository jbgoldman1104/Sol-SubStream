import env
import common
import datetime
import json
from benchmark import _b

from random import random as rd
from random import randint as rdi
from redis.commands.search.query import Query


def update_cache_thread():
    r = common.connect_redis()
    conn = common.connect_db()
    cur = conn.cursor()
        
    # r.xread( streams={"INIT_COMPLETE": 0}, block = 60000 )
    # r.xtrim("INIT_COMPLETE", maxlen = 0)

    rep = 1
    cached_set = r.smembers('S_C')
    prev_save = common.now()
    while True:
        r.xread( streams = {"UPDATE_RANK": 0}, block = 10000 ) # type: ignore
        r.xtrim("UPDATE_RANK", maxlen = 0)
        now = common.now()
        
        t_start = datetime.datetime.now()
        
        # --- Get New List ---
        cached_set_new = set()
        for i in range(4):
            rank = r.zrevrange(f"SS_PS{i}", 0, env.CACHE_COUNT - 1)
            cached_set_new |= set([t.decode() for t in rank]) # type: ignore
        
        remove_pids = list(cached_set - cached_set_new)
        add_pids = list(cached_set_new - cached_set)
        
        # --- Delete Old TX Keys ---
        cursor = 0
        for pid in remove_pids:
            _b(f'Remove Pair - {pid}')
            # first = True
            # while first or cursor:
            #     first = False
                # rlt = r.scan(cursor = cursor, match = f"TX:{token}:*")
                # cursor = rlt[0] # type: ignore
                # r.delete(*rlt[1]) # type: ignore
            rlt = r.ft('IDX_TX').search(Query(f'@pid:{{{pid}}}'))
            rows = [json.loads(doc['json']) for doc in rlt.docs]
            r.delete(*[f'{tx["id"]}' for tx in rows]) # type: ignore
            cached_set.remove(pid)
            r.srem('S_C', pid)
            _b()

        # --- Add New TX Keys ---
        if add_pids:
            ps = r.json().mget([f'P:{pid}' for pid in add_pids], ".")
            for i in range(len(ps)):
                _b(f'Add Pair - {add_pids[i]}')
                txs = []
                readTxId_last = 0
                # -TODO LOAD CACHE TX FROM PG
                while True:
                    cur.execute("SELECT * FROM trade WHERE id > %s AND \"poolAddress\" = %s", [readTxId_last, ps[i]['poolAddress']])
                    rows = cur.fetchmany(env.DB_READ_SIZE)
                    if len(rows) == 0: break
                    readTxId_last = rows[len(rows)-1][0]    # id
                    txs = [common.toTx(cur, r, row) for row in rows]
                    r.json().mset(txs) # type: ignore
                # for i in range(5):
                #     id = common.rtx()
                #     timestamp = now - rdi(1, 3000) - i//5 * 3000
                #     txs.append(common.toTx(cur, r, (id, pool, common.rp(), rdi(1,5), rd()*100, rd()*100, f'{rdi(1, 0xFFFFFFFFFFFFFFFF):X}', timestamp)))
                cached_set.add(add_pids[i])
                r.sadd('S_C', add_pids[i])
                _b()

        # TODO SAVE ALL INFO TO PG every 1min
        if common.now() - prev_save > 60000:
            prev_save = common.now()
            
        
        print(f"-- Manage Cache ---({rep}): add:{add_pids} remove:{remove_pids} cur:{len(cached_set)} {cached_set} => {(datetime.datetime.now() - t_start).total_seconds()} s")
        rep += 1
        


if __name__ == "__main__":
    rlt = update_cache_thread()


# async def reader(channel: redis.client.PubSub):
#     while True:
#         message = await channel.get_message(ignore_subscribe_messages=True, timeout=None)
#         if message is not None:
#             print(f"(Reader) Message Received: {message}")
#             if message["data"].decode() == STOPWORD:
#                 print("(Reader) STOP")
#                 break

# r = redis.from_url("redis://localhost")
# async with r.pubsub() as pubsub:
#     await pubsub.subscribe("channel:1", "channel:2")

#     future = asyncio.create_task(reader(pubsub))

#     await r.publish("channel:1", "Hello")
#     await r.publish("channel:2", "World")
#     await r.publish("channel:1", STOPWORD)

#     await future