# ============================================================
# Travel Booking System — Kết nối Database (asyncpg)
# ============================================================
# File này quản lý kết nối tới PostgreSQL bằng thư viện asyncpg.
#
# KHÔNG DÙNG ORM (SQLAlchemy). Thay vào đó:
# - Kết nối trực tiếp bằng asyncpg (nhanh hơn, rõ ràng hơn)
# - Gọi Stored Procedures đã tạo sẵn trong database
# - Dùng Connection Pool để tái sử dụng kết nối (hiệu suất cao)
#
# Cách dùng trong code:
#   from app.core.database import get_db
#   async with get_db() as conn:
#       result = await conn.fetch("SELECT * FROM tours")
# ============================================================

import asyncpg
from app.core.config import settings

# Biến toàn cục lưu Connection Pool (khởi tạo 1 lần khi server start)
# Connection Pool = "bể chứa" nhiều kết nối DB sẵn sàng, các request
# mượn kết nối từ pool rồi trả lại khi xong (không cần mở/đóng liên tục)
_pool: asyncpg.Pool | None = None


async def khoi_tao_pool():
    """
    Tạo Connection Pool khi server khởi động.

    Pool giữ sẵn một số kết nối (min_size) và có thể mở thêm (max_size)
    khi có nhiều request đồng thời. Điều này giúp:
    - Giảm thời gian chờ mở kết nối mới
    - Giới hạn số kết nối tối đa tránh quá tải DB
    """
    global _pool
    _pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        min_size=settings.DB_POOL_MIN,      # Số kết nối tối thiểu giữ sẵn
        max_size=settings.DB_POOL_MAX,      # Số kết nối tối đa cho phép
    )
    print(f"[DATABASE] ✅ Đã kết nối PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")


async def dong_pool():
    """Đóng tất cả kết nối khi server tắt (giải phóng tài nguyên)."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        print("[DATABASE] 🛑 Đã đóng kết nối PostgreSQL")


def lay_pool() -> asyncpg.Pool:
    """
    Lấy Connection Pool hiện tại.
    Nếu pool chưa được khởi tạo thì báo lỗi rõ ràng.
    """
    if _pool is None:
        raise RuntimeError(
            "Connection Pool chưa được khởi tạo! "
            "Hãy gọi khoi_tao_pool() trước khi sử dụng database."
        )
    return _pool


async def get_db():
    """
    Dependency Injection cho FastAPI: Cung cấp 1 kết nối DB cho mỗi request.

    Cách hoạt động:
    1. Mượn 1 kết nối từ pool
    2. Dùng kết nối đó để xử lý request
    3. Tự động trả kết nối về pool khi request xong (dù thành công hay lỗi)

    Cách dùng trong Router:
        @router.get("/tours")
        async def get_tours(conn=Depends(get_db)):
            result = await conn.fetch("SELECT * FROM tours")
    """
    pool = lay_pool()
    async with pool.acquire() as connection:
        yield connection


# ==========================================
# ALIASES TIẾNG ANH (tương thích cả 2 chuẩn gọi hàm)
# ==========================================
init_db_pool = khoi_tao_pool
close_db_pool = dong_pool
get_pool = lay_pool
