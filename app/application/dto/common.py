# ============================================================
# Travel Booking System — DTO: Dùng chung (Common)
# ============================================================

from typing import Generic, TypeVar
from pydantic import BaseModel, Field
import math

# TypeVar cho phép PaginatedResponse dùng được với bất kỳ kiểu dữ liệu nào
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Response có phân trang (dùng cho danh sách tour, booking, user...).

    Ví dụ response:
    {
        "items": [...],         // Danh sách dữ liệu trang hiện tại
        "total": 100,           // Tổng số bản ghi
        "page": 1,              // Trang hiện tại
        "page_size": 20,        // Số bản ghi mỗi trang
        "total_pages": 5        // Tổng số trang
    }
    """
    items: list[T]
    total: int = Field(..., description="Tổng số bản ghi")
    page: int = Field(..., description="Trang hiện tại")
    page_size: int = Field(..., description="Số bản ghi mỗi trang")
    total_pages: int = Field(..., description="Tổng số trang")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        """Tạo response phân trang với tổng số trang tự tính."""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
        )


class MessageResponse(BaseModel):
    """Response đơn giản chỉ chứa thông báo."""
    message: str
    success: bool = True
