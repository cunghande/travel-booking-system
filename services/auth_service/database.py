# khai báo thư viện
import os 
from typing import AsyncGenerator 
import aiomysql

# đọc thông số từ biến môi trường trong .env
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "travel_booking")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))

# Biến lưu trữ Connection Pool dùng chung trong Auth Service
_pool: aiomysql.Pool | None = None

async def init_db_pool():
    # khởi tạo connection pool kết nối MySQL khi auth service được khởi động
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
    print(f"[AUTH SERVICE] [OK] Da ket noi MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")

async def close_db_pool():
    # đóng toàn bộ kết nối MYSQL khi auth service tắt
    global _pool 
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool =None
        print("Auth Service đã đóng kết nối MySQL")

def get_pool():
    # lấy kết nối connection pool hiện tại
    if _pool is None:
        raise RuntimeError("MYSQL connection Pool chưa được khởi tạo")
    return _pool

async def get_db():
    pool =get_pool()
    async with pool.acquire() as conn:
        yield conn