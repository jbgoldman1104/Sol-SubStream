import psycopg
import common

conn = common.connect_db()
cur = conn.cursor()

def query_st(duration: int = 0, skip: int = 0, limit: int = 100):
    cur.execute("SELECT * FROM t_tx", [])
    list = cur.fetchall()
    txs = [(f'TX:{tx["id"]}', path, dict(tx)) for tx in list] # type: ignore
    return []
    # rank = r.zrevrange(f"SS_PS{duration}", skip, skip + limit - 1)
    # print(rank)
    # return r.json().mget([f'P:{t.decode("utf-8")}' for t in rank], ".") # type: ignore
    # # TODO custom sort with PG
    # # return r.json().mget(["token:T1111"], ".")

def query_tx(token: str = "", sort: str = "timestamp", direction = "desc", skip: int = 0, limit: int = 100):
    if not str: return []
    # q = Query(f'@from:{{{token}}}').paging(skip, limit).sort_by(sort, asc = False if direction == "desc" else True)
    # rlt = r.ft("IDX_TX").search(q)
    # t = r.json().get(f"P:{token}")
    # r.zadd('SS_PR', {token: common.now()})
    # return rlt

if __name__ == "__main__":
    rlt = query_st()
