# ---- Init Redis Database from Postgresql for start up. ----
# --- Import Redis ---
from copyreg import constructor
import env
import common
from redis.commands.json.path import Path
# import redis.commands.search.aggregation as aggregations
# import redis.commands.search.reducers as reducers
# from redis.commands.search.field import TextField, NumericField, TagField
# from redis.commands.search.indexDefinition import IndexDefinition, IndexType
# from redis.commands.search.query import NumericFilter, Query

from random import random as rd
from random import randint as rdi

import datetime
import json
from redis.commands.search.field import (
    GeoField,
    GeoShapeField,
    NumericField,
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

# async def read_T():
#     cur.execute("SELECT * FROM t_tx", [])
#     cur.fetchone()
#     for row in cur:
#         yield row

def init_redis():
    r = common.connect_redis()
    if env.USE_PG:
        conn = common.connect_db()
        cur = conn.cursor()
    
    r.xtrim("INIT_COMPLETE", maxlen = 0)
    
    t_start = datetime.datetime.now()
    r.flushall()
    pipe = r.pipeline()
    path = "."
    now = common.now()
    
    
    
    # --- Check PG Table Existence ---
    # sync
    cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s", ('sync',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE sync (
                read_tx_id integer,
                read_p_id integer
                )
            """)
        conn.commit()
    cur.execute("SELECT * FROM sync", [])
    if not bool(cur.rowcount):
        cur.execute("INSERT INTO sync (read_tx_id, read_p_id) VALUES (%s, %s)", (0, 0))
        conn.commit()
    
    # trade
    cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s", ('trade',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE trade (
                "id" int8 NOT NULL DEFAULT nextval('trade_id_seq'::regclass),
                "blockDate" timestamptz(6),
                "blockTime" int4,
                "blockSlot" int4,
                "txId" varchar(90) COLLATE "pg_catalog"."default",
                "signer" varchar(45) COLLATE "pg_catalog"."default",
                "poolAddress" varchar(45) COLLATE "pg_catalog"."default",
                "baseMint" varchar(45) COLLATE "pg_catalog"."default",
                "quoteMint" varchar(45) COLLATE "pg_catalog"."default",
                "baseAmount" float8,
                "quoteAmount" float8,
                "outerProgram" varchar(45) COLLATE "pg_catalog"."default",
                "innerProgram" varchar(45) COLLATE "pg_catalog"."default",
                "baseReserve" float8,
                "quoteReserve" float8
                )
            """)
        conn.commit()
        
    
    
    # --- Import P:, SS_PS ---
    # --- Import TX, EN_TX ---

    
    # r.sadd('EN_TX', *[t[2]["id"] for t in txs])
    pairs = []
    txs = []
    read_tx_id = 0
    read_p_id = 0
    if env.USE_PG:
        # - import TX table from PG -
        # read_tx_id = common.getSyncValue(cur, "read_tx_id", 0)
        # cur.execute("SELECT * FROM trade WHERE id > %s", [read_tx_id])
        # while True:
        #     rows = cur.fetchmany(env.DB_READ_SIZE)
        #     txs = [common.toTx(row) for row in rows]
        #     r.json().mset(txs) # type: ignore
        #     read_tx_id = txs[len(txs)-1][2]["id"]
        #     if len(rows) < env.DB_READ_SIZE: break

        # - import T table from PG -
        # TODO make tokens table to PG and Load
        if env.USE_P_TABLE:
            read_p_id = common.getSyncValue(cur, "read_p_id", 0)
            cur.execute("SELECT * FROM pairs WHERE id > %s", [read_p_id])
            while True:
                rows = cur.fetchmany(env.DB_READ_SIZE)
                pairs = [common.toP(row) for row in rows]
                r.json().mset(pairs) # type: ignore
                # r.hmset('H_T', {})    # TODO
                read_p_id = pairs[len(pairs)-1][2]["id"]
                for i in range(4):
                    r.zadd(f"SS_PS{i}", {t[2]["id"] : t[2][f"st{i}"]["score"] for t in pairs})
                if len(rows) < env.DB_READ_SIZE: break
        
    else:
        pairs = [common.toP((f"T{i}/T{i}", rd() * 10, rd() * 1e8, rd() * 1e13, 0, 
                                            rd() * 100,         rd() * 100, rdi(1, 100000), rd() * 1e6, rdi(1, 1000), rd() * 1e3, 0, 0, 0,
                                            100 + rd() * 1000,  rd() * 100, rdi(1, 100000), rd() * 1e6, rdi(1, 1000), rd() * 1e3, 0, 0, 0,
                                            100 + rd() * 10000, rd() * 100, rdi(1, 100000), rd() * 1e6, rdi(1, 1000), rd() * 1e3, 0, 0, 0,
                                            100 + rd() * 100000, rd() * 100, rdi(1, 100000), rd() * 1e6, rdi(1, 1000), rd() * 1e3, 0, 0, 0,
                                            f"SYMBOL{i}", f"SYMBOL{i}")
               ) for i in range(env.NTEST)]
        r.json().mset(pairs) # type: ignore
        for i in range(4):
            r.zadd(f"SS_PS{i}", {t[2]["id"] : t[2][f"st{i}"]["score"] for t in pairs})

        for i in range(env.NTEST * 5):
            id = common.rtx()
            timestamp = now - rdi(1, 3000) - i//5 * 3000
            txs.append(common.toTx(cur, r, (id, common.rp(), common.rp(), rdi(1,5), rd()*100, rd()* 100, f'{rdi(1, 0xFFFFFFFFFFFFFFFF):X}', timestamp)))
            r.json().mset(txs) # type: ignore

    
    # --- Init SS_BLK, SS_PR ---
    if env.USE_PG:
        # This is done in input_redis.py
        # TODO load from PG
        pass
    else:
        r.zadd('SS_BLK', {f'{txs[i*5][2]["id"]},{txs[i*5 + 1][2]["id"]},{txs[i*5 + 2][2]["id"]}' : now - i * 3000 
                for i in range(len(txs) // 5)})
        r.zadd('SS_PR', {common.rp() : now - i * 3000 * len(txs) // 5 for i in range(len(pairs) * 100)} )

    # --- Create Indexes ---
    r.ft("IDX_P").create_index((TextField("$.id", as_name="id"),
                                # NumericField("$.price", as_name="price", sortable=True),
                                NumericField("$.liq", as_name="liq", sortable=True),
                                NumericField("$.mcap", as_name="mcap", sortable=True),
                                NumericField("$.st0.txns", as_name="txns", sortable=True),
                                NumericField("$.st0.volume", as_name="volume", sortable=True),
                                NumericField("$.st0.makers", as_name="makers", sortable=True),
                                NumericField("$.st0.d_price", as_name="d_price", sortable=True),
                                TagField("$.symbol", as_name="symbol")),
                        definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["P:"]))
    r.ft("IDX_TX").create_index((NumericField("$.id", as_name="id"),
                                 NumericField("$.pid", as_name="pid"),
                                 NumericField("$.blockTime", as_name="blockTime", sortable=True), 
                                #  TagField("$.baseMint", as_name="baseMint"), TagField("$.quiteMint", as_name="quiteMint"),
                                #  NumericField("$.type", as_name="type"),
                                 NumericField("$.baseAmount", as_name="baseAmount"),
                                 TagField("$.signer", as_name="signer")),
                        definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["TX:"]))
    
    
    common.setSyncValue(cur, "read_tx_id", read_tx_id)
    if env.USE_P_TABLE:
        common.setSyncValue(cur, "read_p_id", read_p_id)

    conn.commit()
    conn.close()
    print(f"-- INIT_COMPLETE ---: => {(datetime.datetime.now() - t_start).total_seconds()} s")
    r.xadd("INIT_COMPLETE", {"date": str(datetime.datetime.now())})


if __name__ == "__main__":
    rlt = init_redis()