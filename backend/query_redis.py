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

def query_wrap(ns, js, payload = None):
    param = js['data']
    if js['type'] == 'GET_PAIRS':
        return query_st(param['duration'], param['skip'], param['limit'], param['sort'], param['sort_dir'])
    elif js['type'] == 'SUBSCRIBE_PAIRS':
        return query_st(param['duration'], param['skip'], param['limit'], param['sort'], param['sort_dir'])
    elif js['type'] == 'SUBSCRIBE_PAIRS_SEARCH':
        return search_pair(param['search'], param['skip'], param['limit'])
    elif js['type'] == 'TXS_DATA_HISTORICAL':
        return query_tx_historical(param['pool'], param['filter'], param['skip'], param['limit'])
    elif js['type'] == 'TXS_DATA_REALTIME':
        return query_tx_realtime(payload, param['pool'], param['filter'])
    elif js['type'] == 'PRICE_DATA_HISTORICAL':
        return query_price_historical(param['address'], param['address_type'], param['type'], param['time_from'], param['time_to'])
    elif js['type'] == 'SUBSCRIBE_PRICE':
        return query_price_realtime(param['address'], param['address_type'], param['type'])
    
   
def get_pairs(pids):
    if not pids: return { 'type':'PAIRS_DATA', 'data': [] }
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
#   
#   data: [{
#        blockUnixTime: 1714107255,
#        owner: 'TyrZ6SDVQGdMpnYtAgKGocvi1w1mdffhZENf1knyeqy',
#        source: 'raydium',
#        txHash: '3XtCydTzZPJNGr9qQ83rvkKyGQHMQcUa3QpgBZoz97i3VkRGL3e8UBhM7JUnprwbcgWXeHXST74NeaEE4vjWeEME',
#        alias: null,
#        isTradeOnBe: false,
#        platform: 'YmirFH6wUrtUMUmfRPZE7TcnszDw689YNWYrMgyB55N',
#        volumeUSD: 31.569239727896086,
#        from: {
#          symbol: 'SOL',
#          decimals: 9,
#          address: 'So11111111111111111111111111111111111111112',
#          amount: 219852856,
#          type: 'transfer',
#          typeSwap: 'from',
#          uiAmount: 0.219852856,
#          price: null,
#          nearestPrice: 143.5925841595439,
#          changeAmount: -219852856,
#          uiChangeAmount: -0.219852856,
#          icon: null
#        },
#        to: {
#          symbol: 'TOM',
#          decimals: 9,
#          address: '2rJSfgxoWP7h3rw3hDUF7HPToY3exb6FdH9xFBg7TeQk',
#          amount: 650244687263,
#          type: 'transfer',
#          typeSwap: 'to',
#          feeInfo: null,
#          uiAmount: 650.244687263,
#          price: 0.048549784944459676,
#          nearestPrice: 0.048420900217275124,
#          changeAmount: 650244687263,
#          uiChangeAmount: 650.244687263,
#          icon: null
#        }
#    }]
# }
def query_tx_historical(address: str = "", filter = "", skip: int = 0, limit: int = 100):
    _b('query_tx_historical')
    if not address: return []
    pid = r.hget('H_P', address)
    if not pid: return []
    pid = pid.decode() # type: ignore
    query = Query(f'@pid:[{pid} {pid}]').paging(skip, limit).sort_by("blockTime", asc = False)
    rlt = r.ft("IDX_TX").search(query)
    # t = r.json().get(f"P:{pid}")
    r.zadd('SS_PR', {f'{pid}': common.now()})
    rows = [json.loads(doc['json']) for doc in rlt.docs] # type: ignore
    
    # TODO mintAddress.
    split = common.getMintAddresses(r, pid)
    tids = r.hmget('H_T', [split[0], split[1]])
    tids = [item.decode() for item in tids] # type: ignore
    ts = r.json().mget([f'T:{tids[0]}', f'T:{tids[1]}'], ".") # type: ignore
    
    data = [] # TODO txId duplication?
    for row in rows:
        dex = r.json().get(f'D:{row["outerProgram"]}')
        data.append({
            "blockUnixTime": row['blockTime'],
            "owner": row['signer'],
            "source": '' if not dex else dex['name'],
            "txHash": row['txId'],
            "alias": None,  # TODO
            "isTradeOnBe": False,
            "platform": row['outerProgram'],
            "volumeUSD": 0 if row['price'] == 0 else abs(row['baseAmount'] * row['price']),
            "from": {
                "symbol": ts[0]['symbol'] if ts[0]['symbol'] else ts[0]['mint'],
                "decimals": ts[0]['decimals'],
                "address": ts[0]['mint'],
                "amount": abs(row['baseAmount']),
                "type": row['type'],
                "typeSwap": row['instructionType'],
                "uiAmount": abs(row['baseAmount']) / (10.0 ** ts[0]['decimals']),
                "price": row['price'],
                "nearestPrice": row['price'], # ?
                "changeAmount": row['baseAmount'],
                "uiChangeAmount": row['baseAmount'] / (10.0 ** ts[0]['decimals']),
                "icon": ts[0]['image']
            },
            "to": {
                "symbol": ts[1]['symbol'] if ts[1]['symbol'] else ts[1]['mint'],
                "decimals": ts[1]['decimals'],
                "address": ts[1]['mint'],
                "amount": abs(row['quoteAmount']),
                "type": row['type'], #"Buy" if row['type'] == "Sell" else "Sell",
                "typeSwap": row['instructionType'],
                "uiAmount": abs(row['quoteAmount']) / (10.0 ** ts[1]['decimals']),
                "price": row['price'] * abs(row['baseAmount'] / row['quoteAmount']),
                "nearestPrice": row['price'] * abs(row['baseAmount'] / row['quoteAmount']), # ?
                "changeAmount": row['quoteAmount'],
                "uiChangeAmount": row['quoteAmount'] / (10.0 ** ts[1]['decimals']),
                "icon": ts[1]['image']
            },
        })
    
    # split = pair.split('/')
    
    rlt = {
        "type": "TXS_DATA_HISTORICAL",
        "baseSymbol": ts[0]['symbol'] if ts[0]['symbol'] and ts[0]['symbol'] else split[0],
        "quoteSymbol": ts[1]['symbol'] if ts[1]['symbol'] and ts[1]['symbol'] else split[1],
        "data": data
    }
    _b()
    return rlt

def query_tx_realtime(payload, address: str = "", filter = "", skip: int = 0, limit: int = 100):
    _b('query_tx_realtime')
    if not address or not payload: return {}
    if address not in payload: return {}
    rows = payload[address]
    
    pid = r.hget('H_P', address)
    if not pid: return []
    pid = pid.decode() # type: ignore
       
    # TODO mintAddress.
    split = common.getMintAddresses(r, pid)
    tids = r.hmget('H_T', [split[0], split[1]])
    tids = [item.decode() for item in tids] # type: ignore
    ts = r.json().mget([f'T:{tids[0]}', f'T:{tids[1]}'], ".") # type: ignore
    
    data = [] # TODO txId duplication?
    for row in rows:
        dex = r.json().get(f'D:{row["outerProgram"]}')
        data.append({
            "blockUnixTime": row['blockTime'],
            "owner": row['signer'],
            "source": '' if not dex else dex['name'],
            "txHash": row['txId'],
            "alias": None,  # TODO
            "isTradeOnBe": False,
            "platform": row['outerProgram'],
            "volumeUSD": 0 if row['price'] == 0 else abs(row['baseAmount'] * row['price']),
            "from": {
                "symbol": ts[0]['symbol'] if ts[0]['symbol'] else ts[0]['mint'],
                "decimals": ts[0]['decimals'],
                "address": ts[0]['mint'],
                "amount": abs(row['baseAmount']),
                "type": row['type'],
                "typeSwap": row['instructionType'],
                "uiAmount": abs(row['baseAmount']) / (10.0 ** ts[0]['decimals']),
                "price": row['price'],
                "nearestPrice": row['price'], # ?
                "changeAmount": row['baseAmount'],
                "uiChangeAmount": row['baseAmount'] / (10.0 ** ts[0]['decimals']),
                "icon": ts[0]['image']
            },
            "to": {
                "symbol": ts[1]['symbol'] if ts[1]['symbol'] else ts[1]['mint'],
                "decimals": ts[1]['decimals'],
                "address": ts[1]['mint'],
                "amount": abs(row['quoteAmount']),
                "type": row['type'], #"Buy" if row['type'] == "Sell" else "Sell",
                "typeSwap": row['instructionType'],
                "uiAmount": abs(row['quoteAmount']) / (10.0 ** ts[1]['decimals']),
                "price": row['price'] * abs(row['baseAmount'] / row['quoteAmount']),
                "nearestPrice": row['price'] * abs(row['baseAmount'] / row['quoteAmount']), # ?
                "changeAmount": row['quoteAmount'],
                "uiChangeAmount": row['quoteAmount'] / (10.0 ** ts[1]['decimals']),
                "icon": ts[1]['image']
            },
        })
    
    # split = pair.split('/')
    
    rlt = {
        "type": "TXS_DATA_REALTIME",
        "baseSymbol": ts[0]['symbol'] if ts[0]['symbol'] and ts[0]['symbol'] else split[0],
        "quoteSymbol": ts[1]['symbol'] if ts[1]['symbol'] and ts[1]['symbol'] else split[1],
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
def query_price_realtime(address: str = "", address_type: str = "pair", type: str = "15m"):
    _b('query_price_realtime')
    interval = env.INTERVALS[type]
    if not address or not interval: return []

    pid = r.hget('H_P', address)
    if not pid: return []
    pid = pid.decode() # type: ignore
    
    o = r.ts().get(f'TS_PO:{pid}:{interval}', latest = True) or (0, 0)
    h = r.ts().get(f'TS_PH:{pid}:{interval}', latest = True) or (0, 0)
    l = r.ts().get(f'TS_PL:{pid}:{interval}', latest = True) or (0, 0)
    c = r.ts().get(f'TS_PC:{pid}:{interval}', latest = True) or (0, 0)
    v = r.ts().get(f'TS_PV:{pid}:{interval}', latest = True) or (0, 0)
    
    symbols = ['A', 'B'] #common.getSymbols(r, pid)
    pair_symbol = symbols[0] + '-' + symbols[1]
    _b()
    return {
        "type": "PRICE_DATA",
        "data": {
            "unixTime": o[0], 
            "o": o[1], 
            "h": h[1], 
            "l": l[1], 
            "c": c[1],
            "v": v[1],
            "eventType": "ohlcv",
            "type": type,
            "symbol": pair_symbol,
            "address": address
        }
    }
    
    
def query_price_historical(address: str = "", address_type: str = "pair", type: str = '15m', time_from: int = 0, time_to: int = 0):
    _b('query_price_historical')
    interval = env.INTERVALS[type]
    if not address or not interval: return {}
    
    pid = r.hget('H_P', address)
    if not pid: return {}
    pid = pid.decode() # type: ignore

    rows1 = r.ts().range(f'TS_PO:{pid}:{interval}', time_from, time_to)
    if not rows1:
        last = r.ts().get(f'TS_PO:{pid}:{interval}', latest = True)
        if not last or time_to < last[0]: return {
            "type": 'PRICE_DATA_HISTORICAL',
            "data": []
        }
        time_from += last[0] - time_to
        time_to = last[0]
        rows1 = r.ts().range(f'TS_PO:{pid}:{interval}', time_from, time_to)
    rows2 = r.ts().range(f'TS_PH:{pid}:{interval}', time_from, time_to)
    rows3 = r.ts().range(f'TS_PL:{pid}:{interval}', time_from, time_to)
    rows4 = r.ts().range(f'TS_PC:{pid}:{interval}', time_from, time_to)
    rows5 = r.ts().range(f'TS_PV:{pid}:{interval}', time_from, time_to)
        
    symbols = common.getSymbols(r, pid)
    pair_symbol = symbols[0] + '-' + symbols[1]
    data = []
    for i in range(len(rows1)):
        data.append({"unixTime": rows1[i][0], 
                     "o": rows1[i][1], 
                     "h": rows2[i][1], 
                     "l": rows3[i][1], 
                     "c": rows4[i][1],
                     "v": rows5[i][1],
                     "eventType": "ohlcv",
                     "type": type,
                     "symbol": pair_symbol,
                     "address": address})
    _b()
    
    rlt = {
        "type": 'PRICE_DATA_HISTORICAL',
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
    # print(search_pair('2q9AQurvcdjCyxArPmRt26rXx3NBc2RrcDh2grx7aWZb'))
    # print(common.getMintAddresses(r, '1'))
    # print(query_chart('A1BBtTYJd4i3xU8D6Tc2FzU6ZN4oXZWXKZnCxwbHXr8x', 1718629188, 1718727888, 2))
    # print(query_chart('2mCaQrTySFYQtmrKxQxMHBdqHnm2mTx9hMRUbFuNz4Jx', 0, 0, 2))
    # print(query_tx('4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg'))
    pass