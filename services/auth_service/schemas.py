# khai báo thư viện
from IPython.core import display_functions
from typing import Optional 
from pydantic import BaseModel, EmailStr, Field

# dữ liệu đầu vào gửi từ client
class RegisterRequest(BaseModel):
    # dữ liệu từ form đăng ký tài khoản 
    email: EmailStr = Field(..., description="Email đăng nhập của người dùng")
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu (tối thiểu 6 ký tự)")
    full_name: str =Field(...,min_length=2, max_length=255, description="Họ tên đầy đủ" )
    phone_number: Optional[str] = Field(None, max_length=20, description="Số điện thoại liên hệ")

class LoginRequest(BaseModel):
    # dữ liệu từ form đăng nhập
    email: EmailStr = Field(..., description="Email đã đăng ký")
    password: str = Field(..., description="Mật khẩu")

class RefreshTokenRequest(BaseModel):
    # dữ liệu yêu cầu cấp access token mới
    refresh_token: str = Field(..., description="Mã Refresh Token dài hạn đã được cấp")

# dữ liệu trả về cho client
class UserResponse(BaseModel):
    # thông tin tài khoản được trả về 
    id: str
    email: str
    full_name: str
    phone_number: Optional[str] = None
    role: str
    is_active: bool

class TokenResponse(BaseModel):
    # kết quả đăng nhập thành công trả về token và thông tin user
    access_token: str
    refresh_token: str
    token_type: str ="bearer"
    user: UserResponse