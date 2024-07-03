import env
import common
import os
from benchmark import _b

def deleteFile(filename: str):
    if os.path.exists(filename):
        os.remove(filename)
        
def dropTable(cur, name: str):
    cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s", (name,))
    if bool(cur.rowcount):
        cur.execute(f"DROP TABLE \"{name}\"")

def delete_all():
    print('-- delete_all process started. --')
    
    r = common.connect_redis()
    if env.USE_PG:
        conn = common.connect_db()
        cur = conn.cursor()
    
    _b('DELETE')
    
    r.flushall()
    
    # --- Delete PG ---
    dropTable(cur, 'sync')
    dropTable(cur, 'trade')
    dropTable(cur, 'pairs')
    dropTable(cur, 'wallets')
    # dropTable(cur, 'tokens')
    # dropTable(cur, 'dexes')

    conn.commit()
    
    # --- Delete Saved Redis Dump Files ---
    # deleteFile(env.FILENAME_T)
    # deleteFile(env.FILENAME_FailedT)

    _b()


if __name__ == "__main__":
    rlt = delete_all()