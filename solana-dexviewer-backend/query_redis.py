import env
import common
import query_pg
from redis.commands.search.query import Query
import json

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


def query_st(duration: int = 0, sort: str = "score", skip: int = 0, limit: int = 100):
    rank = r.zrevrange(f"SS_PS{duration}", skip, skip + limit - 1)
    # print(rank)
    if rank:
        rlt = r.json().mget([f'P:{t.decode()}' for t in rank], ".") # type: ignore
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
        return rlt
    else:
        return []
    # TODO custom sort with PG
    # return r.json().mget(["token:T1111"], ".")

def query_tx(pair: str = "", sort: str = "blockTime", direction = "desc", skip: int = 0, limit: int = 100):
    if not str: return []
    pid = r.hget('H_P', pair)
    if not pid: return []
    pid = pid.decode() # type: ignore
    q = Query(f'@pid:[{pid} {pid}]').paging(skip, limit).sort_by(sort, asc = False if direction == "desc" else True)
    rlt = r.ft("IDX_TX").search(q)
    # t = r.json().get(f"P:{pid}")
    r.zadd('SS_PR', {f'{pid}': common.now()})
    rows = [json.loads(doc['json']) for doc in rlt.docs] # type: ignore
    data = []
    for row in rows:
        data.append({
            "date": row['blockTime'],
            "type": row['type'], 
            "usd": 0 if row['price'] == 0 else abs(row['baseAmount'] * row['price']),
            "baseAmount": row['baseAmount'],
            "quoteAmount": row['quoteAmount'],
            "price": row['price'],
            "maker": row['signer'],
            "txId": row['txId'],
        })
    
    split = pair.split('/')
    pids = r.hmget('H_T', [split[0], split[1]])
    pids = [item.decode() for item in pids] # type: ignore
    names = r.json().mget([f'T:{pids[0]}', f'T:{pids[1]}'], "$.symbol") # type: ignore
    rlt = {
        "baseName": names[0] if names[0] else split[0],
        "quoteName": names[1] if names[1] else split[1],
        "data": data
    }
    return rlt

if __name__ == "__main__":
    print(query_tx('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/So11111111111111111111111111111111111111112'))