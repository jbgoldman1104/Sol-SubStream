DEBUG = False
DOMAIN = 'http://localhost:8000'
# DOMAIN = 'https://memetrend.united-crypto.xyz'

REDIS_HOST = 'localhost'
REDIS_PORT = 9438
REDIS_PASS = 'b2dErksi2RaPer6kSne9vkw'

DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'substream'
DB_USER = 'substream'
DB_PASS = 'koheitorres'

UPDATE_INTERVAL = 2000
# DURATION = (1 * 6, 2 * 6, 3 * 6, 4 * 6)
DURATION = (5 * 60, 60 * 60, 360 * 60, 24 * 60 * 60)
DURATION_TS = (2, 4, 6, 7)
PREV_SUM_LENGTH = (60)
CACHE_COUNT = 500
NTEST = 20
USE_PG = True
USE_P_TABLE = False
DB_READ_SIZE = 1000
NUM_REQUESTS = 1
NUM_DURATIONS = len(DURATION)
EXPIRE_TIME = 86400

from pathlib import Path
BASE_DIR = Path(__file__).parent
PROJ_DIR = BASE_DIR.parent

# --- exported files ---
FILENAME_D = str(Path(BASE_DIR, 'fileD.json'))
FILENAME_T = str(Path(BASE_DIR, 'fileT.json'))
FILENAME_FailedT = str(Path(BASE_DIR, 'fileFailedT.json'))

SEC = 1             # original or sec(1d)
MIN = 60 * SEC      # min(1d)
MIN5 = 5 * MIN      # 5 min(5d)
MIN30 = 30 * MIN    # 30 min(1m)
HOUR = 60 * MIN     # 1h(3m)
HOUR2 = 2 * HOUR    # 2h(6m)
HOUR6 = 6 * HOUR    # 6h(6m)

DAY = 24 * HOUR     # 1d(1y)
DAY5 = 5 * DAY
WEEK = 7 * DAY      # 1w(5y)
MONTH = 30 * DAY
MONTH3 = 3 * MONTH
MONTH6 = 6 * MONTH
YEAR = 12 * MONTH
YEAR5 = 60 * MONTH

RP = [DAY, DAY, DAY5, MONTH, MONTH3, MONTH6, MONTH6, YEAR, YEAR5]
BD = [SEC, MIN, MIN5, MIN30, HOUR, HOUR2, HOUR6, DAY, WEEK]
NUM_INTERVALS = len(RP)
INTERVALS = {
    '1s': 0,
    '1m': 1,
    '5m': 2,
    '30m': 3,
    '1h': 4,
    '2h': 5,
    '6h': 6,
    '1d': 7,
    '1w': 8,
}


API_KEY_TEST = "https://rpc.hellomoon.io/00f4178d-d782-4d0e-ac29-02706daa7be2"
RPC_LIST = "https://empty-responsive-ensemble.solana-mainnet.quiknode.pro/d317177c944fa95629761e0484360b336177a75e/,https://mainnet.helius-rpc.com/?api-key=e4226aa3-24f7-43c1-869f-a1b1e3fbb148,https://fluent-side-isle.solana-mainnet.quiknode.pro/19a27fc1fa07c0a0aff254ef753b1ba030360b39,https://api.mainnet-beta.solana.com,https://skilled-blissful-waterfall.solana-mainnet.quiknode.pro/d1bbbd179348df7e05a449d81fb7cdde96e589dc/"

NS_ST = '/socket.io/st'
NS_TX = '/socket.io/tx'

NSS = [NS_ST, NS_TX]