# ============================================================
# Travel Booking System — Service: Booking
# ============================================================
# Tầng xử lý nghiệp vụ (Business Logic Layer) cho Đặt tour.
# Xử lý tính tiền, kiểm tra số chỗ còn trống, kiểm tra quyền và trạng thái.
# ============================================================

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.booking import (
    BookingListResponse,
    BookingResponse,
    CreateBookingRequest,
    PassengerResponse,
)
from app.application.dto.common import PaginatedResponse
from app.application.services.audit_service import AuditService
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
)
from app.domain.entities.booking import Booking, BookingPassenger
from app.domain.value_objects.enums import AuditAction, BookingStatus, TourStatus
from app.infrastructure.repositories.booking_repository import BookingRepository
from app.infrastructure.repositories.tour_repository import TourRepository


class BookingService:
    """Nghiệp vụ quản lý Đơn đặt tour."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._booking_repo = BookingRepository(session)
        self._tour_repo = TourRepository(session)
        self._audit = AuditService(session)

    # --------------- Helper sinh mã booking ---------------
    def _generate_booking_code(self) -> str:
        """Sinh mã đặt tour duy nhất: BK-YYYYMMDD-XXXXXX"""
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        random_part = uuid.uuid4().hex[:6].upper()
        return f"BK-{today_str}-{random_part}"

    # --------------- Nghiệp vụ tạo đơn đặt tour ---------------
    async def create_booking(
        self,
        user_id: uuid.UUID,
        data: CreateBookingRequest,
        ip_address: str | None = None,
    ) -> BookingResponse:
        """
        Khách hàng tạo đơn đặt tour:
        1. Kiểm tra tour có tồn tại và đang mở bán (PUBLISHED) không.
        2. Kiểm tra số chỗ còn lại trên tour (max_participants).
        3. Tính toán tổng số tiền dựa theo đơn giá người lớn và trẻ em.
        4. Lưu thông tin hành khách và tạo đơn.
        5. Ghi nhật ký Audit Log.
        """
        # 1. Kiểm tra Tour
        tour = await self._tour_repo.get_by_id(data.tour_id)
        if not tour:
            raise NotFoundError(f"Không tìm thấy Tour với ID '{data.tour_id}'")

        if tour.status != TourStatus.PUBLISHED:
            raise BadRequestError(
                f"Tour '{tour.title}' hiện không mở đặt chỗ (Trạng thái: {tour.status.value})"
            )

        # 2. Kiểm tra chỗ trống
        requested_seats = data.num_adults + data.num_children
        already_booked = await self._booking_repo.get_total_booked_seats(tour.id)
        available_seats = tour.max_participants - already_booked

        if requested_seats > available_seats:
            raise BadRequestError(
                f"Tour không đủ chỗ trống. Bạn yêu cầu {requested_seats} chỗ nhưng chỉ còn {max(0, available_seats)} chỗ trống."
            )

        # 3. Tính tổng tiền
        total_price = (Decimal(data.num_adults) * tour.base_price_adult) + (
            Decimal(data.num_children) * tour.base_price_child
        )

        # 4. Khởi tạo đối tượng Booking
        booking = Booking(
            booking_code=self._generate_booking_code(),
            user_id=user_id,
            tour_id=data.tour_id,
            status=BookingStatus.PENDING_PAYMENT,
            num_adults=data.num_adults,
            num_children=data.num_children,
            total_price=total_price,
            contact_name=data.contact_name,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            special_requests=data.special_requests,
        )

        # Thêm danh sách hành khách đi cùng
        passengers_to_add: list[BookingPassenger] = []
        if data.passengers:
            for p in data.passengers:
                passengers_to_add.append(
                    BookingPassenger(
                        full_name=p.full_name,
                        passenger_type=p.passenger_type,
                        id_card_number=p.id_card_number,
                    )
                )
        else:
            # Nếu khách không nhập danh sách chi tiết, tạo mặc định 1 khách chính
            passengers_to_add.append(
                BookingPassenger(
                    full_name=data.contact_name,
                    passenger_type="ADULT",
                )
            )

        booking.passengers = passengers_to_add

        # Lưu vào Database
        booking = await self._booking_repo.create(booking)

        # 5. Ghi Audit Log
        await self._audit.log(
            user_id=user_id,
            action=AuditAction.BOOKING_CREATED.value,
            resource="bookings",
            resource_id=booking.id,
            details={
                "booking_code": booking.booking_code,
                "tour_title": tour.title,
                "total_price": float(total_price),
                "total_seats": requested_seats,
            },
            ip_address=ip_address,
        )

        logger.info(
            "Booking created: code={} | tour={} | total={}",
            booking.booking_code,
            tour.title,
            total_price,
        )

        return self._to_booking_response(booking, tour.title)

    # --------------- Chi tiết đơn đặt tour ---------------
    async def get_booking_detail(
        self,
        booking_id: uuid.UUID,
        current_user_id: uuid.UUID,
        is_admin_or_staff: bool,
    ) -> BookingResponse:
        """Lấy chi tiết đơn đặt tour (chỉ chính chủ hoặc Admin/Staff mới được xem)."""
        booking = await self._booking_repo.get_by_id(booking_id)
        if not booking:
            raise NotFoundError(f"Không tìm thấy đơn đặt tour với ID '{booking_id}'")

        if not is_admin_or_staff and booking.user_id != current_user_id:
            raise ForbiddenError("Bạn không có quyền xem đơn đặt tour của người khác")

        tour_title = booking.tour.title if booking.tour else None
        return self._to_booking_response(booking, tour_title)

    # --------------- Danh sách đơn đặt của tôi ---------------
    async def list_my_bookings(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[BookingListResponse]:
        """Xem lịch sử các tour mà tài khoản hiện tại đã đặt."""
        skip = (page - 1) * page_size
        items, total = await self._booking_repo.get_user_bookings(user_id, skip=skip, limit=page_size)

        response_items = [
            BookingListResponse(
                id=b.id,
                booking_code=b.booking_code,
                tour_id=b.tour_id,
                tour_title=b.tour.title if b.tour else None,
                status=b.status,
                num_adults=b.num_adults,
                num_children=b.num_children,
                total_price=b.total_price,
                contact_name=b.contact_name,
                created_at=b.created_at,
            )
            for b in items
        ]

        return PaginatedResponse.create(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # --------------- Danh sách toàn bộ đơn đặt (Admin/Staff) ---------------
    async def list_all_bookings(
        self,
        page: int = 1,
        page_size: int = 20,
        status: BookingStatus | None = None,
        tour_id: uuid.UUID | None = None,
    ) -> PaginatedResponse[BookingListResponse]:
        """Admin/Staff xem toàn bộ danh sách đơn đặt tour trong hệ thống."""
        skip = (page - 1) * page_size
        items, total = await self._booking_repo.get_all(
            skip=skip,
            limit=page_size,
            status=status,
            tour_id=tour_id,
        )

        response_items = [
            BookingListResponse(
                id=b.id,
                booking_code=b.booking_code,
                tour_id=b.tour_id,
                tour_title=b.tour.title if b.tour else None,
                status=b.status,
                num_adults=b.num_adults,
                num_children=b.num_children,
                total_price=b.total_price,
                contact_name=b.contact_name,
                created_at=b.created_at,
            )
            for b in items
        ]

        return PaginatedResponse.create(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # --------------- Hủy đơn đặt tour ---------------
    async def cancel_booking(
        self,
        booking_id: uuid.UUID,
        current_user_id: uuid.UUID,
        is_admin_or_staff: bool,
        ip_address: str | None = None,
    ) -> BookingResponse:
        """Hủy đơn đặt tour (giải phóng số chỗ trống cho tour)."""
        booking = await self._booking_repo.get_by_id(booking_id)
        if not booking:
            raise NotFoundError(f"Không tìm thấy đơn đặt tour với ID '{booking_id}'")

        if not is_admin_or_staff and booking.user_id != current_user_id:
            raise ForbiddenError("Bạn không có quyền hủy đơn đặt tour này")

        if booking.status == BookingStatus.CANCELLED:
            raise BadRequestError("Đơn đặt tour này đã bị hủy trước đó rồi")

        booking.status = BookingStatus.CANCELLED
        await self._booking_repo.update(booking)

        # Ghi log hủy
        await self._audit.log(
            user_id=current_user_id,
            action=AuditAction.BOOKING_CANCELLED.value,
            resource="bookings",
            resource_id=booking.id,
            details={"booking_code": booking.booking_code, "reason": "Người dùng yêu cầu hủy"},
            ip_address=ip_address,
        )

        logger.info("Booking cancelled: code={}", booking.booking_code)
        tour_title = booking.tour.title if booking.tour else None
        return self._to_booking_response(booking, tour_title)

    # --------------- Xác nhận đơn đặt tour (Admin) ---------------
    async def confirm_booking(
        self,
        booking_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> BookingResponse:
        """Admin xác nhận đơn đặt tour (đã thanh toán thành công)."""
        booking = await self._booking_repo.get_by_id(booking_id)
        if not booking:
            raise NotFoundError(f"Không tìm thấy đơn đặt tour với ID '{booking_id}'")

        if booking.status == BookingStatus.CANCELLED:
            raise BadRequestError("Không thể xác nhận đơn đã bị hủy")

        booking.status = BookingStatus.CONFIRMED
        await self._booking_repo.update(booking)

        logger.info("Booking confirmed by admin: code={}", booking.booking_code)
        tour_title = booking.tour.title if booking.tour else None
        return self._to_booking_response(booking, tour_title)

    # --------------- Format Response Helper ---------------
    def _to_booking_response(self, booking: Booking, tour_title: str | None) -> BookingResponse:
        """Đóng gói thực thể Booking sang DTO trả về."""
        passengers = [
            PassengerResponse(
                id=p.id,
                full_name=p.full_name,
                passenger_type=p.passenger_type,
                id_card_number=p.id_card_number,
            )
            for p in (booking.passengers or [])
        ]

        now = datetime.datetime.now(datetime.timezone.utc)
        return BookingResponse(
            id=booking.id,
            booking_code=booking.booking_code,
            user_id=booking.user_id,
            tour_id=booking.tour_id,
            tour_title=tour_title,
            status=booking.status,
            num_adults=booking.num_adults,
            num_children=booking.num_children,
            total_price=booking.total_price,
            contact_name=booking.contact_name,
            contact_email=booking.contact_email,
            contact_phone=booking.contact_phone,
            special_requests=booking.special_requests,
            passengers=passengers,
            created_at=booking.created_at or now,
            updated_at=booking.updated_at or now,
        )
