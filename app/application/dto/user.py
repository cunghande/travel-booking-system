# ============================================================
# Travel Booking System — DTO: Người dùng (User)
# ============================================================

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserUpdateRequest(BaseModel):
    """Dữ liệu cập nhật thông tin người dùng."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Họ và tên")
    phone_number: Optional[str] = Field(None, min_length=9, max_length=20, description="Số điện thoại")
    is_active: Optional[bool] = Field(None, description="Trạng thái kích hoạt")


class AssignRoleRequest(BaseModel):
    """Dữ liệu gán vai trò mới cho người dùng."""
    role_name: str = Field(..., description="Tên vai trò (ADMIN, STAFF, CUSTOMER)")


class UserResponse(BaseModel):
    """Thông tin user trả về cho client (KHÔNG chứa mật khẩu)."""
    id: UUID
    email: str
    full_name: str
    phone_number: Optional[str] = None
    is_active: bool
    roles: list[str] = Field(default_factory=list, description="Danh sách vai trò")
    created_at: datetime
