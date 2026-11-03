from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# hành khác đi kèm
class PassengerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255,description="Họ tên hành khách")
    passenger_type: str = Field("ADULT", description="loại khách hàng: ADULT | CHILD ")
    id_card_number: Optional[str] =Field(None, max_length=50,description="CCCD hoặc hộ chiếu")

class PassengerCreate(PassengerBase):
    pass

class PassengerResponse(PassengerBase):
    id: str
    booking_id: str
    create_at: Optional[datetime] =None

    class Config:
        from_attributes = True


# đặt tour DTO
class BookingCreateRequest(BaseModel):
    tour_id: str = Field(..., description="id của tour cần đặt (UUID)")
    num_adults: int = Field(1,ge=1, description="số lượng người lớn tối thiểu là 1")
    num_children: int = Field(0,ge =0, description= "số lượng trẻ em để mặc định là 0")
    contact_name: str = Field(..., min_length =2, max_length =255, description = " tên người liên hệ")
    contact_emai: EmailStr = Field(...,description =" Email nhận thông báo")
    contact_phone: str = Field(..., min_length = 8, max_length= 20, description ="số điện thoại người liên hệ")
    special_requests: Optional[str] =Field(None,description =" yêu cầu đặc biệt của khách hàng")
    passengers: List[PassengerCreate] = Field(default_factory=list, description="Danh sách chi tiết từng hành khách")

# cập nhập trạng thái đơn 

class BookingStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="CONFIRMED | COMPLETED | CANCELLED")


# thông tin trả về của đơn đặt vé

class BookingResponse(BaseModel):
    id: str
    booking_code: str
    user_id: Optional[str] =None
    tour_id: str
    status: str
    num_adults: int
    num_children: int
    total_price: float
    contact_name: str
    contact_email: str
    contact_phone: str
    special_requests: Optional[str] =None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


     # Thông tin tóm tắt tour kèm theo
    tour_title: Optional[str] = None
    tour_code: Optional[str] = None
    tour_destination: Optional[str] = None
    tour_start_date: Optional[date] = None
    tour_end_date: Optional[date] = None
    # Danh sách hành khách chi tiết
    passengers: List[PassengerResponse] = []
    class Config:
        from_attributes = True

class BookingListResponse(BaseModel):
    items: List[BookingResponse]
    total: int
    page: int
    size: int
    pages: int
