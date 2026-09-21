# ============================================================
# Travel Booking System — Tour Repository
# ============================================================
# Data access layer for Tour, Itinerary, ItineraryActivity.
# All DB logic isolated here — services never touch SQLAlchemy.
# ============================================================

from __future__ import annotations

import uuid

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.tour import Itinerary, ItineraryActivity, Tour


class TourRepository:
    """Repository for Tour data access."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # --------------- Eager Loading Options ---------------

    @staticmethod
    def _eager_load():
        """Standard eager loading for tour with itineraries and activities."""
        return selectinload(Tour.itineraries).selectinload(Itinerary.activities)

    # --------------- Tour CRUD ---------------

    async def create(self, tour: Tour) -> Tour:
        """Create a new tour."""
        self._session.add(tour)
        await self._session.flush()
        return tour

    async def get_by_id(self, tour_id: uuid.UUID) -> Tour | None:
        """Get a tour by ID with itineraries and activities."""
        stmt = (
            select(Tour)
            .options(self._eager_load())
            .where(Tour.id == tour_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, tour_code: str) -> Tour | None:
        """Get a tour by tour_code."""
        stmt = (
            select(Tour)
            .options(self._eager_load())
            .where(Tour.tour_code == tour_code)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        destination: str | None = None,
        category: str | None = None,
        status: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        start_date_from=None,
        start_date_to=None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Tour], int]:
        """Get paginated, filtered list of tours with total count."""
        stmt = select(Tour)

        # --- Filters ---
        if destination:
            stmt = stmt.where(Tour.destination.ilike(f"%{destination}%"))
        if category:
            stmt = stmt.where(Tour.category == category)
        if status:
            stmt = stmt.where(Tour.status == status)
        if min_price is not None:
            stmt = stmt.where(Tour.base_price_adult >= min_price)
        if max_price is not None:
            stmt = stmt.where(Tour.base_price_adult <= max_price)
        if start_date_from is not None:
            stmt = stmt.where(Tour.start_date >= start_date_from)
        if start_date_to is not None:
            stmt = stmt.where(Tour.start_date <= start_date_to)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Tour.title.ilike(pattern),
                    Tour.description.ilike(pattern),
                    Tour.destination.ilike(pattern),
                )
            )

        # --- Count ---
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        # --- Sort ---
        sort_column = {
            "price": Tour.base_price_adult,
            "start_date": Tour.start_date,
            "created_at": Tour.created_at,
        }.get(sort_by, Tour.created_at)

        if sort_order == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # --- Paginate ---
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        tours = list(result.scalars().all())

        return tours, total

    async def update(self, tour: Tour) -> Tour:
        """Update a tour (session tracks changes via flush)."""
        await self._session.flush()
        return tour

    async def delete(self, tour: Tour) -> None:
        """Hard delete a tour (cascade deletes itineraries + activities)."""
        await self._session.delete(tour)
        await self._session.flush()

    async def code_exists(self, tour_code: str) -> bool:
        """Check if a tour_code already exists."""
        stmt = select(func.count()).where(Tour.tour_code == tour_code)
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    # --------------- Itinerary Operations ---------------

    async def add_itinerary(self, itinerary: Itinerary) -> Itinerary:
        """Add an itinerary to a tour."""
        self._session.add(itinerary)
        await self._session.flush()
        return itinerary

    async def add_activity(self, activity: ItineraryActivity) -> ItineraryActivity:
        """Add an activity to an itinerary."""
        self._session.add(activity)
        await self._session.flush()
        return activity
