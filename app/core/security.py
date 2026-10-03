# ============================================================
# Travel Booking System — Bảo mật (Security)
# ============================================================
# Xử lý 2 việc chính:
# 1. Mã hóa & kiểm tra mật khẩu (bcrypt)
# 2. Tạo & giải mã JWT Token (JSON Web Token)
#
# QUAN TRỌNG:
# - Mật khẩu KHÔNG BAO GIỜ được lưu dạng gốc (plaintext)
# - Luôn mã hóa bằng bcrypt trước khi lưu vào database
# - JWT Token có thời hạn, hết hạn phải đăng nhập lại
# ============================================================

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ==========================================
# PHẦN 1: MÃ HÓA MẬT KHẨU (BCRYPT)
# ==========================================
# Bcrypt là thuật toán mã hóa 1 chiều:
# - Mã hóa: "Admin@123456" → "$2b$12$xxx..." (không thể giải ngược)
# - Kiểm tra: So sánh mật khẩu nhập vào với hash đã lưu


def ma_hoa_mat_khau(mat_khau_goc: str) -> str:
    """
    Mã hóa mật khẩu bằng bcrypt.

    Ví dụ:
        hash = ma_hoa_mat_khau("Admin@123456")
        # Kết quả: "$2b$12$LJ3m4ys3LzQXx7Xj0fR8ku..."
        # Mỗi lần gọi cho kết quả KHÁC NHAU (do salt ngẫu nhiên) nhưng đều hợp lệ
    """
    mat_khau_bytes = mat_khau_goc.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(mat_khau_bytes, salt).decode("utf-8")


def kiem_tra_mat_khau(mat_khau_nhap: str, mat_khau_hash: str) -> bool:
    """
    Kiểm tra mật khẩu người dùng nhập có khớp với hash trong DB không.

    Ví dụ:
        dung = kiem_tra_mat_khau("Admin@123456", "$2b$12$LJ3m...")
        # Kết quả: True nếu đúng, False nếu sai
    """
    try:
        return bcrypt.checkpw(
            mat_khau_nhap.encode("utf-8"),
            mat_khau_hash.encode("utf-8"),
        )
    except Exception:
        return False


# ==========================================
# PHẦN 2: JWT TOKEN
# ==========================================
# JWT (JSON Web Token) = "thẻ ra vào" kỹ thuật số:
# - Khi đăng nhập thành công → Server tạo token gửi cho client
# - Mỗi request sau đó, client gửi token trong header Authorization
# - Server giải mã token để biết "đây là user nào, có quyền gì"
#
# Có 2 loại token:
# - Access Token: Ngắn hạn (24h), dùng cho mỗi request API
# - Refresh Token: Dài hạn (7 ngày), dùng để lấy access token mới khi hết hạn


def tao_access_token(user_id: str | UUID, roles: list[str] | None = None, subject: str | UUID | None = None) -> str:
    """
    Tạo Access Token (token ngắn hạn dùng cho API).
    Hỗ trợ cả tham số user_id hoặc subject.
    """
    uid = subject if subject is not None else user_id
    het_han = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(uid),               # ID người dùng
        "roles": roles or [],          # Vai trò (dùng để phân quyền)
        "exp": het_han,                # Thời điểm hết hạn
        "iat": datetime.now(timezone.utc),  # Thời điểm tạo
        "type": "access",             # Đánh dấu đây là access token
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def tao_refresh_token(user_id: str | UUID = None, subject: str | UUID | None = None) -> str:
    """
    Tạo Refresh Token (token dài hạn dùng để làm mới access token).
    Hỗ trợ cả tham số user_id hoặc subject.
    """
    uid = subject if subject is not None else user_id
    het_han = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(uid),
        "exp": het_han,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def giai_ma_token(token: str) -> dict[str, Any]:
    """
    Giải mã JWT Token để lấy thông tin bên trong.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ==========================================
# ALIASES TIẾNG ANH (tương thích cả 2 chuẩn gọi hàm)
# ==========================================
hash_password = ma_hoa_mat_khau
verify_password = kiem_tra_mat_khau
create_access_token = tao_access_token
create_refresh_token = tao_refresh_token
decode_token = giai_ma_token
