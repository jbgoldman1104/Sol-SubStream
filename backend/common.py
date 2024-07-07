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

def newP():
    return [0, 0, 0, 0, 0, 0,
            "", "", "", "",
            "", "", "", "",
            "", "", "", 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,]

def toP(r: redis.Redis, row: tuple):
    if len(row) == 6:
        newRow = newP()
        newRow[0] = row[0]
        for i in range(4): newRow[6+i] = row[i + 1]
        dex = ""
        dexImage = ""
        outerProgram = row[5]
        if outerProgram:
            did = r.hget('H_D', outerProgram)
            if not did:
                did = r.hlen('H_D') + 1
                r.hset('H_D', outerProgram, did)
            else:
                did = int(did.decode())
                dex = r.json().get(f'D:{did}')
                if dex:
                    dexImage = dex['image']
                    dex = dex['name']
        newRow[14] = dex
        newRow[15] = dexImage
        newRow[16] = outerProgram
        row = tuple(newRow)

    return (f"P:{row[0]}", ".", {"id": row[0], "price": row[1], "liq": row[2], "mcap": row[3], "cSupply": row[4], "tSupply": row[5],
            "baseMint": row[6], "quoteMint": row[7], "poolAddress": row[8], "created": row[9],
            "baseSymbol": row[10], "quoteSymbol": row[11], "baseName": row[12], "quoteName": row[13], 
            "dex": row[14], "dexImage": row[15], "outerProgram": row[16], "holders": row[17],
            "r": row[18+0], "txns": row[18+1], "buys": row[18+2], "sells": row[18+3], "volume": row[18+4], "buyVolume": row[18+5], "sellVolume": row[18+6], "makers": row[18+7], "buyers": row[18+8], "sellers": row[18+9],
            "r0": row[28+0], "score0": row[23+1], "txns0": row[23+2], "buys0": row[23+3], "sells0": row[23+4], "volume0": row[23+5], "buyVolume0": row[23+6], "sellVolume0": row[23+7], "makers0": row[23+8], "buyers0": row[23+9], "sellers0": row[23+10], "d_price0": row[23+11],
            "r1": row[40+0], "score1": row[35+1], "txns1": row[35+2], "buys1": row[35+3], "sells1": row[35+4], "volume1": row[35+5], "buyVolume1": row[35+6], "sellVolume1": row[35+7], "makers1": row[35+8], "buyers1": row[35+9], "sellers1": row[35+10], "d_price1": row[35+11],
            "r2": row[52+0], "score2": row[47+1], "txns2": row[47+2], "buys2": row[47+3], "sells2": row[47+4], "volume2": row[47+5], "buyVolume2": row[47+6], "sellVolume2": row[47+7], "makers2": row[47+8], "buyers2": row[47+9], "sellers2": row[47+10], "d_price2": row[47+11],
            "r3": row[64+0], "score3": row[59+1], "txns3": row[59+2], "buys3": row[59+3], "sells3": row[59+4], "volume3": row[59+5], "buyVolume3": row[59+6], "sellVolume3": row[59+7], "makers3": row[59+8], "buyers3": row[59+9], "sellers3": row[59+10], "d_price3": row[59+11],
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
        # assert len(row) == 19
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
                                      "pid": poolToId(cur, r, row[6], f'{baseMint}/{quoteMint}', row[12]), "type": type, "price": 0,
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
    return (f'W:{row[0]}', ".", {"wid": row[0], "address": row[1], "tid": row[2], "buy": row[3], "sell": row[4], "remain": row[5],
                                 "buyUSD": row[6], "sellUSD": row[7], "lastTx": row[8]})

def toD(row: tuple):
    return (f"D:{row[0]}", ".", {"id": row[0], "address": row[1], "name": row[2], "image": f'{row[3] if row[3] else "solana/solana.svg"}'})

def toT(row: tuple|list):
    return (f"T:{row[0]}", ".", {"id": row[0], "mint": row[1], "name": row[2], "symbol": row[3], "uri": row[4], "seller_fee_basis_points": row[5],
                                "creators": row[6], "verified": row[7], "share": row[8],  "mint_authority": row[9], "supply": row[10], 
                                "decimals": row[11], "supply_real": row[12], "is_initialized": row[13], "freeze_authority": row[14],
                                "image": row[15], "description": row[16], "twitter": row[17], "website": row[18],
                                "holders": row[19], "created": row[20],
                })

def defaultTValue(id, mint: str):
    return (id, mint, '', '', '', 0, [], [], [], None, 0, 0, 0, True, None, '', '', '', '', 0, 0)

def defaultT(id, mint: str):
    return toT(defaultTValue(id, mint))

def toW(row: tuple|list):
    return (f"W:{row[0]}", ".", {"id": row[0], "address": row[1], "tid": row[2], "buy": row[3], "sell": row[4], "remain": row[5],
                                "buyUSD": row[6], "sellUSD": row[7], "lastTx": row[8],
                })
    
def signerToId(r, address: str):
    id = r.hget('H_W', address)
    if not id:
        id = r.hlen('H_W') + 1
        r.hset('H_W', address, id)
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

def poolToId(cur, r, pool: str, pair: str = "", outerProgram = "" ):
    pid = r.hget('H_P', pool)
    if not pid:      # New Pair!
        if not pair: return None
        pid = r.hlen('H_P') + 1
        r.hset('H_P', pool, pid)
        split = pair.split('/')
        # r.hset('H_P2M', pool, pair)
        newP = toP(r, (pid, split[0], split[1], pool, nows(), outerProgram))
        r.json().mset([newP])

        # -- For Sorting --
        r.zadd(f"SS_PPrice",    {pid : 0})
        r.zadd(f"SS_PLiq",      {pid : 0})
        r.zadd(f"SS_PMcap",     {pid : 0})
        for i in range(env.NUM_DURATIONS):
            r.zadd(f"SS_PScore:{i}",     {pid : 0})
            r.zadd(f"SS_PVolume:{i}",    {pid : 0})
            r.zadd(f"SS_PTxns:{i}",      {pid : 0})
            r.zadd(f"SS_PDPrice:{i}",    {pid : 0})
            r.zadd(f"SS_PMakers:{i}",    {pid : 0})
            r.zadd(f"SS_PBuyers:{i}",    {pid : 0})
            r.zadd(f"SS_PSellers:{i}",   {pid : 0})
        
        MSEC = 1
        # Timeseries
        r.ts().create(f'TS_P:{pid}', retention_msecs = env.DAY * MSEC)
        for i in range(env.NUM_INTERVALS):
            # Open
            r.ts().create(f'TS_PO:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PO:{pid}:{i}', aggregation_type="first", bucket_size_msec=env.BD[i])
            # High
            r.ts().create(f'TS_PH:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PH:{pid}:{i}', aggregation_type="max", bucket_size_msec=env.BD[i])
            # Low
            r.ts().create(f'TS_PL:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PL:{pid}:{i}', aggregation_type="min", bucket_size_msec=env.BD[i])
            # Close
            r.ts().create(f'TS_PC:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PC:{pid}:{i}', aggregation_type="last", bucket_size_msec=env.BD[i])
            # Average
            r.ts().create(f'TS_PA:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            r.ts().createrule(f'TS_P:{pid}', f'TS_PA:{pid}:{i}', aggregation_type="avg", bucket_size_msec=env.BD[i])
            # Count(Transations)
            # r.ts().create(f'TS_PT:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            # r.ts().createrule(f'TS_P:{pid}', f'TS_PT:{pid}:{i}', aggregation_type="count", bucket_size_msec=env.BD[i])
            
        r.ts().create(f'TS_V:{pid}', retention_msecs = env.DAY * MSEC)
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_PV:{pid}:{i}', retention_msecs = env.RP[i] * MSEC)
            r.ts().createrule(f'TS_V:{pid}', f'TS_PV:{pid}:{i}', aggregation_type="sum", bucket_size_msec=env.BD[i])

        baseId = mintToId(cur, r, split[0])
        quoteId = mintToId(cur, r, split[1])

        r.sadd(f"S_TtoPs:{baseId}", pid) # type: ignore
        r.sadd(f"S_TtoPs:{quoteId}", pid) # type: ignore

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

def indexExists(r, index):
    try:
        # T`ry to get info about the index
        index_info = r.execute_command('FT.INFO', "IDX_T")
        return True
    except redis.exceptions.ResponseError as e:
        return False

if __name__ == "__main__":
    # print(getMintAddresses(r, '1'))
    pass