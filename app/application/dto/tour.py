# ============================================================
# Travel Booking System — DTO: Tour du lịch
# ============================================================

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# --- Hoạt động trong ngày ---

class ActivityCreate(BaseModel):
    """Dữ liệu tạo 1 hoạt động trong lịch trình."""
    time_slot: Optional[time] = Field(None, description="Khung giờ (VD: 08:00)")
    place_name: str = Field(..., min_length=1, max_length=255, description="Tên địa điểm")
    description: Optional[str] = Field(None, max_length=2000, description="Mô tả hoạt động")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class ActivityResponse(BaseModel):
    """Thông tin hoạt động trả về."""
    id: UUID
    time_slot: Optional[time] = None
    place_name: str
    description: Optional[str] = None


# --- Lịch trình 1 ngày ---

class ItineraryCreate(BaseModel):
    """Dữ liệu tạo lịch trình 1 ngày."""
    day_number: int = Field(..., ge=1, description="Ngày thứ mấy (1, 2, 3...)")
    title: str = Field(..., min_length=1, max_length=500, description="Tiêu đề ngày")
    activities: list[ActivityCreate] = Field(default_factory=list, description="Danh sách hoạt động")


class ItineraryResponse(BaseModel):
    """Thông tin lịch trình trả về."""
    id: UUID
    day_number: int
    title: str
    activities: list[ActivityResponse] = []


# --- Tour ---

class TourCreate(BaseModel):
    """Dữ liệu tạo tour mới."""
    title: str = Field(..., min_length=3, max_length=500, description="Tên tour")
    description: Optional[str] = Field(None, max_length=5000, description="Mô tả tour")
    category: Optional[str] = Field(None, max_length=100, description="Danh mục (Biển, Núi...)")
    destination: str = Field(..., min_length=1, max_length=255, description="Điểm đến")
    base_price_adult: Decimal = Field(..., gt=0, description="Giá vé người lớn")
    base_price_child: Decimal = Field(..., ge=0, description="Giá vé trẻ em")
    max_participants: int = Field(..., gt=0, le=1000, description="Số chỗ tối đa")
    start_date: date = Field(..., description="Ngày khởi hành")
    end_date: date = Field(..., description="Ngày kết thúc")
    itineraries: list[ItineraryCreate] = Field(default_factory=list, description="Lịch trình từng ngày")

    @field_validator("end_date")
    @classmethod
    def ngay_ket_thuc_phai_sau_bat_dau(cls, v, info):
        """Kiểm tra: ngày kết thúc phải sau ngày bắt đầu."""
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("Ngày kết thúc phải sau ngày bắt đầu")
        return v


class TourUpdate(BaseModel):
    """Dữ liệu cập nhật tour (tất cả trường tùy chọn)."""
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    destination: Optional[str] = Field(None, min_length=1, max_length=255)
    base_price_adult: Optional[Decimal] = Field(None, gt=0)
    base_price_child: Optional[Decimal] = Field(None, ge=0)
    max_participants: Optional[int] = Field(None, gt=0, le=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TourResponse(BaseModel):
    """Thông tin chi tiết tour (kèm lịch trình)."""
    id: UUID
    tour_code: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    destination: str
    base_price_adult: float
    base_price_child: float
    max_participants: int
    available_slots: int
    start_date: date
    end_date: date
    status: str
    created_by: Optional[UUID] = None
    itineraries: list[ItineraryResponse] = []
    created_at: datetime
    updated_at: datetime


class TourListResponse(BaseModel):
    """Thông tin rút gọn cho danh sách tour (không có lịch trình)."""
    id: UUID
    tour_code: str
    title: str
    category: Optional[str] = None
    destination: str
    base_price_adult: float
    base_price_child: float
    max_participants: int
    available_slots: int
    start_date: date
    end_date: date
    status: str
    created_at: datetime
