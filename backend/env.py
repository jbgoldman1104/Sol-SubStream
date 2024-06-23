
DOMAIN = 'http://localhost:8000'
# DOMAIN = 'https://memetrend.united-crypto.xyz'

REDIS_HOST = 'localhost'
# REDIS_PORT = 12000
REDIS_PORT = 6379

# DB_HOST = 'solana-dex-trade.cv6oeci62jkj.eu-north-1.rds.amazonaws.com'
# DB_PORT = 5432
# DB_NAME = 'dex_trade'
# DB_USER = 'postgres'
# DB_PASS = 'lOkPF4Rz0rFy6IdMdrUk'
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'dex_trade'
DB_USER = 'postgres'
DB_PASS = 'lOkPF4Rz0rFy6IdMdrUk'

UPDATE_INTERVAL = 2000
# DURATION = (1 * 6, 2 * 6, 3 * 6, 4 * 6)
DURATION = (5 * 60, 60 * 60, 360 * 60, 24 * 60 * 60)
PREV_SUM_LENGTH = (60)
CACHE_COUNT = 500
NTEST = 20
USE_PG = True
USE_P_TABLE = False
DB_READ_SIZE = 1000
NUM_REQUESTS = 8
NUM_DURATIONS = len(DURATION)

# --- exported files ---
FILENAME_D = '/root/torres/Sol-SubStream/fileD.json'
FILENAME_T = '/root/torres/Sol-SubStream/fileT.json'
FILENAME_FailedT = '/root/torres/Sol-SubStream/fileFailedT.json'


DAY = 86400
DAY5 = 5 * DAY
MONTH = 30 * DAY
MONTH3 = 3 * MONTH
MONTH6 = 6 * MONTH
YEAR5 = 60 * MONTH

SEC = 1          # original or sec(1d)
MIN = 60 * SEC      # min(1d)
MIN5 = 5 * MIN      # 5 min(5d)
MIN30 = 30 * MIN    # 30 min(1m)
HOUR = 60 * MIN     # 1h(3m)
HOUR2 = 120 * MIN   # 2h(6m)
WEEK = 7 * DAY      # 1w(5y)


RP = [DAY, DAY, DAY5, MONTH, MONTH3, MONTH6, YEAR5]
BD = [SEC, MIN, MIN5, MIN30, HOUR, HOUR2, WEEK]
NUM_INTERVALS = len(RP)
INTERVALS = {
    '1s': 0,
    '1m': 1,
    '5m': 2,
    '30m': 3,
    '1h': 4,
    '2h': 5,
    '1w': 6,
}


API_KEY_TEST = "https://rpc.hellomoon.io/00f4178d-d782-4d0e-ac29-02706daa7be2"
API_KEY1 = "https://empty-responsive-ensemble.solana-mainnet.quiknode.pro/d317177c944fa95629761e0484360b336177a75e/"
API_KEY2 = "https://skilled-blissful-waterfall.solana-mainnet.quiknode.pro/d1bbbd179348df7e05a449d81fb7cdde96e589dc/"

NS_ST = '/socket.io/st'
NS_TX = '/socket.io/tx'

NSS = [NS_ST, NS_TX]