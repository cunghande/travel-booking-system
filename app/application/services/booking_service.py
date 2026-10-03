# ============================================================
# Travel Booking System — Service: Đặt tour (Booking Service)
# ============================================================
# Tầng nghiệp vụ Đặt tour: Tạo đơn, quản lý hành khách, duyệt và hủy đơn.
# Không dùng ORM — Gọi Stored Procedures PostgreSQL bảo vệ race condition.
# ============================================================

from decimal import Decimal
from typing import Optional
import uuid
import asyncpg
from loguru import logger

from app.application.dto.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    PassengerResponse,
)
from app.application.dto.common import PaginatedResponse
from app.core.exceptions import ForbiddenError, NotFoundError
from app.infrastructure.repositories.booking_repository import BookingRepository


def _to_booking_list_item(row: dict) -> BookingListResponse:
    """Chuyển đổi record tóm tắt sang BookingListResponse."""
    return BookingListResponse(
        id=row.get("booking_id") or row.get("id"),
        booking_code=row["booking_code"],
        tour_id=row["tour_id"],
        tour_title=row.get("tour_title") or row.get("title"),
        status=row["status"],
        num_adults=row["num_adults"],
        num_children=row["num_children"],
        total_price=Decimal(str(row["total_price"])),
        contact_name=row["contact_name"],
        created_at=row["created_at"],
    )


def _to_booking_detail(data: dict) -> BookingResponse:
    """Chuyển đổi record chi tiết sang BookingResponse."""
    passengers = [
        PassengerResponse(
            id=p.get("passenger_id") or p.get("id"),
            full_name=p["full_name"],
            passenger_type=p["passenger_type"],
            id_card_number=p.get("id_card_number"),
        )
        for p in data.get("passengers", [])
    ]

    return BookingResponse(
        id=data.get("booking_id") or data.get("id"),
        booking_code=data["booking_code"],
        user_id=data.get("user_id"),
        tour_id=data["tour_id"],
        tour_title=data.get("tour_title"),
        status=data["status"],
        num_adults=data["num_adults"],
        num_children=data["num_children"],
        total_price=Decimal(str(data["total_price"])),
        contact_name=data["contact_name"],
        contact_email=data["contact_email"],
        contact_phone=data["contact_phone"],
        special_requests=data.get("special_requests"),
        passengers=passengers,
        created_at=data["created_at"],
        updated_at=data.get("updated_at"),
    )


class BookingService:
    """Nghiệp vụ quản lý Đơn đặt tour."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self._repo = BookingRepository(conn)

    async def create_booking(
        self,
        user_id: uuid.UUID,
        data: BookingCreate,
        ip_address: Optional[str] = None,
    ) -> BookingResponse:
        """
        Khách hàng đặt tour:
        1. Gọi Stored Procedure fn_tao_don_dat_tour:
           - Tự động kiểm tra Tour PUBLISHED
           - Khóa dòng Tour FOR UPDATE tránh tranh chấp chỗ (race condition)
           - Tự tính tiền theo số lượng người lớn/trẻ em
           - Trừ chỗ trống available_slots
           - Sinh mã booking BK-...
        2. Thêm danh sách hành khách đi kèm.
        3. Trả về chi tiết đơn đặt tour vừa tạo.
        """
        result = await self._repo.create_booking(
            user_id=user_id,
            tour_id=data.tour_id,
            num_adults=data.num_adults,
            num_children=data.num_children,
            contact_name=data.contact_name,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            special_requests=data.special_requests,
            ip_address=ip_address,
        )

        booking_id = result["booking_id"]

        # Thêm hành khách vào đơn
        for p in data.passengers:
            await self._repo.add_passenger(
                booking_id=booking_id,
                full_name=p.full_name,
                passenger_type=p.passenger_type,
                id_card_number=p.id_card_number,
            )

        logger.info(
            "Đặt tour thành công: mã={} bởi user={}",
            result.get("booking_code"),
            user_id,
        )
        return await self.get_booking(booking_id, current_user_id=user_id)

    async def get_booking(
        self,
        booking_id: uuid.UUID,
        current_user_id: uuid.UUID,
        is_admin: bool = False,
    ) -> BookingResponse:
        """Lấy chi tiết một đơn đặt tour kèm danh sách hành khách."""
        booking = await self._repo.get_by_id(booking_id)
        if not booking:
            raise NotFoundError("Booking", booking_id)

        # Kiểm tra quyền: Chỉ chủ đơn hoặc Admin/Staff mới được xem
        if not is_admin and booking.get("user_id") != current_user_id:
            raise ForbiddenError("Bạn không có quyền xem đơn đặt tour này")

        return _to_booking_detail(booking)

    async def list_my_bookings(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[BookingListResponse]:
        """Xem lịch sử các đơn đặt tour của chính mình."""
        skip = (page - 1) * page_size
        rows, total = await self._repo.get_my_bookings(
            user_id=user_id,
            skip=skip,
            limit=page_size,
        )
        items = [_to_booking_list_item(r) for r in rows]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_all_bookings(
        self,
        *,
        status: Optional[str] = None,
        tour_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[BookingListResponse]:
        """Xem toàn bộ đơn đặt tour trong hệ thống (Admin / Staff)."""
        skip = (page - 1) * page_size
        rows, total = await self._repo.get_all_bookings(
            skip=skip,
            limit=page_size,
            status=status,
            tour_id=tour_id,
        )
        items = [_to_booking_list_item(r) for r in rows]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def cancel_booking(
        self,
        booking_id: uuid.UUID,
        current_user_id: uuid.UUID,
        is_admin: bool = False,
        ip_address: Optional[str] = None,
    ) -> BookingResponse:
        """Hủy đơn đặt tour và tự động hoàn trả chỗ trống cho tour."""
        await self._repo.cancel_booking(
            booking_id=booking_id,
            current_user_id=current_user_id,
            is_admin=is_admin,
            ip_address=ip_address,
        )
        return await self.get_booking(booking_id, current_user_id=current_user_id, is_admin=True)

    async def confirm_booking(
        self,
        booking_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> BookingResponse:
        """Xác nhận đơn đặt tour đã duyệt thanh toán (Admin / Staff)."""
        await self._repo.confirm_booking(
            booking_id=booking_id,
            admin_id=admin_id,
            ip_address=ip_address,
        )
        return await self.get_booking(booking_id, current_user_id=admin_id, is_admin=True)
