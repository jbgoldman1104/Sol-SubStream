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

token_columns = """
                ("id", "mint", "name", "symbol", "uri", "seller_fee_basis_points", 
                    "creators", "verified", "share", mint_authority", "supply", "image", "description", "twitter", "website", "holders", "created")
                """
def write_tokens(cur, rows):
    data = [[v for v in row.values()] for row in rows.values()]
    cur.executemany(f"""
                    INSERT INTO "tokens" {token_columns}
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT("id") DO UPDATE SET {token_columns} = ROW(EXCLUDED.*)
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


pair_columns = """
                ("id", "price", "liq", "mcap", "cSupply", "tSupply", "baseMint", "quoteMint", 
                "poolAddress", "created", "baseSymbol", "quoteSymbol", "baseName", "quoteName", "dex", "dexImage", "outerProgram", "holders",
                "r",            "txns", "buys", "sells", "volume", "buyVolume", "sellVolume", "makers", "buyers", "sellers",
                "r0", "score0", "txns0", "buys0", "sells0", "volume0", "buyVolume0", "sellVolume0", "makers0", "buyers0", "sellers0", "d_price0",
                "r1", "score1", "txns1", "buys1", "sells1", "volume1", "buyVolume1", "sellVolume1", "makers1", "buyers1", "sellers1", "d_price1",
                "r2", "score2", "txns2", "buys2", "sells2", "volume2", "buyVolume2", "sellVolume2", "makers2", "buyers2", "sellers2", "d_price2",
                "r3", "score3", "txns3", "buys3", "sells3", "volume3", "buyVolume3", "sellVolume3", "makers3", "buyers3", "sellers3", "d_price3"
                )
                """
def write_pairs(cur, rows):
    data = [[v for v in row.values()] for row in rows.values()]
    cur.executemany(f"""
                    INSERT INTO "pairs" {pair_columns} VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT("id") DO UPDATE SET {pair_columns} = ROW(EXCLUDED.*)
                    """, data)
                     

def read_wallets(cur, r):
    cur.execute("SELECT * FROM wallets")
    while True:
        rows = cur.fetchmany(env.DB_READ_SIZE * 10)
        if not rows: break
        r.hmset('H_W', {row[1]: row[0] for row in rows})
        r.json().mset([common.toW(row) for row in rows])

wallet_columns = """
                ("wid", "address", "tid", "buy", "sell", "remain", "buyUSD", "sellUSD", "lastTx") 
                """
def write_wallets(cur, rows):
    # data = [[v for v in row.values()] for row in rows.values()]
    cur.executemany(f"""
                    INSERT INTO "wallets" {wallet_columns}
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT "wid_tid" DO UPDATE SET {wallet_columns} = ROW(EXCLUDED.*)
                    """, rows)

def update_wallets(cur, rows):
    cur.executemany(f"""
                    INSERT INTO "wallets" {wallet_columns}
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT "wid_tid" DO UPDATE SET 
                        "buy" = "wallets"."buy" + EXCLUDED."buy",
                        "sell" = "wallets"."sell" + EXCLUDED."sell",
                        "remain" = "wallets"."remain" + EXCLUDED."remain",
                        "buyUSD" = "wallets"."buyUSD" + EXCLUDED."buyUSD",
                        "sellUSD" = "wallets"."sellUSD" + EXCLUDED."sellUSD"
                    """, rows)

   
dex_columns = """
            ("id", "address", "name", "image")
            """
def write_dexes(cur, rows):
    data = [[v for v in row.values()] for row in rows.values()]
    cur.executemany(f"""
                    INSERT INTO "dexes" {dex_columns} VALUES (%s, %s, %s, %s)
                    ON CONFLICT("id") DO UPDATE SET {dex_columns} = ROW(EXCLUDED.*)
                    """, data)
            
def read_dexes(cur, r):
    cur.execute("SELECT * FROM dexes")
    while True:
        rows = cur.fetchmany(env.DB_READ_SIZE * 10)
        if not rows: break
        r.hmset('H_D', {row[1]: row[0] for row in rows})
        r.json().mset([common.toW(row) for row in rows])

async def input_thread():
    while True:
        time.sleep(0.001)

        for row in cur:
            print(row)

if __name__ == "__main__":
    rlt = input_thread()