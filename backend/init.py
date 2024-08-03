# ---- Init Redis Database from Postgresql for start up. ----
# --- Import Redis ---
from copyreg import constructor
import env
import common
import os
from redis.commands.json.path import Path
from benchmark import _b
from random import random as rd
from random import randint as rdi
import redis

import input_pg

import datetime
import json
from redis.commands.search.field import (NumericField, TagField, TextField, )
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

r = common.connect_redis()
if env.USE_PG:
    conn = common.connect_db()
    cur = conn.cursor()
        
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
                    if len(rows) >= 1:
                        print(f'D:{row[1]}')
                        # r.json().mset(rows)
                        input_pg.write_dexes(cur, rows)
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
                        # r.json().mset(rows)
                        input_pg.write_tokens(cur, rows)
                        rows = []
                except Exception as e:
                    print("input file type error: " + str(e) + ":    " + line)
                    file.write('\n')
    if len(rows) > 0: r.json().mset(rows)
    # ts == line.split('^')


def init_redis():
    print('-- init_redis process started. --')
    # r.xtrim("INIT_COMPLETE", maxlen = 0)
    _b('INIT')

    # r.flushall()
    pipe = r.pipeline()
    path = "."
    now = common.now()
    
    # --- Check PG Table Existence ---
    qExists = "SELECT * FROM information_schema.tables WHERE table_name=%s"
    # - sync -
    cur.execute(qExists, ('sync',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE sync ("read_tx_id" INT, "read_p_id" INT)
            """)
        common.setSyncValue(cur, "read_tx_id", 0)
        if env.USE_P_TABLE:
            common.setSyncValue(cur, "read_p_id", 0)

    cur.execute("SELECT * FROM sync", [])
    if not bool(cur.rowcount):
        cur.execute("INSERT INTO sync (read_tx_id, read_p_id) VALUES (%s, %s)", (0, 0))
    
   
    # - trade -
    cur.execute(qExists, ('trade',))
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
                "quoteReserve" float8 NOT NULL,
                "pid" INT,
                "type" VARCHAR(10),
                "price" float8
                );
        """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blockTime ON \"trade\" (\"blockTime\")")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_baseAmount ON \"trade\" (\"baseAmount\")")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quoteAmount ON \"trade\" (\"quoteAmount\")")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_signer ON \"trade\" (\"signer\")")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pid ON \"trade\" (\"pid\")")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_type ON \"trade\" (\"type\")")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_price ON \"trade\" (\"price\")")


    # - tokens -
    cur.execute(qExists, ('tokens',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE tokens (
                "id" INT PRIMARY KEY,
                "mint" VARCHAR(45) NOT NULL,
                "name" VARCHAR(50),
                "symbol" VARCHAR(20),
                "uri" TEXT,
                "seller_fee_basis_points" float8,
                "creators" VARCHAR(255),
                "verified" VARCHAR(255),
                "share" VARCHAR(255),
                "mint_authority" VARCHAR(255),
                "supply" float8,
                "decimals" INT,
                "supply_real" float8,
                "is_initialized" BOOL,
                "free_authority" VARCHAR(255),
                "image" TEXT,
                "description" TEXT,
                "twitter" VARCHAR(255),
                "website" TEXT,
                
                "holders" INT,
                "created" INT
                )
            """)
        # cur.execute("CREATE INDEX IF NOT EXISTS idx_price ON \"trade\" (\"price\")")
                        
    # - pairs -
    cur.execute(qExists, ('pairs',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE pairs (
                "id" INT PRIMARY KEY,
                "price" float8,
                "liq" float8,
                "mcap" float8,
                "cSupply" float8,
                "tSupply" float8,
                "baseMint" VARCHAR(45),
                "quoteMint" VARCHAR(45),
                "poolAddress" VARCHAR(45),
                "created" INT,
                "baseSymbol" VARCHAR(20),
                "quoteSymbol" VARCHAR(20),
                "baseName" VARCHAR(50),
                "quoteName" VARCHAR(50),
                "dex" VARCHAR(45),
                "dexImage" VARCHAR(255),
                "outerProgram" VARCHAR(45),
                "holders" INT,
                "r" INT, "txns" INT, "buys" INT, "sells" INT, "volume" float8, "buyVolume" float8, "sellVolume" float8, "makers" INT, "buyers" INT, "sellers" INT,
                "r0" INT, "score0" float8, "txns0" INT, "buys0" INT, "sells0" INT, "volume0" float8, "buyVolume0" float8, "sellVolume0" float8, "makers0" INT, "buyers0" INT, "sellers0" INT, "d_price0" float8,
                "r1" INT, "score1" float8, "txns1" INT, "buys1" INT, "sells1" INT, "volume1" float8, "buyVolume1" float8, "sellVolume1" float8, "makers1" INT, "buyers1" INT, "sellers1" INT, "d_price1" float8,
                "r2" INT, "score2" float8, "txns2" INT, "buys2" INT, "sells2" INT, "volume2" float8, "buyVolume2" float8, "sellVolume2" float8, "makers2" INT, "buyers2" INT, "sellers2" INT, "d_price2" float8,
                "r3" INT, "score3" float8, "txns3" INT, "buys3" INT, "sells3" INT, "volume3" float8, "buyVolume3" float8, "sellVolume3" float8, "makers3" INT, "buyers3" INT, "sellers3" INT, "d_price3" float8
                )
            """)
    
    # - wallets -
    cur.execute(qExists, ('wallets',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE wallets (
                "wid" INT,
                "address" VARCHAR(45),
                "tid" INT,
                "buy" float8,
                "sell" float8,
                "remain" float8,
                "buyUSD" float8,
                "sellUSD" float8,
                "lastTx" INT,
                CONSTRAINT "wid_tid" UNIQUE ("wid", "tid")
                )
            """)
    
    # - dexes -
    cur.execute(qExists, ('dexes',))
    if not bool(cur.rowcount):
        cur.execute("""
            CREATE TABLE dexes (
                "id" INT PRIMARY KEY,
                "address" VARCHAR(45),
                "name" VARCHAR(50),
                "image" VARCHAR(255)
                )
            """)
    conn.commit()

    # --------------------- Import Data From PG ---------------------
    _, keys = r.scan(match='TX:*', count=1)
    if len(keys) == 0:
        input_pg.read_txs(cur, r)
    if not r.exists('H_D'):
        input_pg.read_dexes(cur, r)
    if not r.exists('H_T'):
        input_pg.read_tokens(cur, r)
    if not r.exists('H_P'):
        input_pg.read_pairs(cur, r)
    if not r.exists('H_W'):
        input_pg.read_wallets(cur, r)
    

    # --- Import D:, H_D ---
    # importD(r, env.FILENAME_D)

    # --- Import T:, H_T ---
    # importT(r, env.FILENAME_T)
    # importT(r, env.FILENAME_FailedT)
    
    
    # --- Import P:, SS_PScore ---
    # --- Import TX:, EN_TX ---



    # --- Create Indexes ---
    if not common.indexExists(r, "IDX_T"):
        r.ft("IDX_T").create_index((TextField("$.name", as_name="name"),
                                    TextField("$.symbol", as_name="symbol")),
                            definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["T:"]))
    if not common.indexExists(r, "IDX_P"):
        r.ft("IDX_P").create_index((NumericField("$.id", as_name="id"),
                                    # NumericField("$.price", as_name="price", sortable=True),
                                    TextField("$.symbol", as_name="symbol")),
                            definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["P:"]))
    if not common.indexExists(r, "IDX_TX"):
        r.ft("IDX_TX").create_index((NumericField("$.pid", as_name="pid"),
                                    NumericField("$.blockTime", as_name="blockTime", sortable=True), 
                                    #  TagField("$.baseMint", as_name="baseMint"), TagField("$.quiteMint", as_name="quiteMint"),
                                    #  NumericField("$.type", as_name="type"),
                                    NumericField("$.baseAmount", as_name="baseAmount"),
                                    TagField("$.signer", as_name="signer")),
                            definition = IndexDefinition(index_type = IndexType.JSON, prefix = ["TX:"]))
    
    conn.commit()
    conn.close()
    
    r.xadd("INIT_COMPLETE", {"date": str(datetime.datetime.now())})
    _b()

if __name__ == "__main__":
    rlt = init_redis()