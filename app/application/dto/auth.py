# ============================================================
# Travel Booking System — DTO: Xác thực (Auth)
# ============================================================
# DTO = Data Transfer Object = "khuôn dữ liệu"
# Định nghĩa cấu trúc dữ liệu đầu vào/đầu ra cho các API xác thực.
# Pydantic tự động kiểm tra dữ liệu hợp lệ (validate).
# ============================================================

from pydantic import BaseModel, EmailStr, Field


# --- Dữ liệu đầu vào (Client gửi lên Server) ---

class RegisterRequest(BaseModel):
    """Dữ liệu đăng ký tài khoản mới."""
    email: EmailStr = Field(..., description="Email đăng ký (phải đúng format)")
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu (tối thiểu 6 ký tự)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Họ và tên đầy đủ")
    phone_number: str | None = Field(None, max_length=20, description="Số điện thoại (tùy chọn)")


class LoginRequest(BaseModel):
    """Dữ liệu đăng nhập."""
    email: EmailStr = Field(..., description="Email đã đăng ký")
    password: str = Field(..., description="Mật khẩu")


class RefreshRequest(BaseModel):
    """Dữ liệu làm mới token."""
    refresh_token: str = Field(..., description="Refresh token hiện tại")


# --- Dữ liệu đầu ra (Server trả về Client) ---

class TokenResponse(BaseModel):
    """Token trả về sau khi đăng nhập/refresh thành công."""
    access_token: str = Field(..., description="Token dùng cho mỗi request API")
    refresh_token: str = Field(..., description="Token dùng để lấy access_token mới")
    token_type: str = Field(default="bearer", description="Loại token (luôn là 'bearer')")
