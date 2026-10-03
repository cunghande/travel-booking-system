# ============================================================
# Travel Booking System — API Router: Đặt tour (Bookings)
# ============================================================
# Các endpoints: Đặt tour, xem lịch sử đặt chỗ, quản lý toàn bộ đơn (Admin),
# xác nhận duyệt và hủy đơn hoàn vé.
# ============================================================

from typing import Optional
import uuid
from fastapi import APIRouter, Query, Request

from app.application.dto.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
)
from app.application.dto.common import PaginatedResponse
from app.application.services.booking_service import BookingService
from app.core.dependencies import (
    CurrentUser,
    DBConn,
    StaffUser,
    get_client_ip,
)

router = APIRouter(prefix="/bookings", tags=["Quản lý Đặt tour (Bookings)"])


@router.post(
    "",
    response_model=BookingResponse,
    status_code=201,
    summary="Khách hàng tạo đơn đặt tour",
    description="Tạo đơn đặt tour mới, tự động kiểm tra số chỗ và giữ chỗ bằng khóa an toàn trong PostgreSQL.",
)
async def create_booking(
    data: BookingCreate,
    conn: DBConn,
    current_user: CurrentUser,
    request: Request,
) -> BookingResponse:
    service = BookingService(conn)
    return await service.create_booking(
        user_id=current_user["id"],
        data=data,
        ip_address=get_client_ip(request),
    )


@router.get(
    "/my",
    response_model=PaginatedResponse[BookingListResponse],
    summary="Lịch sử đặt tour của bản thân",
    description="Khách hàng tra cứu các tour mình đã đặt và trạng thái hiện tại.",
)
async def list_my_bookings(
    conn: DBConn,
    current_user: CurrentUser,
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(10, ge=1, le=50, description="Số đơn mỗi trang"),
) -> PaginatedResponse[BookingListResponse]:
    service = BookingService(conn)
    return await service.list_my_bookings(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "",
    response_model=PaginatedResponse[BookingListResponse],
    summary="Quản lý toàn bộ đơn đặt tour (Staff / Admin)",
    description="Nhân viên hoặc Admin tra cứu danh sách đơn đặt tour của tất cả khách hàng.",
)
async def list_all_bookings(
    conn: DBConn,
    staff: StaffUser,
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số đơn mỗi trang"),
    status: Optional[str] = Query(None, description="Lọc trạng thái: PENDING_PAYMENT, CONFIRMED, CANCELLED"),
    tour_id: Optional[uuid.UUID] = Query(None, description="Lọc theo Tour ID cụ thể"),
) -> PaginatedResponse[BookingListResponse]:
    service = BookingService(conn)
    return await service.list_all_bookings(
        status=status,
        tour_id=tour_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Xem chi tiết một đơn đặt tour",
    description="Xem thông tin chi tiết đơn, giá vé và danh sách hành khách đi kèm.",
)
async def get_booking(
    booking_id: uuid.UUID,
    conn: DBConn,
    current_user: CurrentUser,
) -> BookingResponse:
    # Kiểm tra xem user có phải Admin hoặc Staff không
    roles = set(current_user.get("roles", []))
    is_admin = bool(roles.intersection({"ADMIN", "STAFF"}))

    service = BookingService(conn)
    return await service.get_booking(
        booking_id=booking_id,
        current_user_id=current_user["id"],
        is_admin=is_admin,
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Hủy đơn đặt tour",
    description="Hủy đơn đặt tour và tự động hoàn trả số chỗ trống về cho tour đó.",
)
async def cancel_booking(
    booking_id: uuid.UUID,
    conn: DBConn,
    current_user: CurrentUser,
    request: Request,
) -> BookingResponse:
    roles = set(current_user.get("roles", []))
    is_admin = bool(roles.intersection({"ADMIN", "STAFF"}))

    service = BookingService(conn)
    return await service.cancel_booking(
        booking_id=booking_id,
        current_user_id=current_user["id"],
        is_admin=is_admin,
        ip_address=get_client_ip(request),
    )


@router.post(
    "/{booking_id}/confirm",
    response_model=BookingResponse,
    summary="Xác nhận duyệt đơn đặt tour (Staff / Admin)",
    description="Nhân viên hoặc Quản trị viên duyệt thanh toán và chuyển trạng thái sang CONFIRMED.",
)
async def confirm_booking(
    booking_id: uuid.UUID,
    conn: DBConn,
    staff: StaffUser,
    request: Request,
) -> BookingResponse:
    service = BookingService(conn)
    return await service.confirm_booking(
        booking_id=booking_id,
        admin_id=staff["id"],
        ip_address=get_client_ip(request),
    )
