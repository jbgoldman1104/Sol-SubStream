from typing import ParamSpecArgs
import env
import common
import asyncio
import datetime
import time
from redis.commands.search.query import Query
import json
from redis.commands.json.path import Path

from random import random as rd
from random import randint as rdi

# class Block:
    # pass

def update_thread():
    r = common.connect_redis()
    conn = common.connect_db()
    cur = conn.cursor()

    # --- SYNC WITH INIT ---
    # r.xread( streams = {"INIT_COMPLETE": 0}, block = 60000 )
    # r.xtrim("INIT_COMPLETE", maxlen = 0)
    path = "."
    
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

        # --- add new block and txs ---
        new_txs = []
        blk_value = ''
        if env.USE_PG:
            # - import TX table from PG -
            read_tx_id = common.getSyncValue(cur, "read_tx_id", 0)
            cur.execute("SELECT * FROM trade WHERE id > %s", [read_tx_id])
            rows = cur.fetchmany(env.DB_READ_SIZE)
            new_txs = [common.toTx(cur, r, row) for row in rows]
            if len(new_txs) == 0: continue
            # r.json().mset(new_txs) # type: ignore
            read_tx_id = new_txs[len(new_txs)-1][2]["id"]
            common.setSyncValue(cur, "read_tx_id", read_tx_id)
            new_tx_count = len(rows)
        else:
            new_tx_count = 3
            for i in range(new_tx_count):
                id = common.rtx()
                timestamp = now - rdi(1, 3000)
                tx = common.toTx(cur, r, (id, common.rp(), common.rp(), rdi(1,5), rd()*100, rd() * 100, rdi(1, 0xFFFFFFFFFFFFFFFF), timestamp))
                new_txs.append(tx)
        # assert len(new_txs) > 0
        for tx in new_txs:
            if common.isUSD(tx[2]['quoteMint']) and common.isSol(tx[2]['baseMint']) and tx[2]['baseAmount'] != 0 and tx[2]['quoteAmount'] != 0:
                solPrice = abs(tx[2]['quoteAmount'] / tx[2]['baseAmount']) * (1 if common.isUSDT(tx[2]['quoteMint']) else 0.999632)
            tx[2]["price"] = common.getPrice(solPrice, tx[2]["baseAmount"], tx[2]['quoteAmount'], tx[2]['baseMint'], tx[2]['quoteMint']) # type: ignore
            blk_value += f'{tx[2]["id"]}' if not blk_value else f',{tx[2]["id"]}'
        # TODO lifetime
        r.json().mset(new_txs) # type: ignore
        r.zadd('SS_BLK', {blk_value: now})
        # TODO Sync with PG
        

        # --- Update Score ---
        prev_blocks = [r.zrangebyscore('SS_BLK', prev - env.DURATION[i], now - env.DURATION[i]) for i in range(4)]
        prev_prev_blocks = [r.zrangebyscore('SS_BLK', prev - env.DURATION[i] - env.PREV_SUM_LENGTH, now - env.DURATION[i] - env.PREV_SUM_LENGTH) for i in range(4)]
        
        # Add tokens for old txs
        old_txs_4 = []
        old_txs_p_ids_4 = []
        for i in range(4):
            if not prev_blocks[i]:
                old_txs_4.append([])
                old_txs_p_ids_4.append([])
                continue
            old_txs_ids = []
            for old_block in prev_blocks[i]: # type: ignore
                if not old_block: continue
                for old_tx in old_block.decode().split(','):
                    if not old_tx: continue
                    old_txs_ids.append(old_tx)
            txs_to_load = [f'TX:{id}' for id in old_txs_ids]
            if txs_to_load:
                old_txs_4.append(r.json().mget(txs_to_load, "."))
                newlist = []
                for tx in old_txs_4[i]:
                    if tx:
                        newlist.append(tx['pid'])
                old_txs_p_ids_4.append(newlist)

        # Add tokens for prev old txs
        prev_old_txs_4 = []
        prev_old_txs_p_ids_4 = []
        for i in range(4):
            if not prev_prev_blocks[i]:
                prev_old_txs_4.append([])
                prev_old_txs_p_ids_4.append([])
                continue
            old_txs_ids = []
            for old_block in prev_prev_blocks[i]: # type: ignore
                if not old_block: continue
                for old_tx in old_block.decode().split(','):
                    if not old_tx: continue
                    old_txs_ids.append(old_tx)
            txs_to_load = [f'TX:{id}' for id in old_txs_ids]
            if txs_to_load:
                prev_old_txs_4.append(r.json().mget(txs_to_load, "."))
                newlist = []
                for tx in prev_old_txs_4[i]:
                    if tx:
                        newlist.append(tx['pid'])
                prev_old_txs_p_ids_4.append(newlist)


        # --- Recent and Old Read Count ---
        new_r_pids = r.zrangebyscore('SS_PR', prev, now) # for +
        old_rs_pids_4 = [r.zrangebyscore('SS_PR', prev - env.DURATION[i], now - env.DURATION[i]) for i in range(4)] # type: ignore
        
        new_r_pids = [item.decode() for item in new_r_pids] # type: ignore
        for i in range(4):
            old_rs_pids_4[i] = [item.decode() for item in old_rs_pids_4[i]] # type: ignore
        
        # --- Make New Token Values ---
        replace_pids = [f'{tx[2]["pid"]}' for tx in new_txs] # names to load and replace **new token id
        replace_pids.extend(new_r_pids) # type: ignore
        for i in range(4):
            if old_rs_pids_4[i]:
                replace_pids.extend(old_rs_pids_4[i]) # type: ignore
            if old_txs_p_ids_4[i]:
                replace_pids.extend(old_txs_p_ids_4[i])
            if prev_old_txs_p_ids_4[i]:
                replace_pids.extend(prev_old_txs_p_ids_4[i])

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
            
            p_replace[p]['price'] = tx[2]['price']
            p_replace[p]['liq'] = tx[2]["quoteReserve"] * 2
            p_replace[p]['mcap'] = 1e9 * p_replace[p]['price']  # TODO with T:*

            for i in range(4):
                p_replace[p][f"st{i}"]['txns'] += 1
                p_replace[p][f"st{i}"]['volume'] += abs(tx[2]["baseAmount"] * p_replace[p]['price'])
                p_replace[p][f"st{i}"]['makers'] += 1   #TODO

                p_replace[p][f"st{i}"]['d_price'] = 1 if p_replace[p][f"st{i}"]['prevPrice'] == 0 else p_replace[p]['price'] / p_replace[p][f"st{i}"]['prevPrice']

        # apply for recent, old access count
        for pid in new_r_pids: # type: ignore
            p = f'P:{pid}'
            p_replace[p]['r'] += 1
            for i in range(4):
                p_replace[p][f"st{i}"]['r'] += 1
        for i in range(4):
            for pid in old_rs_pids_4[i]: # type: ignore
                p_replace[f'P:{pid}'][f'st{i}']['r'] -= 1
        
        # --- Handle Prev Old txs ---
        for i in range(4):
            if not prev_old_txs_4[i]: continue
            
            for tx in prev_old_txs_4[i]:
                if tx:
                    p = f'P:{tx["pid"]}' # type: ignore
                    amount = abs(tx["baseAmount"])
                    volume = amount * tx['price']
                    p_replace[p][f"st{i}"]['prevVolume'] -= volume
                    p_replace[p][f"st{i}"]['prevAmount'] -= amount
                    p_replace[p][f"st{i}"]['prevPrice'] = 0 if p_replace[p][f"st{i}"]['prevAmount'] == 0 else p_replace[p][f"st{i}"]['prevVolume'] / p_replace[p][f"st{i}"]['prevAmount']
                    p_replace[p][f"st{i}"]['d_price'] = 1 if p_replace[p][f"st{i}"]['prevPrice'] == 0 else p_replace[p]['price'] / p_replace[p][f"st{i}"]['prevPrice']

                    

        # --- Handle Old txs ---
        for i in range(4):
            if not old_txs_4[i]: continue
            
            for tx in old_txs_4[i]:
                if tx:
                    p = f'P:{tx["pid"]}' # type: ignore
                    p_replace[p][f"st{i}"]['txns'] -= 1
                    amount = abs(tx["baseAmount"])
                    volume = amount * tx["price"]
                    p_replace[p][f"st{i}"]['volume'] -= volume
                    p_replace[p][f"st{i}"]['makers'] -= 1   #TODO
                    
                    p_replace[p][f"st{i}"]['prevVolume'] += volume
                    p_replace[p][f"st{i}"]['prevAmount'] += amount
                    p_replace[p][f"st{i}"]['prevPrice'] = 0 if p_replace[p][f"st{i}"]['prevAmount'] == 0 else p_replace[p][f"st{i}"]['prevVolume'] / p_replace[p][f"st{i}"]['prevAmount']
                    p_replace[p][f"st{i}"]['d_price'] = 1 if p_replace[p][f"st{i}"]['prevPrice'] == 0 else p_replace[p]['price'] / p_replace[p][f"st{i}"]['prevPrice']

        for i in range(4):
            for p in p_replace.keys():
                # d_price = p_replace[p][f"st{i}"]['d_price']
                # d_price_affect = (d_price if d_price > 1 else 1 if d_price == 0 else 1 / d_price)
                # score = p_replace[p][f'st{i}']['txns'] / 10000 * p_replace[p][f'st{i}']['volume'] / 10000 * d_price_affect * d_price_affect * d_price_affect
                # score *= 1.0 / (common.now() + 1 - p_replace[p]['created'])
                score = p_replace[p][f'st{i}']['volume']
                p_replace[p][f'st{i}']['score'] = score    # TODO score algorithm
        
        r.json().mset([(f'P:{p["id"]}', ".", p) for p in p_replace.values()])
        # TODO sync with PG
        
        for i in range(4):
            r.zadd(f"SS_PS{i}", {p["id"] : p[f"st{i}"]["score"] for p in p_replace.values()})
        # TODO sync with PG
        
        r.xadd("UPDATE_RANK", {"date": str(datetime.datetime.now())})
        print(f'-- Input Redis ---({rep}): blockId: {new_txs[0][2]["blockSlot"]} => {(datetime.datetime.now() - t_start).total_seconds()} s')
        rep += 1
        
        conn.commit()
      
    conn.close()
    

if __name__ == "__main__":
    rlt = update_thread()