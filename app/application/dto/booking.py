# ============================================================
# Travel Booking System — DTO: Đặt tour (Booking)
# ============================================================

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Dữ liệu đầu vào ---

class PassengerCreate(BaseModel):
    """Thông tin 1 hành khách đi cùng."""
    full_name: str = Field(..., min_length=2, max_length=255, description="Họ và tên")
    passenger_type: str = Field("ADULT", pattern="^(ADULT|CHILD)$", description="ADULT hoặc CHILD")
    id_card_number: str | None = Field(None, max_length=50, description="Số CCCD / Hộ chiếu")


class BookingCreate(BaseModel):
    """Dữ liệu tạo đơn đặt tour."""
    tour_id: UUID = Field(..., description="ID tour muốn đặt")
    num_adults: int = Field(1, ge=1, le=50, description="Số vé người lớn (tối thiểu 1)")
    num_children: int = Field(0, ge=0, le=50, description="Số vé trẻ em")
    contact_name: str = Field(..., min_length=2, max_length=255, description="Tên người liên hệ")
    contact_email: EmailStr = Field(..., description="Email nhận thông tin vé")
    contact_phone: str = Field(..., min_length=9, max_length=20, description="Số điện thoại")
    special_requests: str | None = Field(None, max_length=1000, description="Yêu cầu đặc biệt")
    passengers: list[PassengerCreate] = Field(default_factory=list, description="Danh sách hành khách")


# --- Dữ liệu đầu ra ---

class PassengerResponse(BaseModel):
    """Thông tin hành khách trả về."""
    id: UUID
    full_name: str
    passenger_type: str
    id_card_number: str | None = None


class BookingResponse(BaseModel):
    """Chi tiết đơn đặt tour đầy đủ."""
    id: UUID
    booking_code: str
    user_id: UUID | None = None
    tour_id: UUID
    tour_title: str | None = None
    status: str
    num_adults: int
    num_children: int
    total_price: Decimal
    contact_name: str
    contact_email: str
    contact_phone: str
    special_requests: str | None = None
    passengers: list[PassengerResponse] = []
    created_at: datetime
    updated_at: datetime | None = None


class BookingListResponse(BaseModel):
    """Thông tin rút gọn cho danh sách đơn đặt tour."""
    id: UUID
    booking_code: str
    tour_id: UUID
    tour_title: str | None = None
    status: str
    num_adults: int
    num_children: int
    total_price: Decimal
    contact_name: str
    created_at: datetime
