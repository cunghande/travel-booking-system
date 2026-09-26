# ============================================================
# Travel Booking System — API Router: Bookings
# ============================================================
# Định nghĩa các endpoints xử lý đơn đặt tour du lịch.
# Phân quyền chặt chẽ giữa Khách hàng (Customer) và Nhân viên (Staff/Admin).
# ============================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request

from app.application.dto.booking import (
    BookingListResponse,
    BookingResponse,
    CreateBookingRequest,
)
from app.application.dto.common import PaginatedResponse
from app.application.services.booking_service import BookingService
from app.core.dependencies import (
    CurrentUser,
    DBSession,
    StaffUser,
    get_client_ip,
)
from app.domain.value_objects.enums import BookingStatus

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=BookingResponse,
    status_code=201,
    summary="Khách hàng tạo đơn đặt tour",
    description="Tạo đơn đặt tour mới, tự động tính tổng tiền và trừ/giữ chỗ trên tour.",
)
async def create_booking(
    data: CreateBookingRequest,
    session: DBSession,
    current_user: CurrentUser,
    request: Request,
) -> BookingResponse:
    service = BookingService(session)
    return await service.create_booking(
        user_id=current_user.id,
        data=data,
        ip_address=get_client_ip(request),
    )


@router.get(
    "/my",
    response_model=PaginatedResponse[BookingListResponse],
    summary="Xem lịch sử đặt tour của bản thân",
    description="Khách hàng tra cứu toàn bộ các tour mình đã đặt và trạng thái hiện tại.",
)
async def list_my_bookings(
    session: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(10, ge=1, le=50, description="Số đơn trên mỗi trang"),
) -> PaginatedResponse[BookingListResponse]:
    service = BookingService(session)
    return await service.list_my_bookings(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "",
    response_model=PaginatedResponse[BookingListResponse],
    summary="Quản lý danh sách toàn bộ đơn đặt tour (Staff/Admin)",
    description="Nhân viên hoặc Quản trị viên xem tất cả các đơn đặt tour trong hệ thống để xử lý.",
)
async def list_all_bookings(
    session: DBSession,
    _: StaffUser,
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số đơn trên mỗi trang"),
    status: BookingStatus | None = Query(None, description="Lọc theo trạng thái đơn"),
    tour_id: uuid.UUID | None = Query(None, description="Lọc theo mã Tour cụ thể"),
) -> PaginatedResponse[BookingListResponse]:
    service = BookingService(session)
    return await service.list_all_bookings(
        page=page,
        page_size=page_size,
        status=status,
        tour_id=tour_id,
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Xem chi tiết một đơn đặt tour",
    description="Xem đầy đủ thông tin đơn, tên tour, tiền vé, danh sách hành khách đi cùng.",
)
async def get_booking_detail(
    booking_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> BookingResponse:
    service = BookingService(session)
    is_staff = any(r.name in ["ADMIN", "STAFF"] for r in current_user.roles)
    return await service.get_booking_detail(
        booking_id=booking_id,
        current_user_id=current_user.id,
        is_admin_or_staff=is_staff,
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Hủy đơn đặt tour",
    description="Khách hàng hoặc Quản trị viên hủy đơn đặt tour (giải phóng số chỗ trống lại cho tour).",
)
async def cancel_booking(
    booking_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
    request: Request,
) -> BookingResponse:
    service = BookingService(session)
    is_staff = any(r.name in ["ADMIN", "STAFF"] for r in current_user.roles)
    return await service.cancel_booking(
        booking_id=booking_id,
        current_user_id=current_user.id,
        is_admin_or_staff=is_staff,
        ip_address=get_client_ip(request),
    )


@router.post(
    "/{booking_id}/confirm",
    response_model=BookingResponse,
    summary="Xác nhận đơn đặt tour đã thanh toán (Staff/Admin)",
    description="Nhân viên/Admin duyệt và chuyển trạng thái đơn sang CONFIRMED.",
)
async def confirm_booking(
    booking_id: uuid.UUID,
    session: DBSession,
    current_user: StaffUser,
    request: Request,
) -> BookingResponse:
    service = BookingService(session)
    return await service.confirm_booking(
        booking_id=booking_id,
        admin_id=current_user.id,
        ip_address=get_client_ip(request),
    )
