import env
import common
import query_pg
from redis.commands.search.query import Query
import json
from benchmark import _b

r = common.connect_redis()
conn = common.connect_db()
cur = conn.cursor()

def convert_to_custom_format(number):
    # Convert number to string and split into integer and fractional parts
    integer_part, fractional_part = str(number).split('.')
    
    # Check how many leading zeros in the fractional part
    leading_zeros = len(fractional_part) - len(fractional_part.lstrip('0'))
    
    # Get the subscript character for the number of leading zeros
    subscript_char = ''.join(chr(8272 + int(digit)) for digit in str(leading_zeros))
    
    # Construct the final string with the custom format
    result = f"{integer_part}.0{subscript_char}{fractional_part[leading_zeros:]}"
    
    return result

# {
#   "type": "PAIRS_DATA",
#   "data": [{
#     "base" {
#       "Name": "Wrapped SOL",
#       "Symbol": SOL,
#       "Uri": ,
#       "Supply": 24.555908821439385,
#       "Image": "ohlcv",
#       "Description": "1m",
#       "Twitter": 1675506120,
#       "Website: 51.838008518,
#     }

#     "quoteName": "SOL-USDC",
#     "address": "7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJnm"
#   }]
# }

def get_pairs(pids):
    if not pids: return []
    rlt = r.json().mget([f'P:{t.decode()}' for t in pids], ".") # type: ignore
    tids = []
    for p in rlt:
        tids.append(common.mintToId(cur, r, p['baseMint'])) # type: ignore
        tids.append(common.mintToId(cur, r, p['quoteMint'])) # type: ignore
    ts = r.json().mget([f"T:{id}" for id in tids], ".")
    for i in range(len(rlt)): # type: ignore
        if ts[2*i]:
            rlt[i]['baseName'] = ts[2*i]['name'] # type: ignore
            rlt[i]['baseSymbol'] = ts[2*i]['symbol'] # type: ignore
            rlt[i]['baseUri'] = ts[2*i]['uri'] # type: ignore
            rlt[i]['baseSupply'] = ts[2*i]['supply_real'] # type: ignore
            rlt[i]['baseImage'] = ts[2*i]['image'] # type: ignore
            rlt[i]['baseDescription'] = ts[2*i]['description'] # type: ignore
            rlt[i]['baseTwitter'] = ts[2*i]['twitter'] # type: ignore
            rlt[i]['baseWebsite'] = ts[2*i]['website'] # type: ignore
            
            rlt[i]['quoteName'] = ts[2*i+1]['name'] # type: ignore
            rlt[i]['quoteSymbol'] = ts[2*i+1]['symbol'] # type: ignore
            rlt[i]['quoteUri'] = ts[2*i+1]['uri'] # type: ignore
            rlt[i]['quoteSupply'] = ts[2*i+1]['supply_real'] # type: ignore
            rlt[i]['quoteImage'] = ts[2*i+1]['image'] # type: ignore
            rlt[i]['quoteDescription'] = ts[2*i+1]['description'] # type: ignore
            rlt[i]['quoteTwitter'] = ts[2*i+1]['twitter'] # type: ignore
            rlt[i]['quoteWebsite'] = ts[2*i+1]['website'] # type: ignore


            if not rlt[i]['baseImage']: rlt[i]['baseImage'] = '' # type: ignore
            if not rlt[i]['quoteImage']: rlt[i]['quoteImage'] = '' # type: ignore
    return {
        'type':'PAIRS_DATA', 
        'data': [{'type': 'PAIR_DATA', 'data': item} for item in rlt]
        }

def query_wrap(ns, data):
    if not data: return {}
    js = json.loads(data)
    if not js: return {}
    if js['type'] == 'SUBSCRIBE_RANK':
        return query_st(js['data']['duration'], js['data']['skip'], js['data']['limit'], js['data']['sort'], js['data']['sort_dir'])
    # elif js == env.NS_TX:
    #     return query_tx(data['duration'], data['skip'], data['limit'], data['sort'], data['sort_dir'])
    
def query_st(duration: int = 0, skip: int = 0, limit: int = 100, sort: str = "score", sort_dir: str = "desc"):
    _b('query_st')
    
    if sort == "score": set = f"SS_PS{duration}"
    elif sort == "price": set = f"SS_PP"
    elif sort == "volume": set = f"SS_PV{duration}"
    elif sort == "txns": set = f"SS_PX{duration}"
    elif sort == "ratio": set = f"SS_PPR{duration}"
    elif sort == "liq": set = f"SS_PL"
    elif sort == "mcap": set = f"SS_PM"
    else: return []
        
    if sort_dir == "desc":
        rank = r.zrevrange(set, skip, skip + limit - 1)    
    else:
        rank = r.zrange(set, skip, skip + limit - 1)    
        
    # print(rank)
    if rank:
        rlt = get_pairs(rank)
        _b()
        return rlt
    else:
        return []
    # TODO custom sort with PG
    # return r.json().mget(["token:T1111"], ".")

# {
#   type: 'TXS_DATA',
#   data: {
#     blockUnixTime: 1714107255,
#     owner: 'TyrZ6SDVQGdMpnYtAgKGocvi1w1mdffhZENf1knyeqy',
#     source: 'raydium',
#     txHash: '3XtCydTzZPJNGr9qQ83rvkKyGQHMQcUa3QpgBZoz97i3VkRGL3e8UBhM7JUnprwbcgWXeHXST74NeaEE4vjWeEME',
#     alias: null,
#     isTradeOnBe: false,
#     platform: 'YmirFH6wUrtUMUmfRPZE7TcnszDw689YNWYrMgyB55N',
#     volumeUSD: 31.569239727896086,
#     from: {
#       symbol: 'SOL',
#       decimals: 9,
#       address: 'So11111111111111111111111111111111111111112',
#       amount: 219852856,
#       type: 'transfer',
#       typeSwap: 'from',
#       uiAmount: 0.219852856,
#       price: null,
#       nearestPrice: 143.5925841595439,
#       changeAmount: -219852856,
#       uiChangeAmount: -0.219852856,
#       icon: null
#     },
#     to: {
#       symbol: 'TOM',
#       decimals: 9,
#       address: '2rJSfgxoWP7h3rw3hDUF7HPToY3exb6FdH9xFBg7TeQk',
#       amount: 650244687263,
#       type: 'transfer',
#       typeSwap: 'to',
#       feeInfo: null,
#       uiAmount: 650.244687263,
#       price: 0.048549784944459676,
#       nearestPrice: 0.048420900217275124,
#       changeAmount: 650244687263,
#       uiChangeAmount: 650.244687263,
#       icon: null
#     }
#   }
# }
def query_tx(pool: str = "", sort: str = "blockTime", direction = "desc", skip: int = 0, limit: int = 100):
    _b('query_tx')
    if not pool: return []
    pid = r.hget('H_P', pool)
    if not pid: return []
    pid = pid.decode() # type: ignore
    query = Query(f'@pid:[{pid} {pid}]').paging(skip, limit).sort_by(sort, asc = False if direction == "desc" else True)
    rlt = r.ft("IDX_TX").search(query)
    # t = r.json().get(f"P:{pid}")
    r.zadd('SS_PR', {f'{pid}': common.now()})
    rows = [json.loads(doc['json']) for doc in rlt.docs] # type: ignore
    data = [] # TODO txId duplication?
    for row in rows:
        data.append({
            "date": row['blockTime'],
            "type": row['type'], 
            "usd": 0 if row['price'] == 0 else abs(row['baseAmount'] * row['price']),
            "baseAmount": abs(row['baseAmount']),
            "quoteAmount": abs(row['quoteAmount']),
            "price": row['price'],
            "maker": row['signer'],
            "txId": row['txId'],
        })
    
    # split = pair.split('/')
    # TODO mintAddress.
    split = common.getMintAddresses(r, pid)
    tids = r.hmget('H_T', [split[0], split[1]])
    tids = [item.decode() for item in tids] # type: ignore
    names = r.json().mget([f'T:{tids[0]}', f'T:{tids[1]}'], "$.symbol") # type: ignore
    rlt = {
        "baseName": names[0] if names[0] and names[0][0] else split[0],
        "quoteName": names[1] if names[1] and names[1][0] else split[1],
        "data": data
    }
    _b()
    return rlt

# {
#   "type": "PRICE_DATA",
#   "data": {
#     "o": 24.552070604303985,
#     "h": 24.555908821439385,
#     "l": 24.552070604303985,
#     "c": 24.555908821439385,
#     "eventType": "ohlcv",
#     "type": "1m",
#     "unixTime": 1675506120,
#     "v": 51.838008518,
#     "symbol": "SOL-USDC",
#     "address": "7qbRF6YsyGuLUVs6Y1q64bdVrfe4ZcUUz1JRdoVNUJnm"
#   }
# }
def query_chart(pool: str = "", t_from: int = 0, t_to: int = 0, interval: int = 0):
    _b('query_chart')
    if not pool or interval < 0 or interval > 7: return []
    
    pid = r.hget('H_P', pool)
    if not pid: return []
    pid = pid.decode() # type: ignore
    
    if t_to == 0:
        rows1 = r.ts().revrange(f'TS_PO{pid}:{interval}', '-', '+', 30)
        rows1.reverse()
        rows2 = r.ts().revrange(f'TS_PH{pid}:{interval}', '-', '+', 30)
        rows2.reverse()
        rows3 = r.ts().revrange(f'TS_PL{pid}:{interval}', '-', '+', 30)
        rows3.reverse()
        rows4 = r.ts().revrange(f'TS_PC{pid}:{interval}', '-', '+', 30)
        rows4.reverse()
        
    else:
        t_from *= 1000
        t_to *= 1000
        # t_from -= common.now() - 1718392375000
        # t_to -= common.now() - 1718392375000
        rows1 = r.ts().range(f'TS_PO{pid}:{interval}', t_from, t_to)
        rows2 = r.ts().range(f'TS_PH{pid}:{interval}', t_from, t_to)
        rows3 = r.ts().range(f'TS_PL{pid}:{interval}', t_from, t_to)
        rows4 = r.ts().range(f'TS_PC{pid}:{interval}', t_from, t_to)
        
    data = []
    for i in range(len(rows1)):
        data.append({"time": rows1[i][0], 
                     "open": rows1[i][1], 
                     "high": rows2[i][1], 
                     "low": rows3[i][1], 
                     "close": rows4[i][1],
                     "volume": rows4[i][1]})
    _b()
    rlt = {
        "data": data
    }
    return rlt

def search_pair(q: str = "", skip: int = 0, limit: int = 10):
    _b('search_pair')
    if not q: return {}
    pids = set()
    tids = []
    pid = pid = r.hget('H_P', q) #common.poolToId(cur, r, q)
    if pid:
        pids.add(pid)
        # return {"data": [r.get(f'P:{pid}')]}
    else:
        tid = r.hget('H_T', q) #common.mintToId(cur, r, q)
        if tid:
            tids.append(int(tid.decode()))
        else:
            query = Query(q).paging(skip, limit)
            rlt = r.ft("IDX_T").search(query)
            tids = [json.loads(doc['json'])['id'] for doc in rlt.docs] # type: ignore
        for tid in tids:
            # pids |= set(int(pid.decode()) for pid in r.smembers(f'S_TP{tid}'))  #set(r.zrangebyscore('SS_TP', tid, tid))
            pids |= r.smembers(f'S_TP{tid}')

    rlt = get_pairs(list(pids)[skip: skip+limit])
    _b()
    return rlt

if __name__ == "__main__":
    aa = query_wrap(env.NS_ST, '{"type":"SUBSCRIBE_RANK","data":{"duration":0,"sort":"score","sort_dir":"desc","skip":0,"limit":50}}')
    bb = 1
    # print(search_pair('2q9AQurvcdjCyxArPmRt26rXx3NBc2RrcDh2grx7aWZb'))
    # print(common.getMintAddresses(r, '1'))
    # print(query_chart('A1BBtTYJd4i3xU8D6Tc2FzU6ZN4oXZWXKZnCxwbHXr8x', 1718629188, 1718727888, 2))
    # print(query_chart('2mCaQrTySFYQtmrKxQxMHBdqHnm2mTx9hMRUbFuNz4Jx', 0, 0, 2))
    # print(query_tx('4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg'))