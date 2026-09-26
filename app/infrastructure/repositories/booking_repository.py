# ============================================================
# Travel Booking System — Repository: Booking
# ============================================================
# Tầng truy xuất dữ liệu (Data Access Layer) cho Đơn đặt tour.
# Sử dụng SQLAlchemy 2.0 Async Session, cô lập hoàn toàn truy vấn SQL.
# ============================================================

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.booking import Booking, BookingPassenger
from app.domain.value_objects.enums import BookingStatus


class BookingRepository:
    """Repository quản lý dữ liệu Booking và BookingPassenger."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, booking: Booking) -> Booking:
        """Thêm mới một đơn đặt tour vào database."""
        self._session.add(booking)
        await self._session.flush()
        return booking

    async def get_by_id(self, booking_id: uuid.UUID) -> Booking | None:
        """Lấy thông tin chi tiết một đơn đặt tour theo ID (eager load tour và passengers)."""
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.tour),
                selectinload(Booking.passengers),
            )
            .where(Booking.id == booking_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, booking_code: str) -> Booking | None:
        """Lấy đơn đặt tour theo mã code (ví dụ: BK-20260926-XXXX)."""
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.tour),
                selectinload(Booking.passengers),
            )
            .where(Booking.booking_code == booking_code)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_bookings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Booking], int]:
        """Lấy danh sách các đơn đặt tour của một người dùng cụ thể kèm tổng số lượng."""
        # Đếm tổng số
        count_stmt = select(func.count(Booking.id)).where(Booking.user_id == user_id)
        total = (await self._session.execute(count_stmt)).scalar() or 0

        # Lấy danh sách có phân trang và sắp xếp mới nhất
        stmt = (
            select(Booking)
            .options(selectinload(Booking.tour))
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        status: BookingStatus | None = None,
        tour_id: uuid.UUID | None = None,
    ) -> tuple[list[Booking], int]:
        """Lấy toàn bộ danh sách đơn đặt tour (dành cho Admin / Staff quản lý)."""
        stmt = select(Booking).options(selectinload(Booking.tour))

        if status:
            stmt = stmt.where(Booking.status == status)
        if tour_id:
            stmt = stmt.where(Booking.tour_id == tour_id)

        # Đếm tổng số
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        # Lấy dữ liệu phân trang
        stmt = stmt.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_total_booked_seats(self, tour_id: uuid.UUID) -> int:
        """
        Tính tổng số chỗ đã được đặt (chưa bị hủy) cho một tour.
        Bao gồm cả trạng thái PENDING_PAYMENT và CONFIRMED.
        """
        stmt = select(func.sum(Booking.num_adults + Booking.num_children)).where(
            Booking.tour_id == tour_id,
            Booking.status.in_([BookingStatus.PENDING_PAYMENT, BookingStatus.CONFIRMED]),
        )
        result = await self._session.execute(stmt)
        total_seats = result.scalar()
        return int(total_seats) if total_seats is not None else 0

    async def update(self, booking: Booking) -> Booking:
        """Lưu các thay đổi trên booking."""
        await self._session.flush()
        return booking
