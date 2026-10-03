# ============================================================
# Travel Booking System — Dependency Injection (Tiêm phụ thuộc)
# ============================================================
# File này cung cấp các "dependency" dùng chung cho tất cả API:
# - get_db: Cung cấp kết nối database
# - get_current_user: Xác thực token và trả về user hiện tại
# - require_roles: Kiểm tra quyền truy cập theo vai trò
#
# CÁCH DÙNG trong Router:
#   @router.get("/tours")
#   async def get_tours(conn=Depends(get_db)):
#       ...
#
#   @router.post("/bookings")
#   async def create_booking(user=Depends(get_current_user)):
#       ...
# ============================================================

from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import giai_ma_token

# OAuth2 scheme: Cho FastAPI biết token nằm ở header "Authorization: Bearer <token>"
# tokenUrl: Đường dẫn API đăng nhập (hiển thị trên Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Type alias cho dependency kết nối DB (viết gọn hơn trong router)
DBConn = Annotated[asyncpg.Connection, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    conn: DBConn,
) -> dict:
    """
    Xác thực JWT Token và trả về thông tin user hiện tại.

    Luồng xử lý:
    1. Lấy token từ header Authorization
    2. Giải mã token để lấy user_id
    3. Truy vấn database lấy thông tin user + roles
    4. Kiểm tra user còn hoạt động không
    5. Trả về dict chứa thông tin user

    Nếu token sai/hết hạn/user không tồn tại → ném lỗi 401
    """
    # Bước 1: Giải mã token
    try:
        payload = giai_ma_token(token)
    except JWTError:
        raise UnauthorizedError("Token không hợp lệ hoặc đã hết hạn")

    # Bước 2: Kiểm tra loại token (phải là "access", không phải "refresh")
    if payload.get("type") != "access":
        raise UnauthorizedError("Loại token không hợp lệ")

    # Bước 3: Lấy user_id từ token
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token thiếu thông tin người dùng")

    # Bước 4: Truy vấn database qua stored procedure
    row = await conn.fetchrow(
        "SELECT * FROM fn_lay_user_theo_id($1)",
        UUID(user_id)
    )

    if not row:
        raise UnauthorizedError("Không tìm thấy tài khoản")

    if not row["is_active"]:
        raise UnauthorizedError("Tài khoản đã bị khóa")

    # Bước 5: Trả về thông tin user dạng dict
    return {
        "id": row["user_id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "phone_number": row["phone_number"],
        "is_active": row["is_active"],
        "roles": list(row["role_names"]) if row["role_names"] else [],
        "created_at": row["created_at"],
    }


# Type alias: Inject user đã xác thực vào router
CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_roles(*role_names: str):
    """
    Tạo dependency kiểm tra quyền truy cập theo vai trò.

    Cách dùng:
        # Chỉ Admin mới truy cập được
        @router.get("/users", dependencies=[Depends(require_roles("ADMIN"))])

        # Admin hoặc Staff đều truy cập được
        @router.post("/tours")
        async def create_tour(user=Depends(require_roles("ADMIN", "STAFF"))):
            ...
    """
    async def kiem_tra_quyen(current_user: CurrentUser) -> dict:
        # Lấy danh sách vai trò của user
        user_roles = set(current_user.get("roles", []))
        # Danh sách vai trò được phép
        required = set(role_names)

        # Kiểm tra: user có ít nhất 1 vai trò trong danh sách yêu cầu không
        if not user_roles.intersection(required):
            raise ForbiddenError(
                f"Bạn cần có vai trò {', '.join(role_names)} để thực hiện thao tác này"
            )
        return current_user

    return kiem_tra_quyen


# Các type alias tiện lợi cho từng mức quyền:
AdminUser = Annotated[dict, Depends(require_roles("ADMIN"))]
StaffUser = Annotated[dict, Depends(require_roles("ADMIN", "STAFF"))]


def get_client_ip(request: Request) -> str | None:
    """Lấy địa chỉ IP của client từ request (dùng cho audit log)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
