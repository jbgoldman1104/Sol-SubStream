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
        return (f"P:{row[0]}", ".", {"id": row[0], "price": row[1], "liq": row[2], "mcap": row[3], "r": row[4],
                "st0": {"r": row[5], "score": row[6], "txns": row[7], "volume": row[8], "makers": row[9], "d_price": row[10], "prevVolume": row[11], "prevAmount": row[12], "prevPrice": row[13]},
                "st1": {"r": row[14], "score": row[15], "txns": row[16], "volume": row[17], "makers": row[18], "d_price": row[19], "prevVolume": row[20], "prevAmount": row[21], "prevPrice": row[22]},
                "st2": {"r": row[23], "score": row[24], "txns": row[25], "volume": row[26], "makers": row[27], "d_price": row[28], "prevVolume": row[29], "prevAmount": row[30], "prevPrice": row[31]},
                "st3": {"r": row[32], "score": row[33], "txns": row[34], "volume": row[35], "makers": row[36], "d_price": row[37], "prevVolume": row[38], "prevAmount": row[39], "prevPrice": row[40]},

                "baseMint": row[41], "quoteMint": row[42], "poolAddress": row[43], "created": row[44], 
                "baseSymbol":"", "quoteSymbol":"", "baseName": "", "quoteName": ""
                })

def getPSymbols(r, p):
    if not p[2]["baseName"]:
        tid = mintToId(p[2]["baseMint"])
        if tid:
            p[2]["baseSymbol"] = r.get(f'T:{tid}')['symbol']
            p[2]["baseName"] = r.get(f'T:{tid}')['name']

    if not p[2]["quoteName"]:
        tid = mintToId(p[2]["quoteMint"])
        if tid:
            p[2]["quoteSymbol"] = r.get(f'T:{tid}')['symbol']
            p[2]["quoteName"] = r.get(f'T:{tid}')['name']
    
    return [p[2]["baseSymbol"] if p[2]["baseSymbol"] else p[2]["baseMint"],
            p[2]["quoteSymbol"] if p[2]["quoteSymbol"] else p[2]["quoteMint"]]


def toTx(cur, r, row: tuple):
    if env.USE_PG:
        assert len(row) == 16
        return (f'TX:{row[0]}', ".", {"id": row[0], "blockDate": row[1].timestamp(), "blockTime": row[2], "blockSlot": row[3],
                                      "txId": row[4], "signer": row[5], "poolAddress": row[6], "baseMint": row[7], "quoteMint": row[8],
                                      "baseAmount": row[9], "quoteAmount": row[10], "instructionType": row[11],
                                      "outerProgram": row[12], "innerProgram": row[13], "baseReserve": row[14], "quoteReserve": row[15], 
                                      # new fields
                                      "pid": poolToId(cur, r, row[6], f'{row[7]}/{row[8]}'), "type": "Buy" if row[9] > 0 else "Sell", "price": 0,
                                      
                                      })
    else:
        assert len(row) == 8
        return (f'TX:{row[0]}', ".", {"id": row[0], "baseMint": row[1], "quoteMint": row[2], "type": row[3], "baseAmount": row[4], "quoteAmount": row[5],
                                        "signer": row[6], "blockTime": row[7]})

def rp():
    return f'T{rdi(0, env.NTEST-1)}'

def rtx():
    return f'{rdi(1, 0xFFFF)}'

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

def insertP(cur, newT):
    cur.execute(f'''
                INSERT INTO tokens("id", "price", "liq", "mcap", "r", 
                "r0", "score0", "txns0", "volume0", "makers0", d_price0
                "r1", "score1", "txns1", "volume1", "makers1", d_price1
                "r2", "score2", "txns2", "volume2", "makers2", d_price2
                "r3", "score3", "txns3", "volume3", "makers3", d_price3
                ") 
    VALUES (%s,%s,%s,%s,%s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s, %s, %s, %s, %s, %s, )', 
            newT["id"], newT["price"], newT["liq"], newT["mcap"],
            newT["st0"]["r"], newT["st0"]["score"], newT["st0"]["txns"], newT["st0"]["volume"], newT["st0"]["makers]"], newT["st0"]["d_price"],
            newT["st1"]["r"], newT["st1"]["score"], newT["st1"]["txns"], newT["st1"]["volume"], newT["st1"]["makers]"], newT["st1"]["d_price"],
            newT["st2"]["r"], newT["st2"]["score"], newT["st2"]["txns"], newT["st2"]["volume"], newT["st2"]["makers]"], newT["st2"]["d_price"],
            newT["st3"]["r"], newT["st3"]["score"], newT["st3"]["txns"], newT["st3"]["volume"], newT["st3"]["makers]"], newT["st3"]["d_price"],
            newT["symbol"]
            )''')


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

def toD(row: tuple):
    return (f"D:{row[0]}", ".", {"id": row[0], "address": row[1], "name": row[2], "image": row[3]})

def toT(row: tuple):
    return (f"T:{row[0]}", ".", {"id": row[0], "mint": row[1], "name": row[2], "symbol": row[3], "uri": row[4], "seller_fee_basis_points": row[5],
                                "created": row[6], "verified": row[7], "share": row[8],  "mint_authority": row[9], "supply": row[10], 
                                "decimals": row[11], "supply_real": row[12], "is_initialized": row[13], "freeze_authority": row[14],
                                "image": row[15], "description": row[16], "twitter": row[17], "website": row[18],
                })

def defaultTValue(id, mint: str):
    return (f'{id}', mint, '', '', '', 0, [], [], [], None, 0, 0, 0, True, None, '', '', '', '')

def defaultT(id, mint: str):
    return toT(defaultTValue(id, mint))
               
def mintToId(cur, r, mint: str):
    id = r.hget('H_T', mint)
    if not id:
        id = r.hlen('H_T') + 1
        # print(f"new mint {mint} => {id}")
        r.hset('H_T', mint, id)
        r.json().mset([defaultT(id, mint)])
        # token_info.update_nft(cur, r, id, mint)
        # r.xadd('TOKEN_STREAM', {id: mint})
        r.lpush('L_TOKENS', f'{id},{mint}')
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
        newP = toP((f'{pid}', 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0,
                        split[0], split[1], pool, now()))
        r.json().mset([newP])
        for i in range(env.NUM_DURATIONS):
            r.zadd(f"SS_PS{i}", {newP[2]["id"] : newP[2][f"st{i}"]["score"]}) # type: ignore
        
        r.ts().create(f'TS_P{pid}', retention_msecs=env.DAY*1000)
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_PO{pid}:{i}', retention_msecs=env.RP[i]*1000)    
            r.ts().createrule(f'TS_P{pid}', f'TS_PO{pid}:{i}', aggregation_type="first", bucket_size_msec=env.BD[i])
        
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_PH{pid}:{i}', retention_msecs=env.RP[i]*1000)    
            r.ts().createrule(f'TS_P{pid}', f'TS_PH{pid}:{i}', aggregation_type="max", bucket_size_msec=env.BD[i])
        
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_PL{pid}:{i}', retention_msecs=env.RP[i]*1000)    
            r.ts().createrule(f'TS_P{pid}', f'TS_PL{pid}:{i}', aggregation_type="min", bucket_size_msec=env.BD[i])
        
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_PC{pid}:{i}', retention_msecs=env.RP[i]*1000)    
            r.ts().createrule(f'TS_P{pid}', f'TS_PC{pid}:{i}', aggregation_type="last", bucket_size_msec=env.BD[i])
        
        r.ts().create(f'TS_V{pid}', retention_msecs=env.DAY*1000)
        for i in range(env.NUM_INTERVALS):
            r.ts().create(f'TS_V{pid}:{i}', retention_msecs=env.RP[i]*1000)    
            r.ts().createrule(f'TS_V{pid}', f'TS_V{pid}:{i}', aggregation_type="sum", bucket_size_msec=env.BD[i])

        baseId = mintToId(cur, r, split[0])
        quoteId = mintToId(cur, r, split[1])

        r.sadd(f"S_TP{baseId}", pid) # type: ignore
        r.sadd(f"S_TP{quoteId}", pid) # type: ignore

        # TODO sync with PG
        # insertP(cur, newP)
    else:
        pid = int(pid.decode())
    return pid

def isSol(mint: str):
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
        elif isSol(baseMint):
            price = solPrice
        elif isSol(quoteMint):
            price = solPrice * quoteAmount / baseAmount
        else:
            #TODO
            pass
    return abs(price)
# __app__ = [connect_redis, connect_db]


if __name__ == "__main__":
    # print(getMintAddresses(r, '1'))
    pass