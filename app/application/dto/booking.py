# ============================================================
# Travel Booking System — DTOs: Booking
# ============================================================
# Định nghĩa cấu trúc dữ liệu đầu vào và đầu ra cho Đơn đặt tour.
# Sử dụng Pydantic v2 để validate dữ liệu chặt chẽ.
# ============================================================

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.value_objects.enums import BookingStatus


# --------------- Input DTOs (Dữ liệu gửi lên từ Client) ---------------

class PassengerCreateRequest(BaseModel):
    """Thông tin chi tiết của 1 hành khách đi cùng."""
    full_name: str = Field(..., min_length=2, max_length=255, description="Họ và tên hành khách")
    passenger_type: str = Field("ADULT", pattern="^(ADULT|CHILD)$", description="Loại hành khách: ADULT hoặc CHILD")
    id_card_number: str | None = Field(None, max_length=50, description="CCCD / Hộ chiếu (nếu có)")


class CreateBookingRequest(BaseModel):
    """
    Dữ liệu khách hàng gửi lên để tạo đơn đặt tour.
    """
    tour_id: uuid.UUID = Field(..., description="ID của tour muốn đặt")
    num_adults: int = Field(1, ge=1, le=50, description="Số lượng vé người lớn (tối thiểu 1)")
    num_children: int = Field(0, ge=0, le=50, description="Số lượng vé trẻ em (mặc định 0)")
    
    # Thông tin liên hệ
    contact_name: str = Field(..., min_length=2, max_length=255, description="Họ tên người liên hệ")
    contact_email: EmailStr = Field(..., description="Email nhận thông tin vé")
    contact_phone: str = Field(..., min_length=9, max_length=20, description="Số điện thoại liên hệ")
    
    # Yêu cầu đặc biệt (tùy chọn)
    special_requests: str | None = Field(None, max_length=1000, description="Yêu cầu riêng (ăn kiêng, phòng...)")
    
    # Danh sách hành khách (tùy chọn, nếu không gửi thì hệ thống tự tạo theo người liên hệ)
    passengers: list[PassengerCreateRequest] = Field(default_factory=list, description="Danh sách chi tiết từng khách")


# --------------- Output DTOs (Dữ liệu trả về cho Client) ---------------

class PassengerResponse(BaseModel):
    """Thông tin hành khách trả về."""
    id: uuid.UUID | None = None
    full_name: str
    passenger_type: str
    id_card_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    """
    Chi tiết đơn đặt tour đầy đủ trả về cho Client.
    """
    id: uuid.UUID
    booking_code: str = Field(..., description="Mã đặt tour duy nhất")
    user_id: uuid.UUID
    tour_id: uuid.UUID
    tour_title: str | None = Field(None, description="Tên tour du lịch đã đặt")
    status: BookingStatus = Field(..., description="Trạng thái đơn (PENDING_PAYMENT, CONFIRMED, CANCELLED)")
    num_adults: int
    num_children: int
    total_price: Decimal = Field(..., description="Tổng số tiền thanh toán")
    contact_name: str
    contact_email: str
    contact_phone: str
    special_requests: str | None = None
    passengers: list[PassengerResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    """
    Thông tin rút gọn cho danh sách hiển thị đơn đặt tour.
    """
    id: uuid.UUID
    booking_code: str
    tour_id: uuid.UUID
    tour_title: str | None = None
    status: BookingStatus
    num_adults: int
    num_children: int
    total_price: Decimal
    contact_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
