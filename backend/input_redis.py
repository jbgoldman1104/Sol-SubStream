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

from benchmark import _b
from random import random as rd
from random import randint as rdi
import query_redis
import input_pg
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
        __ = False  # Timing
    # try:
        r = common.connect_redis()
        pipe = r.pipeline()
        conn = common.connect_db()
        cur = conn.cursor()

        # --- SYNC WITH INIT ---
        # r.xread( streams = {"INIT_COMPLETE": 0}, block = 60000 )
        # r.xtrim("INIT_COMPLETE", maxlen = 0)
        
        # # for Sync with R & PG purpose
        # rlt = r.hmget()
        # rlt = r.zrange('SS_PScore0', 0, -1)
        # token_ids = set([t.decode() for t in rlt]) # type: ignore
        
        solPrice = 160
        rep = 1
        qcount = 0
        
        while True:
            time.sleep(0.2)
            
            t_start = datetime.datetime.now()

            # now = common.nows()
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
                # qcount += 1
                # print(qcount)
                t_end1 = datetime.datetime.now()
                
                new_txs = [common.toTx(cur, r, row) for row in rows]
                if len(new_txs) == 0: continue
                # r.json().mset(new_txs) # type: ignore
                read_tx_id = new_txs[len(new_txs)-1][2]["id"]
                
            synced_now = new_txs[len(new_txs) - 1][2]['blockTime']

            # --- Block's TX ids --- Checked
            # assert len(new_txs) > 0
            w_update = []
            new_txs_sel = []
            if __: _b('1')
            for tx in new_txs:
                if tx[2]['instructionType'] != "Liquidity": #and tx[2]['outerProgram'] != 'FqGg2Y1FNxMiGd51Q6UETixQWkF5fB92MysbYogRJb3P'
                    if common.isUSD(tx[2]['quoteMint']) and common.isSOL(tx[2]['baseMint']) and tx[2]['baseAmount'] != 0 and tx[2]['quoteAmount'] != 0 and tx[2]['poolAddress'] == 'B6LL9aCWVuo1tTcJoYvCTDqYrq1vjMfci8uHxsm4UxTR':
                        solPrice = abs(tx[2]['quoteAmount'] / tx[2]['baseAmount']) * (1 if common.isUSDT(tx[2]['quoteMint']) else 0.999632)
                    tx[2]["price"] = common.getPrice(solPrice, tx[2]["baseAmount"], tx[2]['quoteAmount'], tx[2]['baseMint'], tx[2]['quoteMint'])
                    blk_value += f'{tx[2]["id"]}' if not blk_value else f',{tx[2]["id"]}'
                    new_txs_sel.append(tx)
                    
                    wid = common.signerToId(r, tx[2]['signer'])
                    tid = common.mintToId(cur, r, tx[2]['baseMint'])
                    amount = abs(tx[2]['baseAmount'])
                    volume = amount * tx[2]['price']
                    if tx[2]['type'] == "Buy":
                        w_update.append((wid, tx[2]['signer'], tid,     amount, 0, amount,    volume, 0, tx[2]['id']))
                        pipe.zincrby(f'SS_THolders_Ref:{tid}', amount, wid)
                    else:
                        w_update.append((wid, tx[2]['signer'], tid,     0, amount, -amount,    0, volume, tx[2]['id']))
                        pipe.zincrby(f'SS_THolders_Ref:{tid}', -amount, wid)

            
            # TODO lifetime, Only Hot Tx
            prev_time = r.zrevrange('SS_BLK', 0, 0, withscores=True)
            prev = synced_now if not prev_time else int(prev_time[0][1]) # type: ignore
            # delta = synced_now - prev
            
            if new_txs:
                r.json().mset(new_txs) # type: ignore
            for tx in new_txs:
                pipe.expire(tx[0], env.EXPIRE_TIME)
            r.zadd('SS_BLK', { blk_value: synced_now })
            remove_blks = r.zrevrangebyscore('SS_BLK', synced_now - env.EXPIRE_TIME, "-inf")
            pipe.zremrangebyscore('SS_BLK', "-inf", synced_now - env.EXPIRE_TIME)
            # for blk in remove_blks:
            #     tx_ids = blk.decode().split(',')
            #     pipe.delete(*[f'TX:{tx_id}' for tx_id in tx_ids])
            pipe.execute()
            if __: _b()

            # --- TS_i ---
            if __: _b('3')
            r.ts().madd([(f'TS_P:{tx[2]["pid"]}', tx[2]['blockTime'], tx[2]['price']) for tx in new_txs_sel])
            r.ts().madd([(f'TS_V:{tx[2]["pid"]}', tx[2]['blockTime'], abs(tx[2]['baseAmount']) * tx[2]['price']) for tx in new_txs_sel])
            if __: _b()

            # --- Recent and Old Read Count ---
            
            if __: _b('4')
            new_r_pids = r.zrangebyscore('SS_PR', prev, synced_now) # for +
            new_r_pids = [item.decode() for item in new_r_pids] # type: ignore
            
            # --- Make New Token Values ---
            replace_pids = [f'{tx[2]["pid"]}' for tx in new_txs] # names to load and replace **new token id
            new_txs_pids = list(set(replace_pids))
            replace_pids.extend(new_r_pids) # type: ignore
            replace_pids = list(set(replace_pids))    # remove duplicates
            replace_pids_key = [f'P:{t}' for t in replace_pids]
            t_values = r.json().mget(replace_pids_key, ".")

            t_update = {}
            p_update = {}
            for i in range(len(replace_pids_key)):
                if t_values[i]:
                    p_update[replace_pids_key[i]] = t_values[i]
                else:
                    pass
            if __: _b()
            
            # -- Apply for new txs (TODO: Score, Volume, Makers Algorithm) --
            if __: _b('5')
            for tx in new_txs:
                pid = tx[2]["pid"]
                p = f'P:{pid}' # type: ignore
                if tx[2]['instructionType'] == 'Liquidity':
                    p_update[p]['price'] = common.getPrice(solPrice, tx[2]["baseAmount"], tx[2]['quoteAmount'], tx[2]['baseMint'], tx[2]['quoteMint'])
                    if tx[2]['type'] == 'Add':
                        p_update[p]['tSupply'] += tx[2]["baseAmount"]
                    elif tx[2]['type'] == 'Remove':
                        p_update[p]['tSupply'] -= tx[2]["baseAmount"]
                    p_update[p]['cSupply'] = p_update[p]['tSupply'] -  tx[2]["baseReserve"]
                    continue
                
                # if tx[2]['price'] <= 10 * p_update[p]['price']:
                p_update[p]['price'] = tx[2]['price']
                p_update[p]['liq'] = tx[2]["quoteReserve"] * 2
                p_update[p]['mcap'] = (p_update[p]['tSupply'] or 1e9) * p_update[p]['price']  # TODO with T:*
                
                volume = tx[2]['price'] * abs(tx[2]['baseAmount'])
                p_update[p]['volume'] += volume
                p_update[p]['txns'] += 1

                if tx[2]['type'] == 'Buy':
                    p_update[p]['buyVolume'] += volume
                    p_update[p]['buys'] += 1
                elif tx[2]['type'] == 'Sell':
                    p_update[p]['sellVolume'] += volume
                    p_update[p]['sells'] += 1


                if p_update[p]['volume'] < 0:
                    aaaa = 1

                # -- Make Txns, Makers, Buyers, Sellers tree --
                pipe.zadd(f'SS_PVolume_Ref:{pid}', {p_update[p]['volume']: tx[2]['blockTime']})
                pipe.zadd(f'SS_PBuyVolume_Ref:{pid}', {p_update[p]['buyVolume']: tx[2]['blockTime']})
                pipe.zadd(f'SS_PSellVolume_Ref:{pid}', {p_update[p]['sellVolume']: tx[2]['blockTime']})
                pipe.zadd(f'SS_PTxns_Ref:{pid}', {tx[2]['id']: tx[2]['blockTime']})
                pipe.zadd(f'SS_PMakers_Ref:{pid}', {tx[2]['signer']: tx[2]['blockTime']})
                if tx[2]['type'] == 'Buy':
                    pipe.zadd(f'SS_PBuys_Ref:{pid}', {tx[2]['id']: tx[2]['blockTime']})
                    pipe.zadd(f'SS_PBuyers_Ref:{pid}', {tx[2]['signer']: tx[2]['blockTime']})
                else:
                    pipe.zadd(f'SS_PSells_Ref:{pid}', {tx[2]['id']: tx[2]['blockTime']})
                    pipe.zadd(f'SS_PSellers_Ref:{pid}', {tx[2]['signer']: tx[2]['blockTime']})
                
                
                # -- Assert dex info --
                if not p_update[p]['dex']:
                    p_update[p]['outerProgram'] = tx[2]['outerProgram']
                    dex = r.json().get(f'D:{common.dexToId(cur, r, tx[2]["outerProgram"])}')
                    if dex:
                        p_update[p]['dex'] = dex['name']
                        p_update[p]['dexImage'] = dex['image']
            pipe.execute()
            if __: _b()

            # -- Calculate Pair Statistics --
            if __: _b('6')
            for pid in new_txs_pids:
                p = f'P:{pid}'
                for i in range(env.NUM_DURATIONS):
                    pipe.ts().get(f'TS_PA:{pid}:{env.DURATION_TS[i]}')
                    pipe.zrevrangebyscore(f'SS_PVolume_Ref:{pid}', synced_now - env.DURATION[i], '-inf', 0, 1)
                    pipe.zrevrangebyscore(f'SS_PBuyVolume_Ref:{pid}', synced_now - env.DURATION[i], '-inf', 0, 1)
                    pipe.zrevrangebyscore(f'SS_PSellVolume_Ref:{pid}', synced_now - env.DURATION[i], '-inf', 0, 1)
                    pipe.zcount(f'SS_PTxns_Ref:{pid}', synced_now - env.DURATION[i], synced_now)
                    pipe.zcount(f'SS_PBuys_Ref:{pid}', synced_now - env.DURATION[i], synced_now)
                    pipe.zcount(f'SS_PSells_Ref:{pid}', synced_now - env.DURATION[i], synced_now)
                    pipe.zcount(f'SS_PMakers_Ref:{pid}', synced_now - env.DURATION[i], synced_now)
                    pipe.zcount(f'SS_PBuyers_Ref:{pid}', synced_now - env.DURATION[i], synced_now)
                    pipe.zcount(f'SS_PSellers_Ref:{pid}', synced_now - env.DURATION[i], synced_now)
                pipe.zcount(f'SS_PMakers_Ref:{pid}', "-inf", "+inf")
                pipe.zcount(f'SS_PBuyers_Ref:{pid}', "-inf", "+inf")
                pipe.zcount(f'SS_PSellers_Ref:{pid}', "-inf", "+inf")
                pipe.zcount(f'SS_THolders_Ref:{pid}', 0.0000000001, "+inf")
            read_data = pipe.execute()
            
            pi = 0
            for pid in new_txs_pids:
                p = f'P:{pid}'
                for i in range(env.NUM_DURATIONS):
                    # p_replace[p][f'txns{i}'] = (r.ts().get(f'TS_PT:{pid}:{env.DURATION_TS[i]}') or (0,0))[1] + (r.ts().get(f'TS_PT:{pid}:{env.DURATION_TS[i]}', latest = True) or (0, 0))[1]
                    # p_replace[p][f'volume{i}'] = (r.ts().get(f'TS_PV:{pid}:{env.DURATION_TS[i]}') or (0, 0))[1] + (r.ts().get(f'TS_PV:{pid}:{env.DURATION_TS[i]}', latest = True) or (0, 0))[1]
                    # p_replace[p][f'makers{i}'] = p_replace[p][f'txns{i}']   # TODO
                    prevPrice = (read_data[pi]  or (0, 0))[1]
                    pi += 1
                    p_update[p][f'd_price{i}'] = (p_update[p]['price'] / prevPrice - 1.0) if prevPrice > 0 else 0.0

                    val = read_data[pi]
                    pi += 1
                    val = val[0].decode() if val else 0
                    p_update[p][f'volume{i}'] = p_update[p]['volume'] - float(val)
                    val = read_data[pi]
                    pi += 1
                    val = val[0].decode() if val else 0
                    p_update[p][f'buyVolume{i}'] = p_update[p]['buyVolume'] - float(val)
                    val = read_data[pi]
                    pi += 1
                    val = val[0].decode() if val else 0
                    p_update[p][f'sellVolume{i}'] = p_update[p]['sellVolume'] - float(val)

                    p_update[p][f'txns{i}'] = read_data[pi]
                    pi += 1
                    p_update[p][f'buys{i}'] = read_data[pi]
                    pi += 1
                    p_update[p][f'sells{i}'] = read_data[pi]
                    pi += 1
                    
                    p_update[p][f'makers{i}'] = read_data[pi]
                    pi += 1
                    p_update[p][f'buyers{i}'] = read_data[pi]
                    pi += 1
                    p_update[p][f'sellers{i}'] = read_data[pi]
                    pi += 1
                p_update[p]['makers'] = read_data[pi]
                pi += 1
                p_update[p]['buyers'] = read_data[pi]
                pi += 1
                p_update[p]['sellers'] = read_data[pi]
                pi += 1
                # TODO
                tid = common.mintToId(cur, r, p_update[p]['baseMint'])
                holders = read_data[pi]
                pi += 1
                p_update[p]['holders'] = holders
                # t_update[tid]['holders'] = 
            if __: _b()

            # -- Apply for recent --
            if __: _b('7')
            for pid in new_r_pids: # type: ignore
                p = f'P:{pid}'
                p_update[p]['r'] += 1
                for i in range(env.NUM_DURATIONS):
                    p_update[p][f'r{i}'] += 1
            if __: _b()
           
            # -- Calculate score --
            if __: _b('8')
            for i in range(env.NUM_DURATIONS):
                for p in p_update.keys():
                    d_price = p_update[p][f'd_price{i}'] + 1.0
                    d_price_affect = d_price if d_price > 1 else 1 # if d_price == 0 else 1 / d_price
                    score = p_update[p][f'txns{i}'] / 10000 * p_update[p][f'volume{i}'] / 10000 * d_price_affect
                    score *= 1.0 / (common.now() + 1 - p_update[p]['created'])
                    # score = p_replace[p][f'volume{i}']
                    p_update[p][f'score{i}'] = score    # TODO score algorithm
            
            r.json().mset([(f'P:{p["id"]}', ".", p) for p in p_update.values()])
            if __: _b()
            # aaa= [(f'P:{p["id"]}', ".", p) for p in p_replace.values()]
            # for a in aaa:
            #     r.json().mset([a])
            # TODO sync with PG
            
            
            # -- For Query Result Sort --
            if __: _b('9')
            r.zadd(f'SS_PPrice',    {p['id'] : p['price'] for p in p_update.values()})
            r.zadd(f'SS_PLiq',      {p['id'] : p['liq'] for p in p_update.values()})
            r.zadd(f'SS_PMcap',     {p['id'] : p['mcap'] for p in p_update.values()})
            for i in range(env.NUM_DURATIONS):
                r.zadd(f'SS_PScore:{i}',     {p['id'] : p[f'score{i}'] for p in p_update.values()})
                r.zadd(f'SS_PVolume:{i}',    {p['id'] : p[f'volume{i}'] for p in p_update.values()})
                r.zadd(f'SS_PTxns:{i}',      {p['id'] : p[f'txns{i}'] for p in p_update.values()})
                r.zadd(f'SS_PDPrice:{i}',    {p['id'] : p[f'd_price{i}'] for p in p_update.values()})
                r.zadd(f'SS_PMakers:{i}',    {p['id'] : p[f'makers{i}'] for p in p_update.values()})
                r.zadd(f'SS_PBuyers:{i}',    {p['id'] : p[f'buyers{i}'] for p in p_update.values()})
                r.zadd(f'SS_PSellers:{i}',   {p['id'] : p[f'sellers{i}'] for p in p_update.values()})
            if __: _b()


            # TODO sync with PG
            if __: _b('10')
            conn.commit()
            if __: _b()
            
            r.lpush('L_UPDATED', f'{common.now()}')

            # --- Send TXS_DATA ---
            if __: _b('11')
            payload = {}
            for i in range(len(new_txs)):
                tx = new_txs[len(new_txs) - i - 1][2]
                pool = tx['poolAddress']
                if pool not in payload:
                    payload[pool] = []
                payload[pool].append(tx)
            if __: _b()
            
            # -- finished updating one period --
            # -TODO Backup-
            # r.dump()
            # r.restore()

            # -TODO Sync with PG-
            if __: _b('save db')
            input_pg.update_txs(cur, new_txs)            # insert
            input_pg.write_pairs(cur, p_update)         # insert/update
            input_pg.update_wallets(cur, w_update)      # insert/get + update
            # input_pg.update_tokens(cur, t_update)
            common.setSyncValue(cur, "read_tx_id", read_tx_id)
            if __: _b()
            
            if __: _b('tx send')
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
            if __: _b()
            
            t_end = datetime.datetime.now()
            blockTime = new_txs[len(new_txs) - 1][2]["blockTime"] + 7 * 3600
            print(f'--- Input Redis ---({rep}_{len(new_txs)}): blockTime: {datetime.datetime.fromtimestamp(blockTime)} =>\
    {(t_end - t_start).total_seconds()} s\
    (DB: {(t_end1 - t_start1).total_seconds()} s\
    OTHERS:{((t_end - t_start) - (t_end1 - t_start1)).total_seconds()} s)')
            rep += 1
            
            conn.commit()
            
        conn.close()

    # except Exception as e:
    #     print(e)
    

if __name__ == "__main__":
    asyncio.run(update_thread())
