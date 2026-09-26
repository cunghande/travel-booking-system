# ============================================================
# Travel Booking System — Unit Tests: Booking Service
# ============================================================
# Kiểm thử toàn diện logic nghiệp vụ Đặt tour:
# - Validate dữ liệu đầu vào (số lượng vé, email, họ tên)
# - Tính toán tổng số tiền vé
# - Kiểm tra trạng thái tour và số chỗ trống
# - Quy tắc hủy và duyệt đơn đặt tour
# ============================================================

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.dto.booking import CreateBookingRequest, PassengerCreateRequest
from app.application.services.booking_service import BookingService
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.domain.entities.booking import Booking, BookingPassenger
from app.domain.entities.tour import Tour
from app.domain.value_objects.enums import BookingStatus, TourStatus


class TestBookingDTOValidation:
    """Kiểm tra tính hợp lệ của DTO đầu vào."""

    def test_valid_booking_request(self):
        req = CreateBookingRequest(
            tour_id=uuid.uuid4(),
            num_adults=2,
            num_children=1,
            contact_name="Nguyen Van A",
            contact_email="test@example.com",
            contact_phone="0912345678",
            special_requests="Cần phòng không hút thuốc",
            passengers=[
                PassengerCreateRequest(full_name="Nguyen Van A", passenger_type="ADULT"),
                PassengerCreateRequest(full_name="Tran Thi B", passenger_type="ADULT"),
                PassengerCreateRequest(full_name="Nguyen Van C", passenger_type="CHILD"),
            ],
        )
        assert req.num_adults == 2
        assert req.num_children == 1
        assert len(req.passengers) == 3

    def test_adults_must_be_at_least_one(self):
        with pytest.raises(ValueError):
            CreateBookingRequest(
                tour_id=uuid.uuid4(),
                num_adults=0,  # Không được = 0
                num_children=1,
                contact_name="Nguyen Van A",
                contact_email="test@example.com",
                contact_phone="0912345678",
            )

    def test_invalid_email_format(self):
        with pytest.raises(ValueError):
            CreateBookingRequest(
                tour_id=uuid.uuid4(),
                num_adults=1,
                contact_name="Nguyen Van A",
                contact_email="not-an-email",  # Sai định dạng
                contact_phone="0912345678",
            )

    def test_invalid_passenger_type(self):
        with pytest.raises(ValueError):
            PassengerCreateRequest(
                full_name="Nguyen Van A",
                passenger_type="BABY",  # Chỉ chấp nhận ADULT hoặc CHILD
            )


class TestBookingBusinessLogic:
    """Kiểm thử các quy tắc nghiệp vụ trong BookingService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def sample_tour(self):
        tour = MagicMock(spec=Tour)
        tour.id = uuid.uuid4()
        tour.title = "Tour Nha Trang 3N2Đ"
        tour.status = TourStatus.PUBLISHED
        tour.base_price_adult = Decimal("200.00")
        tour.base_price_child = Decimal("100.00")
        tour.max_participants = 20
        return tour

    @pytest.mark.asyncio
    async def test_create_booking_calculates_correct_price(self, mock_session, sample_tour):
        service = BookingService(mock_session)
        service._tour_repo.get_by_id = AsyncMock(return_value=sample_tour)
        service._booking_repo.get_total_booked_seats = AsyncMock(return_value=5)

        # Giả lập lưu booking thành công
        def fake_create(b):
            b.id = uuid.uuid4()
            return b

        service._booking_repo.create = AsyncMock(side_effect=fake_create)
        service._audit.log = AsyncMock()

        req = CreateBookingRequest(
            tour_id=sample_tour.id,
            num_adults=3,
            num_children=2,
            contact_name="Le Van B",
            contact_email="levanb@gmail.com",
            contact_phone="0987654321",
        )

        res = await service.create_booking(user_id=uuid.uuid4(), data=req)

        # 3 * 200 + 2 * 100 = 800.00
        assert res.total_price == Decimal("800.00")
        assert res.booking_code.startswith("BK-")
        assert res.status == BookingStatus.PENDING_PAYMENT
        assert res.tour_title == "Tour Nha Trang 3N2Đ"

    @pytest.mark.asyncio
    async def test_cannot_book_tour_not_published(self, mock_session, sample_tour):
        sample_tour.status = TourStatus.DRAFT  # Tour đang ở dạng nháp
        service = BookingService(mock_session)
        service._tour_repo.get_by_id = AsyncMock(return_value=sample_tour)

        req = CreateBookingRequest(
            tour_id=sample_tour.id,
            num_adults=1,
            contact_name="Le Van B",
            contact_email="levanb@gmail.com",
            contact_phone="0987654321",
        )

        with pytest.raises(BadRequestError) as exc_info:
            await service.create_booking(user_id=uuid.uuid4(), data=req)
        assert "không mở đặt chỗ" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cannot_book_exceeding_seats(self, mock_session, sample_tour):
        # Tour có 20 chỗ, đã đặt 18 chỗ, khách muốn đặt thêm 3 chỗ (18 + 3 = 21 > 20)
        service = BookingService(mock_session)
        service._tour_repo.get_by_id = AsyncMock(return_value=sample_tour)
        service._booking_repo.get_total_booked_seats = AsyncMock(return_value=18)

        req = CreateBookingRequest(
            tour_id=sample_tour.id,
            num_adults=2,
            num_children=1,
            contact_name="Le Van B",
            contact_email="levanb@gmail.com",
            contact_phone="0987654321",
        )

        with pytest.raises(BadRequestError) as exc_info:
            await service.create_booking(user_id=uuid.uuid4(), data=req)
        assert "không đủ chỗ trống" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_user_cannot_cancel_others_booking(self, mock_session):
        service = BookingService(mock_session)
        owner_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        mock_booking = MagicMock(spec=Booking)
        mock_booking.id = uuid.uuid4()
        mock_booking.user_id = owner_id
        mock_booking.status = BookingStatus.PENDING_PAYMENT

        service._booking_repo.get_by_id = AsyncMock(return_value=mock_booking)

        with pytest.raises(ForbiddenError):
            await service.cancel_booking(
                booking_id=mock_booking.id,
                current_user_id=other_user_id,
                is_admin_or_staff=False,
            )

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_booking_fails(self, mock_session):
        service = BookingService(mock_session)
        owner_id = uuid.uuid4()

        mock_booking = MagicMock(spec=Booking)
        mock_booking.id = uuid.uuid4()
        mock_booking.user_id = owner_id
        mock_booking.status = BookingStatus.CANCELLED

        service._booking_repo.get_by_id = AsyncMock(return_value=mock_booking)

        with pytest.raises(BadRequestError) as exc_info:
            await service.cancel_booking(
                booking_id=mock_booking.id,
                current_user_id=owner_id,
                is_admin_or_staff=False,
            )
        assert "đã bị hủy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_admin_confirm_booking_success(self, mock_session):
        service = BookingService(mock_session)
        mock_booking = MagicMock(spec=Booking)
        mock_booking.id = uuid.uuid4()
        mock_booking.booking_code = "BK-20260926-123456"
        mock_booking.user_id = uuid.uuid4()
        mock_booking.tour_id = uuid.uuid4()
        mock_booking.status = BookingStatus.PENDING_PAYMENT
        mock_booking.num_adults = 2
        mock_booking.num_children = 0
        mock_booking.total_price = Decimal("400.00")
        mock_booking.contact_name = "Nguyen A"
        mock_booking.contact_email = "a@gmail.com"
        mock_booking.contact_phone = "0123456789"
        mock_booking.special_requests = None
        mock_booking.passengers = []
        mock_booking.created_at = None
        mock_booking.updated_at = None
        mock_booking.tour = MagicMock(title="Ha Long")

        service._booking_repo.get_by_id = AsyncMock(return_value=mock_booking)
        service._booking_repo.update = AsyncMock()

        res = await service.confirm_booking(
            booking_id=mock_booking.id,
            admin_id=uuid.uuid4(),
        )

        assert mock_booking.status == BookingStatus.CONFIRMED
