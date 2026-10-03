from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ==============================================================================
# 1. ASYNC ENGINE & CONNECTION POOLING
# Quản lý vòng đời và hồ chứa kết nối (Connection Pool) tới PostgreSQL
# ==============================================================================
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,  # In toàn bộ câu lệnh SQL ra terminal khi ở chế độ DEBUG
    future=True,
    pool_size=settings.DB_POOL_SIZE,          # Số lượng kết nối mở sẵn trong pool
    max_overflow=settings.DB_MAX_OVERFLOW,    # Kết nối mở thêm khi tải cao
    pool_timeout=settings.DB_POOL_TIMEOUT,    # Thời gian chờ trước khi báo lỗi Timeout
    pool_pre_ping=True,                       # Kiểm tra tính sẵn sàng của kết nối trước khi dùng
)

# ==============================================================================
# 2. ASYNC SESSION FACTORY
# Nhà máy sản xuất đối tượng AsyncSession đại diện cho một Database Transaction
# ==============================================================================
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # BẮT BUỘC: Ngăn chặn lỗi MissingGreenlet trong Async SQLAlchemy
    autoflush=False,         # Kiểm soát tường minh thời điểm gửi câu lệnh xuống DB
    autocommit=False,        # Quản lý transaction rõ ràng (Explicit Transaction Management)
)


# ==============================================================================
# 3. DECLARATIVE BASE
# Lớp cơ sở (Base Class) chuẩn của SQLAlchemy 2.0 cho mọi Model định nghĩa sau này
# ==============================================================================
class Base(DeclarativeBase):
    pass


# ==============================================================================
# 4. DEPENDENCY INJECTION: get_db
# Hàm cung cấp Database Session độc lập cho từng HTTP Request trong FastAPI
# ==============================================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency: Cung cấp AsyncSession cho từng HTTP request.

    Vòng đời của Session trong một Request:
    1. Request đi vào endpoint có `db: AsyncSession = Depends(get_db)`:
       - Mượn 1 kết nối vật lý từ Connection Pool và mở 1 Session.
    2. Endpoint / Service / Repository thực thi các câu lệnh SQL hoặc gọi Stored Procedure.
    3. Nếu xảy ra lỗi (Exception):
       - Khối `except` tự động gọi `await session.rollback()` để hủy bỏ mọi thay đổi dở dang.
    4. Khối `finally`:
       - Luôn luôn gọi `await session.close()` để đóng session và hoàn trả kết nối
         về lại cho Connection Pool, chống rò rỉ kết nối (Connection Leak).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
