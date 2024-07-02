# import psycopg
import common
import time
import env

r = common.connect_redis()
conn = common.connect_db()
cur = conn.cursor()

def update_txs(cur, txs):
    data = [(tx[2]['pid'], tx[2]['type'], tx[2]['price'], tx[2]['id']) for tx in txs]
    cur.executemany("""
                    UPDATE "trade" SET "pid" = %s, "type" = %s, "price" = %s WHERE "id" = %s
                    """, data)

def read_txs():
    pass


def write_tokens(cur, tokens):
    data = [tokens.values()]
    cur.executemany("""
                    INSERT INTO "tokens" ("id", "mint", "name", "symbol", "uri", "seller_fee_basis_points", 
                    "creators", "verified", "share", mint_authority", "supply", "image", "description", "twitter", "website", "holders", "created")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, data)

def read_tokens(cur, r):
    cur.execute("SELECT * FROM tokens")
    while True:
        rows = cur.fetchmany(env.DB_READ_SIZE * 10)
        if not rows: break
        r.hmset('H_T', {row[1]: row[0] for row in rows})
        r.json().mset([common.toT(row) for row in rows])
        
def read_pairs(cur, r):
    cur.execute("SELECT * FROM pairs")
    while True:
        rows = cur.fetchmany(env.DB_READ_SIZE * 10)
        if not rows: break
        r.hmset('H_P', {row[1]: row[8] for row in rows})
        r.json().mset([common.toP(row) for row in rows])

def write_pairs(cur, pairs):
    data = [(pairs.values())]
    cur.executemany("""
                    INSERT INTO "pairs" ("id", "price", "liq", "mcap", "cSupply", "tSupply", "baseMint", "quoteMint", 
                    "poolAddress", "created", "baseSymbol", "quoteSymbol", "baseName", "quoteName", "dex", "dexImage", "outerProgram", "holders",
                    "r",            "txns", "buys", "sells", "volume", "buyVolume", "sellVolume", "makers", "buyers", "sellers",
                    "r0", "score0", "txns0", "buys0", "sells0", "volume0", "buyVolume0", "sellVolume0", "makers0", "buyers0", "sellers0", "d_price0",
                    "r1", "score1", "txns1", "buys1", "sells1", "volume1", "buyVolume1", "sellVolume1", "makers1", "buyers1", "sellers1", "d_price1",
                    "r2", "score2", "txns2", "buys2", "sells2", "volume2", "buyVolume2", "sellVolume2", "makers2", "buyers2", "sellers2", "d_price2",
                    "r3", "score3", "txns3", "buys3", "sells3", "volume3", "buyVolume3", "sellVolume3", "makers3", "buyers3", "sellers3", "d_price3",
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """, data)
def read_wallets(cur, r):
    cur.execute("SELECT * FROM wallets")
    while True:
        rows = cur.fetchmany(env.DB_READ_SIZE * 10)
        if not rows: break
        r.hmset('H_W', {row[1]: row[0] for row in rows})
        r.json().mset([common.toW(row) for row in rows])

def write_wallets(cur, wallets):
    data = [(wallets.values())]
    cur.executemany("""
                    INSERT INTO "wallets" ("id", "address") VALUES (%s, %s)
                    """, data)


    

def write_dexes(cur, dexes):
    data = [(dexes.values())]
    cur.executemany("""
                    INSERT INTO "dexes" ("id", "address", "name", "image")
                    """)

def read_dexes(cur, r):
    cur.execute("SELECT * FROM dexes")
    while True:
        rows = cur.fetchmany(env.DB_READ_SIZE * 10)
        if not rows: break
        r.hmset('H_D', {row[1]: row[0] for row in rows})
        r.json().mset([common.toW(row) for row in rows])

async def input_thread():
    cur.execute("""
        CREATE TABLE tokens (
            id serial PRIMARY KEY,
            name text,
            freq integer)
        """)
    cur.execute("INSERT INTO tokens (name, freq) VALUES (%s, %s)", ("SOL", 0))
    cur.execute("SELECT * FROM tokens")
    cur.fetchone()
        
    while True:
        time.sleep(0.001)
        

        for row in cur:
            print(row)

if __name__ == "__main__":
    rlt = input_thread()