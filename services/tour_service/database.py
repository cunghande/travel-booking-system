import os
from typing import AsyncGenerator
import aiomysql

# Đọc thông số kết nối từ .env
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "travel_booking")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))

# Connection Pool dùng chung trong Tour Service
_pool: aiomysql.Pool | None = None

async def init_db_pool():
    global _pool
    _pool = await aiomysql.create_pool(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DB,
        minsize=DB_POOL_MIN,
        maxsize=DB_POOL_MAX,
        autocommit=True,
        cursorclass=aiomysql.DictCursor,
    )
    print(f"[TOUR SERVICE] [OK] Da ket noi MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")

async def close_db_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        print("[TOUR SERVICE] Da dong ket noi MySQL")

def get_pool():
    if _pool is None:
        raise RuntimeError("MySQL connection Pool chua duoc khoi tao")
    return _pool

async def get_db():
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn
