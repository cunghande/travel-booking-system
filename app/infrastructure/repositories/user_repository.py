# ============================================================
# Travel Booking System — Repository: Người dùng (User Repository)
# ============================================================
# Tầng truy xuất dữ liệu người dùng qua asyncpg và Stored Procedures.
# KHÔNG sử dụng ORM -> An toàn, bảo mật, tốc độ cao và dễ hiểu.
# ============================================================

import uuid
from typing import Any, Dict, List, Optional, Tuple
import asyncpg


class UserRepository:
    """
    Repository phụ trách toàn bộ thao tác dữ liệu liên quan đến Người dùng và Phân quyền.
    Tất cả các truy vấn đều gọi Stored Procedures / Functions trong PostgreSQL.
    """

    def __init__(self, conn: asyncpg.Connection):
        """
        Khởi tạo repository với kết nối asyncpg.
        conn được tiêm (inject) từ FastAPI dependency get_db.
        """
        self._conn = conn

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin người dùng theo UUID.
        Gọi function: fn_lay_user_theo_id(p_user_id)
        """
        sql = "SELECT * FROM fn_lay_user_theo_id($1);"
        row = await self._conn.fetchrow(sql, user_id)
        return dict(row) if row else None

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin người dùng kèm mật khẩu mã hóa theo email (dùng khi đăng nhập).
        Gọi function: fn_lay_user_theo_email(p_email)
        """
        sql = "SELECT * FROM fn_lay_user_theo_email($1);"
        row = await self._conn.fetchrow(sql, email.strip().lower())
        return dict(row) if row else None

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        phone_number: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Đăng ký tài khoản mới với vai trò mặc định CUSTOMER.
        Gọi function: fn_dang_ky_tai_khoan(...)
        """
        sql = """
            SELECT * FROM fn_dang_ky_tai_khoan(
                p_email := $1,
                p_hashed_password := $2,
                p_full_name := $3,
                p_phone_number := $4,
                p_ip_address := $5
            );
        """
        row = await self._conn.fetchrow(
            sql,
            email.strip().lower(),
            hashed_password,
            full_name.strip(),
            phone_number,
            ip_address,
        )
        return dict(row) if row else {}

    async def log_login(self, user_id: uuid.UUID, ip_address: Optional[str] = None) -> None:
        """
        Ghi nhật ký đăng nhập của người dùng vào audit_logs.
        Gọi function: fn_ghi_log_dang_nhap(...)
        """
        sql = "SELECT fn_ghi_log_dang_nhap($1, $2);"
        await self._conn.execute(sql, user_id, ip_address)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lấy danh sách người dùng kèm phân trang (Dành cho Admin).
        Gọi function: fn_lay_danh_sach_users(p_skip, p_limit, p_is_active)
        Trả về: (danh_sach_user, tong_so_user)
        """
        sql = "SELECT * FROM fn_lay_danh_sach_users($1, $2, $3);"
        rows = await self._conn.fetch(sql, skip, limit, is_active)
        
        if not rows:
            return [], 0
            
        items = [dict(r) for r in rows]
        total = items[0]["total_count"] if items else 0
        return items, total

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_name: str,
        admin_id: Optional[uuid.UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Gán thêm vai trò cho người dùng (Ví dụ: STAFF, ADMIN).
        Gọi function: fn_gan_vai_tro(...)
        """
        sql = "SELECT * FROM fn_gan_vai_tro($1, $2, $3);"
        row = await self._conn.fetchrow(sql, user_id, role_name.upper(), admin_id)
        return dict(row) if row else None

    async def update_profile(
        self,
        user_id: uuid.UUID,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cập nhật thông tin cá nhân cơ bản của người dùng.
        """
        sql = """
            UPDATE users
            SET full_name = COALESCE($2, full_name),
                phone_number = COALESCE($3, phone_number),
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, email, full_name, phone_number, is_active, updated_at;
        """
        row = await self._conn.fetchrow(sql, user_id, full_name, phone_number)
        return dict(row) if row else None
