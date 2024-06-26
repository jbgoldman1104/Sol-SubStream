# ---- Init Redis Database from Postgresql for start up. ----
# --- Import Redis ---
from copyreg import constructor
import env
import common
import os
from redis.commands.json.path import Path
from benchmark import _b
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

def importD(r, filename: str):
    print('-- init process started. --')
    
    if not os.path.exists(filename):
        open(filename, 'x')
    file = open(filename, 'r+')
    # line = fileT.read(1000000).decode()
    rows = []
    if file:
        for line in file:
            if line:
                try:
                    row = json.loads(line)
                    rows.append(common.toD(row))
                    # r.hset('H_D', row[1], row[0])
                    if len(rows) >= 1000:
                        print(f'D:{row[1]}')
                        r.json().mset(rows)
                        rows = []
                except Exception as e:
                    print("input file type error: " + str(e) + ":    " + line)
                    file.write('\n')
    if len(rows) > 0: r.json().mset(rows)
    
def importT(r, filename: str):
    if not os.path.exists(filename):
        open(filename, 'x')
    file = open(filename, 'r+')
    # line = fileT.read(1000000).decode()
    rows = []
    if file:
        for line in file:
            if line:
                try:
                    row = json.loads(line)
                    rows.append(common.toT(row))
                    r.hset('H_T', row[1], row[0])
                    if len(rows) >= 1000:
                        print(f'T:{row[0]}')
                        r.json().mset(rows)
                        rows = []
                except Exception as e:
                    print("input file type error: " + str(e) + ":    " + line)
                    file.write('\n')
    if len(rows) > 0: r.json().mset(rows)
    # ts == line.split('^')

def init_redis():
    r = common.connect_redis()
    if env.USE_PG:
        conn = common.connect_db()
        cur = conn.cursor()
    
    r.xtrim("INIT_COMPLETE", maxlen = 0)
    
    _b('INIT')

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
                "read_tx_id" integer,
                "read_p_id" integer
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
        cur.execute(
        """
            CREATE TABLE trade (
                "id" SERIAL PRIMARY KEY,
                "blockDate" TIMESTAMP,
                "blockTime" INT NOT NULL,
                "blockSlot" INT NOT NULL,
                "txId" VARCHAR(90) NOT NULL,
                "signer" VARCHAR(45) NOT NULL,
                "poolAddress" VARCHAR(45) NOT NULL,
                "baseMint" VARCHAR(45) NOT NULL,
                "quoteMint" VARCHAR(45) NOT NULL,
                "baseAmount" float8 NOT NULL,
                "quoteAmount" float8 NOT NULL,
                "instructionType" VARCHAR(20),
                "outerProgram" VARCHAR(45),
                "innerProgram" VARCHAR(45),
                "baseReserve" float8 NOT NULL,
                "quoteReserve" float8 NOT NULL);
        """
        )
        conn.commit()
        
    # --- Import D:, H_D ---
    importD(r, env.FILENAME_D)

    # --- Import T:, H_T ---
    importT(r, env.FILENAME_T)
    importT(r, env.FILENAME_FailedT)
    
    
    # --- Import P:, SS_PScore ---
    # --- Import TX:, EN_TX ---

    
    # r.sadd('EN_TX', *[t[2]["id"] for t in txs])
    pairs = []
    txs = []
    read_tx_id = 0
    read_p_id = 0
    if env.USE_PG:
        pass
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
        # if env.USE_P_TABLE:
        #     read_p_id = common.getSyncValue(cur, "read_p_id", 0)
        #     cur.execute("SELECT * FROM pairs WHERE id > %s", [read_p_id])
        #     while True:
        #         rows = cur.fetchmany(env.DB_READ_SIZE)
        #         pairs = [common.toP(row) for row in rows]
        #         r.json().mset(pairs) # type: ignore
        #         # r.hmset('H_T', {})    # TODO
        #         read_p_id = pairs[len(pairs)-1][2]["id"]
        #         for i in range(env.NUM_DURATIONS):
        #             r.zadd(f"SS_PScore{i}", {t[2]["id"] : t[2][f"st{i}"]["score"] for t in pairs})
        #         if len(rows) < env.DB_READ_SIZE: break
        
    
    
    # --- Init SS_BLK, SS_PR ---
    if env.USE_PG:
        # This is done in input_redis.py
        # TODO load from PG
        pass
   

    # --- Create Indexes ---
    r.ft("IDX_T").create_index((TextField("$.name", as_name="name"),
                                TextField("$.symbol", as_name="symbol")),
                        definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["T:"]))
    r.ft("IDX_P").create_index((NumericField("$.id", as_name="id"),
                                # NumericField("$.price", as_name="price", sortable=True),
                                
                                TextField("$.symbol", as_name="symbol")),
                        definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["P:"]))
    r.ft("IDX_TX").create_index((NumericField("$.pid", as_name="pid"),
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
    r.xadd("INIT_COMPLETE", {"date": str(datetime.datetime.now())})

    _b()

if __name__ == "__main__":
    rlt = init_redis()