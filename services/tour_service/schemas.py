from datetime import date, time 
from typing import List, Optional 
from pydantic import BaseModel, Field


# 1 xây dựng class activity hoạt động trong ngày
class ActivityBase(BaseModel):
    time_slot: Optional[time] = Field(None, description = "khung giờ diễn ra")
    place_name: str = Field(..., max_length =255, description = "tên địa điểm")
    description: Optional[str] = Field(None, description = "mô tả chi tiết")
    latitude: Optional[float] = Field(None, description = " vĩ độ bản đồ")
    longitude: Optional[float] = Field(None, description = "kinh độ bản đồ")


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
    
    
    