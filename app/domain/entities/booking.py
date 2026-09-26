# ============================================================
# Travel Booking System — Domain Entity: Booking
# ============================================================
# Thực thể Quản lý Đơn đặt tour (Booking) và Hành khách (Passenger).
# Áp dụng Clean Architecture: Thực thể độc lập, quy tắc nghiệp vụ rõ ràng.
# ============================================================

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.value_objects.enums import BookingStatus
from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.domain.entities.tour import Tour
    from app.domain.entities.user import User


class Booking(Base, UUIDMixin, TimestampMixin):
    """
    Thực thể Đơn đặt tour du lịch.
    Lưu trữ thông tin khách hàng đặt tour, số lượng người, tổng tiền và trạng thái.
    """

    __tablename__ = "bookings"

    # Mã đặt tour duy nhất (ví dụ: BK-20260926-AB12)
    booking_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)

    # Người đặt (User ID) và Tour được đặt (Tour ID)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tour_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tours.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Trạng thái đơn đặt tour: PENDING_PAYMENT, CONFIRMED, CANCELLED
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status", native_enum=False),
        default=BookingStatus.PENDING_PAYMENT,
        nullable=False,
        index=True,
    )

    # Số lượng hành khách
    num_adults: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    num_children: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Tổng số tiền phải thanh toán (tính tự động từ giá người lớn và trẻ em)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Thông tin liên hệ nhận vé/xác nhận
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=False)

    # Ghi chú hoặc yêu cầu đặc biệt (ví dụ: ăn chay, phòng tầng cao, ...)
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships (Quan hệ liên kết dữ liệu)
    tour: Mapped[Tour] = relationship("Tour", lazy="selectin")
    user: Mapped[User] = relationship("User", lazy="selectin")
    passengers: Mapped[list[BookingPassenger]] = relationship(
        "BookingPassenger",
        back_populates="booking",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def total_passengers(self) -> int:
        """Tổng số lượng khách (người lớn + trẻ em)."""
        return self.num_adults + self.num_children

    def __repr__(self) -> str:
        return f"<Booking(code={self.booking_code}, status={self.status}, total={self.total_price})>"


class BookingPassenger(Base, UUIDMixin, TimestampMixin):
    """
    Thực thể Hành khách trong đơn đặt tour.
    Lưu chi tiết tên từng người đi cùng để phục vụ làm thủ tục, bảo hiểm.
    """

    __tablename__ = "booking_passengers"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    passenger_type: Mapped[str] = mapped_column(String(20), default="ADULT", nullable=False) # ADULT hoặc CHILD
    id_card_number: Mapped[str | None] = mapped_column(String(50), nullable=True) # CCCD / Hộ chiếu

    # Relationship
    booking: Mapped[Booking] = relationship("Booking", back_populates="passengers")

    def __repr__(self) -> str:
        return f"<Passenger(name={self.full_name}, type={self.passenger_type})>"
