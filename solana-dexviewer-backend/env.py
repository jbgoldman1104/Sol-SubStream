REDIS_HOST = '178.63.98.180'
REDIS_PORT = 6379

DB_HOST = REDIS_HOST
DB_PORT = 5432
DB_NAME = 'test_db'
DB_USER = 'test_user'
DB_PASS = 'p@33w0rd'

UPDATE_INTERVAL = 3
# DURATION = (1 * 6000, 2 * 6000, 3 * 6000, 4 * 6000)
DURATION = (5 * 60000, 60 * 60000, 360 * 60000, 24 * 60 * 60000)
PREV_SUM_LENGTH = (60000)
CACHE_COUNT = 10
NTEST = 20
USE_PG = True
USE_P_TABLE = False
DB_READ_SIZE = 100

API_KEY = "https://mainnet.helius-rpc.com/?api-key=e4226aa3-24f7-43c1-869f-a1b1e3fbb148"