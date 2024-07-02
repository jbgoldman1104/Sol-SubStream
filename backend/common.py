from typing import Any
import env
import psycopg
import redis
import datetime
from random import randint as rdi
# import token_info
import json
import os
import socketio

# def get_redis_manager():
#     socketio.AsyncRedisManager(f'redis://{env.REDIS_HOST}:{env.REDIS_PORT}/0', write_only=True)

def connect_redis():
    return redis.Redis(host = env.REDIS_HOST, port = env.REDIS_PORT)

def connect_db():
    return psycopg.connect(host = env.DB_HOST, port = env.DB_PORT, dbname = env.DB_NAME, user = env.DB_USER, password = env.DB_PASS)

def getToken(r: redis.Redis, token: str):
    return r.json().get("P:" + token)

# def name2id(r: redis.Redis, token: str):
#     return r.json().get("P:" + token, "id")

def nows():
    return int(datetime.datetime.now().timestamp())
    
def now():
    return int(datetime.datetime.now().timestamp() * 1000)

def toP(row: tuple):
    # if env.USE_PG:
    #     return {"id":}
    # else:
        return (f"P:{row[0]}", ".", {"id": row[0], "price": 0, "liq": 0, "mcap": 0, "cSupply": 0, "tSupply": 0,
                "baseMint": row[1], "quoteMint": row[2], "poolAddress": row[3], "created": row[4],
                "baseSymbol":"", "quoteSymbol":"", "baseName": "", "quoteName": "", "dex": "", "dexImage":"", "outerProgram": "",
                "holders": 0,
                "r": 0, "txns": 0, "buys": 0, "sells": 0, "volume": 0, "buyVolume": 0, "sellVolume": 0, "makers": 0, "buyers": 0, "sellers": 0,
                "r0": 0, "score0": 0, "txns0": 0, "buys0": 0, "sells0": 0, "volume0": 0, "buyVolume0": 0, "sellVolume0": 0, "makers0": 0, "buyers0": 0, "sellers0": 0, "d_price0": 0,
                "r1": 0, "score1": 0, "txns1": 0, "buys1": 0, "sells1": 0, "volume1": 0, "buyVolume1": 0, "sellVolume1": 0, "makers1": 0, "buyers1": 0, "sellers1": 0, "d_price1": 0,
                "r2": 0, "score2": 0, "txns2": 0, "buys2": 0, "sells2": 0, "volume2": 0, "buyVolume2": 0, "sellVolume2": 0, "makers2": 0, "buyers2": 0, "sellers2": 0, "d_price2": 0,
                "r3": 0, "score3": 0, "txns3": 0, "buys3": 0, "sells3": 0, "volume3": 0, "buyVolume3": 0, "sellVolume3": 0, "makers3": 0, "buyers3": 0, "sellers3": 0, "d_price3": 0,
                })

def getPSymbols(r, p):
    if not p["baseName"]:
        tid = mintToId(None, r, p["baseMint"])
        if tid:
            p["baseSymbol"] = r.json().get(f'T:{tid}')['symbol']
            p["baseName"] = r.json().get(f'T:{tid}')['name']

    if not p["quoteName"]:
        tid = mintToId(None, r, p["quoteMint"])
        if tid:
            p["quoteSymbol"] = r.json().get(f'T:{tid}')['symbol']
            p["quoteName"] = r.json().get(f'T:{tid}')['name']
    
    return [p["baseSymbol"] if p["baseSymbol"] else p["baseMint"],
            p["quoteSymbol"] if p["quoteSymbol"] else p["quoteMint"]]

def order(mint: str):
    if isUSDT(mint): return 1
    elif isUSDC(mint): return 2
    elif isSOL(mint): return 10
    else: return 100

    

def toTx(cur, r, row: tuple):
    if env.USE_PG:
        assert len(row) == 19
        swap = order(row[7]) < order(row[8])
        baseMint = row[8] if swap else row[7]
        quoteMint = row[7] if swap else row[8]
        baseAmount = row[10] if swap else row[9]
        quoteAmount = row[9] if swap else row[10]
        if row[11] == "SwapBaseIn":
            type = "Sell" if baseAmount > 0 else "Buy"
        elif row[11] == "Liquidity":
            type = "Add" if baseAmount > 0 else "Remove"
        else: # TODO
            type = "Sell" if baseAmount > 0 else "Buy"
            
        return (f'TX:{row[0]}', ".", {"id": row[0], "blockDate": row[1].timestamp(), "blockTime": row[2], "blockSlot": row[3],
                                      "txId": row[4], "signer": row[5], "poolAddress": row[6], "baseMint": baseMint, "quoteMint": quoteMint,
                                      "baseAmount": baseAmount, "quoteAmount": quoteAmount, "instructionType": row[11],
                                      "outerProgram": row[12], "innerProgram": row[13], "baseReserve": row[14], "quoteReserve": row[15], 
                                      # new fields
                                      "pid": poolToId(cur, r, row[6], f'{baseMint}/{quoteMint}'), "type": type, "price": 0,
                                      })


def fetchOneValue(cur, sql: str, params: list = []):
    cur.execute(sql, [])
    row = cur.fetchone()
    return row[0] if row else None

def getSyncValue(cur, field: str, defaultValue: Any):
    rlt = fetchOneValue(cur, f'SELECT "{field}" FROM sync')
    return rlt if rlt else defaultValue

def setSyncValue(cur, field: str, value: Any):
    cur.execute(f'UPDATE sync set "{field}" = %s', [value])
    return True

fileT = None
def writeT(meta: dict):
    global fileT
    if not fileT:
        if not os.path.exists(env.FILENAME_T):
            open(env.FILENAME_T, 'x')
        fileT = open(env.FILENAME_T, 'a')
    if fileT:
        json.dump(meta, fileT)
        fileT.write('\n')
    # fileT.close()

fileFailedT = None
def writeFailedT(id, mint):
    global fileFailedT
    if not fileFailedT:
        if not os.path.exists(env.FILENAME_FailedT):
            open(env.FILENAME_FailedT, 'x')
        fileFailedT = open(env.FILENAME_FailedT, 'a')
    if fileFailedT:
        json.dump(defaultTValue(id, mint), fileFailedT)
        fileFailedT.write('\n')
    # fileFailedT.close()

def toW(row: tuple):
    return (f'W:{row[0]}', ".", {"id": row[0], "address": row[1]})

def toD(row: tuple):
    return (f"D:{row[1]}", ".", {"id": row[0], "address": row[1], "name": row[2], "image": f'/images/dex/{row[3] if row[3] else "solana/solana.svg"}'})

def toT(row: tuple|list):
    return (f"T:{row[0]}", ".", {"id": row[0], "mint": row[1], "name": row[2], "symbol": row[3], "uri": row[4], "seller_fee_basis_points": row[5],
                                "creators": row[6], "verified": row[7], "share": row[8],  "mint_authority": row[9], "supply": row[10], 
                                "decimals": row[11], "supply_real": row[12], "is_initialized": row[13], "freeze_authority": row[14],
                                "image": row[15], "description": row[16], "twitter": row[17], "website": row[18],
                                "holders": 0, "created": 0,
                })

def defaultTValue(id, mint: str):
    return (f'{id}', mint, '', '', '', 0, [], [], [], None, 0, 0, 0, True, None, '', '', '', '')

def defaultT(id, mint: str):
    return toT(defaultTValue(id, mint))

def signerToId(r, address: str):
    id = r.hget('H_S', address)
    if not id:
        id = r.hlen('H_S') + 1
        r.hset('H_S', address, id)
    else:
        id = int(id.decode())
    return id

def mintToId(cur, r, mint: str):
    id = r.hget('H_T', mint)
    if not id:  # New Token!
        id = r.hlen('H_T') + 1
        # print(f"new mint {mint} => {id}")
        r.hset('H_T', mint, id)
        r.json().mset([defaultT(id, mint)])
        # token_info.update_nft(cur, r, id, mint)
        # r.xadd('TOKEN_STREAM', {id: mint})
        r.lpush('L_TOKENS', f'{id},{mint}')
        # r.zadd(f'SS_TRemain{id}', {id: 0})
        # TODO sync with PG
    else:
        id = int(id.decode())
    return id

def getMintAddresses(r, pid):
    # pair = r.hget('H_P2M', pid)
    p = r.json().get(f'P:{pid}')
    if p:
        return [p['baseMint'], p['quoteMint']]
    return []

    

def getSymbols(r, pid):
    p = r.json().get(f'P:{pid}')
    if p:
        return getPSymbols(r, p)
    return None

def poolToId(cur, r, pool: str, pair: str = "" ):
    pid = r.hget('H_P', pool)
    if not pid:      # New Pair!
        if not pair: return None
        pid = r.hlen('H_P') + 1
        r.hset('H_P', pool, pid)
        split = pair.split('/')
        # r.hset('H_P2M', pool, pair)
        newP = toP((f'{pid}', split[0], split[1], pool, now()))
        r.json().mset([newP])

        # -- For Sorting --
        r.zadd(f"SS_PPrice",   {pid : 0})
        r.zadd(f"SS_PLiq",   {pid : 0})
        r.zadd(f"SS_PMcap",   {pid : 0})
        for i in range(env.NUM_DURATIONS):
            r.zadd(f"SS_PScore{i}",     {pid : 0})
            r.zadd(f"SS_PVolume{i}",    {pid : 0})
            r.zadd(f"SS_PTxns{i}",      {pid : 0})
            r.zadd(f"SS_PDPrice{i}",    {pid : 0})
            r.zadd(f"SS_PMakers{i}",    {pid : 0})
            r.zadd(f"SS_PBuyers{i}",    {pid : 0})
            r.zadd(f"SS_PSellers{i}",   {pid : 0})
        
        
        # Timeseries
        r.ts().create(f'TS_P:{pid}', retention_msecs=env.DAY*1000)
        for i in range(env.NUM_INTERVALS):
            # Open
            r.ts().create(f'TS_PO:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PO:{pid}:{i}', aggregation_type="first", bucket_size_msec=env.BD[i])
            # High
            r.ts().create(f'TS_PH:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PH:{pid}:{i}', aggregation_type="max", bucket_size_msec=env.BD[i])
            # Low
            r.ts().create(f'TS_PL:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PL:{pid}:{i}', aggregation_type="min", bucket_size_msec=env.BD[i])
            # Close
            r.ts().create(f'TS_PC:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PC:{pid}:{i}', aggregation_type="last", bucket_size_msec=env.BD[i])
            # Average
            r.ts().create(f'TS_PA:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PA:{pid}:{i}', aggregation_type="avg", bucket_size_msec=env.BD[i])
            # Count(Transations)
            r.ts().create(f'TS_PT:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PT:{pid}:{i}', aggregation_type="count", bucket_size_msec=env.BD[i])
            
        r.ts().create(f'TS_V:{pid}', retention_msecs=env.DAY*1000)
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_PV:{pid}:{i}', retention_msecs=env.RP[i]*1000)
            r.ts().createrule(f'TS_V:{pid}', f'TS_PV:{pid}:{i}', aggregation_type="sum", bucket_size_msec=env.BD[i])

        baseId = mintToId(cur, r, split[0])
        quoteId = mintToId(cur, r, split[1])

        r.sadd(f"S_TtoPs{baseId}", pid) # type: ignore
        r.sadd(f"S_TtoPs{quoteId}", pid) # type: ignore

        # TODO sync with PG
        # insertP(cur, newP)
    else:
        pid = int(pid.decode())
    return pid

def isSOL(mint: str):
    return mint == 'So11111111111111111111111111111111111111112'

def isUSD(mint: str):
    return isUSDC(mint) or isUSDT(mint)

def isUSDC(mint: str):
    return mint == 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'

def isUSDT(mint: str):
    return mint == 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'

def getQuotePrice(quoteMint: str):
    return (170.0 if quoteMint == 'So11111111111111111111111111111111111111112' else 1 )

def getPrice(solPrice, baseAmount, quoteAmount, baseMint, quoteMint):
    price = 0
    if baseAmount != 0 and quoteAmount != 0:
        if isUSD(baseMint): 
            price = 1 if isUSDT(baseMint) else 0.999632
        elif isUSD(quoteMint):
            price = quoteAmount / baseAmount * (1 if isUSDT(quoteMint) else 0.999632)
            # if isSol(baseMint):
            #     solPrice = price
        elif isSOL(baseMint):
            price = solPrice
        elif isSOL(quoteMint):
            price = solPrice * quoteAmount / baseAmount
        else:
            #TODO
            # r.json().mget(replace_pids_key, ".")
            # p = f'P:{tx[2]["pid"]}'
            pass
    return abs(price)
# __app__ = [connect_redis, connect_db]

def js(data):
    try:
        return json.loads(data) if type(data) == str else data
    except json.JSONDecodeError as e:
        return json.loads(data.replace("\'", "\""))


if __name__ == "__main__":
    # print(getMintAddresses(r, '1'))
    pass