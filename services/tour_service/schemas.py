from datetime import date, time, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# 1 xây dựng class activity hoạt động trong ngày
class ActivityBase(BaseModel):
    time_slot: Optional[time] = Field(None, description = "khung giờ diễn ra")
    place_name: str = Field(..., max_length =255, description = "tên địa điểm")
    description: Optional[str] = Field(None, description = "mô tả chi tiết")
    latitude: Optional[float] = Field(None, description = " vĩ độ bản đồ")
    longitude: Optional[float] = Field(None, description="kinh độ bản đồ")

    @field_validator("time_slot", mode="before")
    @classmethod
    def convert_timedelta(cls, v):
        # MySQL trả về TIME dưới dạng timedelta, cần chuyển sang time
        if isinstance(v, timedelta):
            total = int(v.total_seconds())
            return time(total // 3600, (total % 3600) // 60, total % 60)
        return v


class ActivityCreate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: str
    itinerary_id: str
    class Config:
        from_attributes =True

# lịch trình trong ngày
class ItineraryBase(BaseModel):
    day_number: int = Field(..., ge =1, description = " ngày thứ mấy")
    title: str = Field(..., max_length = 500, description =" tiêu đề lịch trình trong ngày")

class ItineraryCreate(ItineraryBase):
    activities: List[ActivityCreate] = Field(default_factory = list, description =" danh sách hoạt động")

class ItineraryResponse(ItineraryBase):
    id: str
    tour_id: str
    activities: List[ActivityResponse] = []
    class Config:
        from_attributes = True

# xây dựng class tour du lịch
class TourCreateRequest(BaseModel):
    tour_code: str = Field(..., max_length =50, description ="Mã tour")
    title: str = Field(..., max_length = 500, description = "Tên tour du lịch")
    description: Optional[str] = Field(None, description ="Mô tả tổng quan") 
    category: Optional[str] = Field(None, description ="Danh mục") 
    destination: str = Field(..., max_length =255, description ="Điểm đến chính")
    base_price_adult: float = Field(...,gt =0, description =" Giá vé người lớn")
    base_price_child: float = Field(0.0, ge = 0,description=" Giá vé trẻ em")
    max_participants: int =Field(20, ge =1, description ="số khách tối đa")
    start_date: date = Field(..., description ="Ngày bắt đầu")
    end_date: date = Field(..., description ="Ngày kết thúc")
    itineraries: List[ItineraryCreate] = Field(default_factory = list)

# xây dựng class update tour
class TourUpdateRequest(BaseModel):
    title: Optional[str] =None
    description: Optional[str] = None
    category: Optional[str] = None
    destination: Optional[str] = None
    base_price_adult: Optional[float] = None
    base_price_child: Optional[float] = None
    max_participants: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, description="DRAFT | PUBLISHED | ARCHIVED | CANCELLED")

# dữ liệu trả về client
class TourResponse(BaseModel):
    id: str
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
    created_by: Optional[str] = None
    itineraries: List[ItineraryResponse] = []
    class Config:
        from_attributes = True


# danh sách tour phân trang
class TourListResponse(BaseModel):
    items: List[TourResponse]
    total: int
    page: int
    size: int
    pages: int
