# ============================================================
# Travel Booking System — Tour / Itinerary Models
# ============================================================
# Placeholder for Week 2 — only model definitions here for
# migration completeness. Full CRUD in next phase.
# ============================================================

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    ARRAY,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.value_objects.enums import TourStatus
from app.infrastructure.db.base import Base, TimestampMixin, UUIDMixin


class Tour(Base, UUIDMixin, TimestampMixin):
    """Tour catalog entry."""

    __tablename__ = "tours"
    __table_args__ = (
        Index("ix_tours_destination", "destination"),
        Index("ix_tours_category", "category"),
        Index("ix_tours_status", "status"),
        Index("ix_tours_start_date_end_date", "start_date", "end_date"),
        Index("ix_tours_base_price_adult", "base_price_adult"),
    )

    tour_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)

    base_price_adult: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    base_price_child: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    available_slots: Mapped[int] = mapped_column(Integer, nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TourStatus.DRAFT.value,
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    itineraries: Mapped[list[Itinerary]] = relationship(
        "Itinerary",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="Itinerary.day_number",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tour(id={self.id}, code={self.tour_code})>"


class Itinerary(Base, UUIDMixin):
    """A single day within a tour's schedule."""

    __tablename__ = "itineraries"
    __table_args__ = (
        Index("ix_itineraries_tour_id", "tour_id"),
    )

    tour_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tours.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    tour: Mapped[Tour] = relationship("Tour", back_populates="itineraries")
    activities: Mapped[list[ItineraryActivity]] = relationship(
        "ItineraryActivity",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryActivity.time",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Itinerary(id={self.id}, day={self.day_number})>"


class ItineraryActivity(Base, UUIDMixin):
    """An activity within an itinerary day."""

    __tablename__ = "itinerary_activities"
    __table_args__ = (
        Index("ix_itinerary_activities_itinerary_id", "itinerary_id"),
    )

    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        nullable=False,
    )
    time: Mapped[time | None] = mapped_column(Time, nullable=True)
    place_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    itinerary: Mapped[Itinerary] = relationship("Itinerary", back_populates="activities")

    def __repr__(self) -> str:
        return f"<ItineraryActivity(id={self.id}, place={self.place_name})>"
