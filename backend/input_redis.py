from typing import ParamSpecArgs
import env
import common
import asyncio
import socketio
import datetime
import time
from redis.commands.search.query import Query
import json
from redis.commands.json.path import Path

from random import random as rd
from random import randint as rdi
import query_redis
mgr = socketio.AsyncRedisManager(f'redis://{env.REDIS_HOST}:{env.REDIS_PORT}/0', write_only=True)

# class Block:
    # pass
async def query_send(ns, data, payload):
    print(f'input_redis: query_send : {data}')
    js = common.js(data)
    if not js or not js['data']: return {}

    if js['type'] == 'TXS_DATA_REALTIME':
        rlt = query_redis.query_wrap('', js, payload)
        if rlt and rlt['data']:
            await mgr.emit('TX_DATA', rlt, room=data, namespace=ns)
        
async def update_thread():
        print('-- input_redis process started. --')
    
    # try:
        r = common.connect_redis()
        conn = common.connect_db()
        cur = conn.cursor()

        # --- SYNC WITH INIT ---
        # r.xread( streams = {"INIT_COMPLETE": 0}, block = 60000 )
        # r.xtrim("INIT_COMPLETE", maxlen = 0)
        
        # # for Sync with R & PG purpose
        # rlt = r.hmget()
        # rlt = r.zrange('SS_PS0', 0, -1)
        # token_ids = set([t.decode() for t in rlt]) # type: ignore
        
        solPrice = 160
        rep = 1
        
        while True:
            time.sleep(0.01)
            
            t_start = datetime.datetime.now()

            now = common.now()
            prev_time = r.zrevrange('SS_BLK', 0, 0, withscores=True)
            prev = now if not prev_time else int(prev_time[0][1]) # type: ignore
            # delta = now - prev

            # cache_set = r.smembers('S_C')
            # --- add new block and txs --- Checked
            new_txs = []
            blk_value = ''
            if env.USE_PG:
                # - import TX table from PG -
                t_start1 = datetime.datetime.now()
                read_tx_id = common.getSyncValue(cur, "read_tx_id", 0)
                cur.execute("SELECT * FROM trade WHERE id > %s", [read_tx_id])
                rows = cur.fetchmany(env.DB_READ_SIZE)
                t_end1 = datetime.datetime.now()
                
                new_txs = [common.toTx(cur, r, row) for row in rows]
                if len(new_txs) == 0: continue
                # r.json().mset(new_txs) # type: ignore
                read_tx_id = new_txs[len(new_txs)-1][2]["id"]
                
                t_start_ = datetime.datetime.now()
                common.setSyncValue(cur, "read_tx_id", read_tx_id)
                t_end_ = datetime.datetime.now()
                t_end1 += t_end_ - t_start_
            
            # --- Block's TX ids --- Checked
            # assert len(new_txs) > 0
            for tx in new_txs:
                if tx[2]['instructionType'] != "Liquidity":
                    if common.isUSD(tx[2]['quoteMint']) and common.isSOL(tx[2]['baseMint']) and tx[2]['baseAmount'] != 0 and tx[2]['quoteAmount'] != 0 and tx[2]['poolAddress'] == 'B6LL9aCWVuo1tTcJoYvCTDqYrq1vjMfci8uHxsm4UxTR':
                        solPrice = abs(tx[2]['quoteAmount'] / tx[2]['baseAmount']) * (1 if common.isUSDT(tx[2]['quoteMint']) else 0.999632)
                    tx[2]["price"] = common.getPrice(solPrice, tx[2]["baseAmount"], tx[2]['quoteAmount'], tx[2]['baseMint'], tx[2]['quoteMint'])
                    blk_value += f'{tx[2]["id"]}' if not blk_value else f',{tx[2]["id"]}'

            # TODO lifetime, Only Hot Tx
            # TODO Sync with PG
            if new_txs:
                r.json().mset(new_txs) # type: ignore
            r.zadd('SS_BLK', {blk_value: now})

            # --- Filter Swap Transactions ---
            new_txs_sel = []
            for tx in new_txs:
                # if r.sismember('S_C', common.poolToId(cur, r, tx[2]['poolAddress'], f'{tx[2]["baseMint"]}/{tx[2]["quoteMint"]}')):
                if tx[2]['instructionType'] != 'Liquidity':
                    new_txs_sel.append(tx)

            # --- TS_i ---
            r.ts().madd([(f'TS_P:{tx[2]["pid"]}', tx[2]['blockTime'], tx[2]['price']) for tx in new_txs_sel])
            r.ts().madd([(f'TS_V:{tx[2]["pid"]}', tx[2]['blockTime'], abs(tx[2]['baseAmount']) * tx[2]['price']) for tx in new_txs_sel])

            # --- Recent and Old Read Count ---
            new_r_pids = r.zrangebyscore('SS_PR', prev, now) # for +
            new_r_pids = [item.decode() for item in new_r_pids] # type: ignore
            
            # --- Make New Token Values ---
            replace_pids = [f'{tx[2]["pid"]}' for tx in new_txs] # names to load and replace **new token id
            new_txs_pids = list(set(replace_pids))
            replace_pids.extend(new_r_pids) # type: ignore
            replace_pids = list(set(replace_pids))    # remove duplicates
            replace_pids_key = [f'P:{t}' for t in replace_pids]
            t_values = r.json().mget(replace_pids_key, ".")

            p_replace = {}
            for i in range(len(replace_pids_key)):
                if t_values[i]:
                    p_replace[replace_pids_key[i]] = t_values[i]
                else:
                    pass
            
            # apply for new txs (TODO: Score, Volume, Makers Algorithm)
            for tx in new_txs:
                p = f'P:{tx[2]["pid"]}' # type: ignore
                if tx[2]['instructionType'] == 'Liquidity':
                    p_replace[p]['price'] = common.getPrice(solPrice, tx[2]["baseAmount"], tx[2]['quoteAmount'], tx[2]['baseMint'], tx[2]['quoteMint'])
                    continue
                
                p_replace[p]['price'] = tx[2]['price']
                p_replace[p]['liq'] = tx[2]["quoteReserve"] * 2
                p_replace[p]['mcap'] = 1e9 * p_replace[p]['price']  # TODO with T:*
                
                if not p_replace[p]['dex']:
                    p_replace[p]['outerProgram'] = tx[2]['outerProgram']
                    dex = r.json().get(f'D:{tx[2]["outerProgram"]}')
                    if dex:
                        p_replace[p]['dex'] = dex['name']
                        p_replace[p]['dexImage'] = dex['image']

            # -- Calculate Pair Statistics --
            for pid in new_txs_pids:
                p = f'P:{pid}'
                for i in range(env.NUM_DURATIONS):
                    p_replace[p][f"st{i}"]['txns'] = (r.ts().get(f'TS_PT:{pid}:{env.DURATION_TS[i]}') or (0,0))[1] + (r.ts().get(f'TS_PT:{pid}:{env.DURATION_TS[i]}', latest = True) or (0, 0))[1]
                    p_replace[p][f"st{i}"]['volume'] = (r.ts().get(f'TS_PV:{pid}:{env.DURATION_TS[i]}') or (0, 0))[1] + (r.ts().get(f'TS_PV:{pid}:{env.DURATION_TS[i]}', latest = True) or (0, 0))[1]
                    p_replace[p][f"st{i}"]['makers'] = p_replace[p][f"st{i}"]['txns']   # TODO
                    prevPrice = (r.ts().get(f'TS_PA:{pid}:{env.DURATION_TS[i]}') or (0, 0))[1]
                    p_replace[p][f"st{i}"]['d_price'] = (p_replace[p]['price'] / prevPrice - 1.0) if prevPrice > 0 else 0.0

            # -- Apply for recent --
            for pid in new_r_pids: # type: ignore
                p = f'P:{pid}'
                p_replace[p]['r'] += 1
                for i in range(env.NUM_DURATIONS):
                    p_replace[p][f"st{i}"]['r'] += 1
           
            # Calculate score
            for i in range(env.NUM_DURATIONS):
                for p in p_replace.keys():
                    d_price = p_replace[p][f"st{i}"]['d_price'] + 1.0
                    d_price_affect = d_price if d_price > 1 else 1 # if d_price == 0 else 1 / d_price
                    score = p_replace[p][f'st{i}']['txns'] / 10000 * p_replace[p][f'st{i}']['volume'] / 10000 * d_price_affect
                    score *= 1.0 / (common.now() + 1 - p_replace[p]['created'])
                    # score = p_replace[p][f'st{i}']['volume']
                    p_replace[p][f'st{i}']['score'] = score    # TODO score algorithm
            
            r.json().mset([(f'P:{p["id"]}', ".", p) for p in p_replace.values()])
            # aaa= [(f'P:{p["id"]}', ".", p) for p in p_replace.values()]
            # for a in aaa:
            #     r.json().mset([a])
            # TODO sync with PG
            
            # -- For Query Result Sort --
            for i in range(env.NUM_DURATIONS):
                r.zadd(f"SS_PS{i}", {p["id"] : p[f"st{i}"]["score"] for p in p_replace.values()})
                r.zadd(f"SS_PV{i}", {p["id"] : p[f"st{i}"]["volume"] for p in p_replace.values()})
                r.zadd(f"SS_PX{i}", {p["id"] : p[f"st{i}"]["txns"] for p in p_replace.values()})
                r.zadd(f"SS_PPR{i}", {p["id"] : p[f"st{i}"]["d_price"] for p in p_replace.values()})
            r.zadd(f"SS_PP", {p["id"] : p["price"] for p in p_replace.values()})
            r.zadd(f"SS_PL", {p["id"] : p["liq"] for p in p_replace.values()})
            r.zadd(f"SS_PM", {p["id"] : p["mcap"] for p in p_replace.values()})

            # TODO sync with PG
            conn.commit()
            
            r.lpush('L_UPDATED', f'{common.now()}')

            # --- Send TXS_DATA ---
            payload = {}
            for i in range(len(new_txs)):
                tx = new_txs[len(new_txs) - i - 1][2]
                pool = tx['poolAddress']
                if pool not in payload:
                    payload[pool] = []
                payload[pool].append(tx)
            
            tasks = []
            for ns in env.NSS:
                rs = r.zrevrange(f'SS_RO{ns}', 0, -1, withscores=True)
                # print(rs)
                rooms = set()
                for room in rs:
                    if room and room[1] and room[1] > 0:
                        rooms.add(room[0].decode())
                for room in rooms:
                    tasks.append(asyncio.create_task(query_send(ns, room, payload)))
            if tasks:
                await asyncio.gather(*tasks)
            
            t_end = datetime.datetime.now()
            print(f'--- Input Redis ---({rep}): blockId: {new_txs[len(new_txs) - 1][2]["blockSlot"]} =>\
    {(t_end - t_start).total_seconds()} s\
    (DB: {(t_end1 - t_start1).total_seconds()} s\
    OTHERS:{((t_end - t_start) - (t_end1 - t_start1)).total_seconds()} s)')
            rep += 1
        conn.close()

    # except Exception as e:
    #     print(e)
    

if __name__ == "__main__":
    asyncio.run(update_thread())
