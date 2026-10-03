# ============================================================
# Travel Booking System — DTO: Người dùng (User)
# ============================================================

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """Thông tin user trả về cho client (KHÔNG chứa mật khẩu)."""
    id: UUID
    email: str
    full_name: str
    phone_number: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list, description="Danh sách vai trò")
    created_at: datetime
