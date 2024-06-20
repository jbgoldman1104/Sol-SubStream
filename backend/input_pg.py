# import psycopg
import common
import time

r = common.connect_redis()
conn = common.connect_db()
cur = conn.cursor()

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