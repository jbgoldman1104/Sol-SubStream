import env
import common
import datetime

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
    cached_set = set()
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
        
        remove_list = list(cached_set - cached_set_new)
        add_list = list(cached_set_new - cached_set)
        
        # --- Delete Old TX Keys ---
        cursor = 0
        for token in remove_list:
            # first = True
            # while first or cursor:
            #     first = False
                # rlt = r.scan(cursor = cursor, match = f"TX:{token}:*")
                # cursor = rlt[0] # type: ignore
                # r.delete(*rlt[1]) # type: ignore
            rlt = r.ft('IDX_TX').search(Query(f'@signer:{{{token}}}'))
            r.delete(*[f'{tx["id"]}' for tx in rlt.docs]) # type: ignore
            cached_set.remove(token)

        # --- Add New TX Keys ---
        for token in add_list:
            txs = []
            # TODO LOAD CACHE TX FROM PG
            for i in range(5):
                id = common.rtx()
                timestamp = now - rdi(1, 3000) - i//5 * 3000
                txs.append(common.toTx(cur, r, (id, token, common.rp(), rdi(1,5), rd()*100, rd()*100, f'{rdi(1, 0xFFFFFFFFFFFFFFFF):X}', timestamp)))
            r.json().mset(txs) # type: ignore
            cached_set.add(token)
        
        
        # TODO SAVE ALL INFO TO PG every 1min
        if common.now() - prev_save > 60000:
            prev_save = common.now()
        
        print(f"-- Manage Cache ---({rep}): add:{add_list} remove:{remove_list} cur:{len(cached_set)} {cached_set} => {(datetime.datetime.now() - t_start).total_seconds()} s")
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