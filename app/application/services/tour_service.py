# ============================================================
# Travel Booking System — Tour Service
# ============================================================
# Business logic for Tour CRUD, search/filter, status transitions.
# ============================================================

from __future__ import annotations

import uuid
from datetime import date

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.common import PaginatedResponse
from app.application.dto.tour import (
    CreateTourRequest,
    TourFilterParams,
    TourListResponse,
    TourResponse,
    UpdateTourRequest,
)
from app.application.services.audit_service import AuditService
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.domain.entities.tour import Itinerary, ItineraryActivity, Tour
from app.domain.value_objects.enums import AuditAction, TourStatus
from app.infrastructure.repositories.tour_repository import TourRepository


class TourService:
    """Business logic for Tour management."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = TourRepository(session)
        self._audit = AuditService(session)

    # --------------- Helpers ---------------

    async def _generate_tour_code(self) -> str:
        """Generate a unique tour code like TOUR-A1B2C3."""
        for _ in range(10):
            code = f"TOUR-{uuid.uuid4().hex[:6].upper()}"
            if not await self._repo.code_exists(code):
                return code
        raise ConflictError("Unable to generate unique tour code, please try again")

    async def _get_tour_or_404(self, tour_id: uuid.UUID) -> Tour:
        """Get tour by ID or raise NotFoundError."""
        tour = await self._repo.get_by_id(tour_id)
        if not tour:
            raise NotFoundError("Tour", tour_id)
        return tour

    @staticmethod
    def _validate_dates(start_date: date, end_date: date) -> None:
        """Validate that end_date is after start_date."""
        if end_date <= start_date:
            raise ValidationError(
                "end_date must be after start_date",
                details={"start_date": str(start_date), "end_date": str(end_date)},
            )

    # --------------- Create ---------------

    async def create_tour(
        self,
        data: CreateTourRequest,
        *,
        created_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> TourResponse:
        """Create a new tour with itineraries and activities."""
        # Generate unique tour code
        tour_code = await self._generate_tour_code()

        # Create tour entity
        tour = Tour(
            tour_code=tour_code,
            title=data.title,
            description=data.description,
            category=data.category,
            tags=data.tags,
            destination=data.destination,
            base_price_adult=float(data.base_price_adult),
            base_price_child=float(data.base_price_child),
            max_participants=data.max_participants,
            available_slots=data.max_participants,
            start_date=data.start_date,
            end_date=data.end_date,
            status=TourStatus.DRAFT.value,
            created_by=created_by,
        )
        await self._repo.create(tour)

        # Create itineraries and activities
        for itin_data in data.itineraries:
            itinerary = Itinerary(
                tour_id=tour.id,
                day_number=itin_data.day_number,
                title=itin_data.title,
            )
            await self._repo.add_itinerary(itinerary)

            for act_data in itin_data.activities:
                activity = ItineraryActivity(
                    itinerary_id=itinerary.id,
                    time=act_data.time,
                    place_name=act_data.place_name,
                    latitude=act_data.latitude,
                    longitude=act_data.longitude,
                    description=act_data.description,
                )
                await self._repo.add_activity(activity)

        await self._session.commit()

        # Audit
        await self._audit.log(
            user_id=created_by,
            action=AuditAction.TOUR_CREATED.value,
            resource="Tour",
            resource_id=tour.id,
            details={"tour_code": tour_code, "title": data.title},
            ip_address=ip_address,
        )

        # Reload with relationships
        tour = await self._repo.get_by_id(tour.id)
        logger.info("Tour created: {} ({})", tour.title, tour.tour_code)
        return TourResponse.model_validate(tour)

    # --------------- Read ---------------

    async def get_tour(self, tour_id: uuid.UUID) -> TourResponse:
        """Get a single tour by ID."""
        tour = await self._get_tour_or_404(tour_id)
        return TourResponse.model_validate(tour)

    async def list_tours(
        self,
        filters: TourFilterParams,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TourListResponse]:
        """List tours with search/filter/pagination."""
        skip = (page - 1) * page_size
        tours, total = await self._repo.get_all(
            skip=skip,
            limit=page_size,
            destination=filters.destination,
            category=filters.category,
            status=filters.status,
            min_price=filters.min_price,
            max_price=filters.max_price,
            start_date_from=filters.start_date_from,
            start_date_to=filters.start_date_to,
            search=filters.search,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )

        items = [TourListResponse.model_validate(t) for t in tours]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # --------------- Update ---------------

    async def update_tour(
        self,
        tour_id: uuid.UUID,
        data: UpdateTourRequest,
        *,
        updated_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> TourResponse:
        """Update a tour's details."""
        tour = await self._get_tour_or_404(tour_id)

        # Only DRAFT tours can be fully edited
        if tour.status not in (TourStatus.DRAFT.value, TourStatus.PUBLISHED.value):
            raise BadRequestError(
                f"Cannot update tour in '{tour.status}' status"
            )

        # Apply partial updates
        update_data = data.model_dump(exclude_unset=True)
        changes = {}

        for field, value in update_data.items():
            old_value = getattr(tour, field, None)
            if old_value != value:
                setattr(tour, field, value)
                changes[field] = {"old": str(old_value), "new": str(value)}

        if not changes:
            return TourResponse.model_validate(tour)

        # Validate dates if either changed
        start = data.start_date or tour.start_date
        end = data.end_date or tour.end_date
        self._validate_dates(start, end)

        # Validate available_slots vs max_participants
        if data.max_participants is not None:
            booked = tour.max_participants - tour.available_slots
            if data.max_participants < booked:
                raise ValidationError(
                    f"Cannot reduce max_participants below {booked} (already booked)"
                )
            tour.available_slots = data.max_participants - booked

        await self._repo.update(tour)
        await self._session.commit()

        # Audit
        await self._audit.log(
            user_id=updated_by,
            action=AuditAction.TOUR_UPDATED.value,
            resource="Tour",
            resource_id=tour.id,
            details=changes,
            ip_address=ip_address,
        )

        tour = await self._repo.get_by_id(tour.id)
        logger.info("Tour updated: {} ({})", tour.title, tour.tour_code)
        return TourResponse.model_validate(tour)

    # --------------- Delete (Archive) ---------------

    async def delete_tour(
        self,
        tour_id: uuid.UUID,
        *,
        deleted_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        """Archive a tour (soft delete — set status to ARCHIVED)."""
        tour = await self._get_tour_or_404(tour_id)

        if tour.status == TourStatus.ARCHIVED.value:
            raise BadRequestError("Tour is already archived")

        # Check if there are confirmed bookings (placeholder for future)
        booked = tour.max_participants - tour.available_slots
        if booked > 0 and tour.status == TourStatus.PUBLISHED.value:
            raise BadRequestError(
                f"Cannot archive tour with {booked} active bookings. Cancel bookings first."
            )

        tour.status = TourStatus.ARCHIVED.value
        await self._repo.update(tour)
        await self._session.commit()

        # Audit
        await self._audit.log(
            user_id=deleted_by,
            action=AuditAction.TOUR_DELETED.value,
            resource="Tour",
            resource_id=tour.id,
            details={"tour_code": tour.tour_code},
            ip_address=ip_address,
        )
        logger.info("Tour archived: {} ({})", tour.title, tour.tour_code)

    # --------------- Publish ---------------

    async def publish_tour(
        self,
        tour_id: uuid.UUID,
        *,
        published_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> TourResponse:
        """Publish a tour — transition DRAFT → PUBLISHED."""
        tour = await self._get_tour_or_404(tour_id)

        if tour.status != TourStatus.DRAFT.value:
            raise BadRequestError(
                f"Only DRAFT tours can be published. Current status: {tour.status}"
            )

        # Validate tour is complete enough to publish
        if tour.max_participants <= 0:
            raise ValidationError("Tour must have max_participants > 0 to publish")
        if tour.start_date <= date.today():
            raise ValidationError("Tour start_date must be in the future to publish")

        tour.status = TourStatus.PUBLISHED.value
        await self._repo.update(tour)
        await self._session.commit()

        # Audit
        await self._audit.log(
            user_id=published_by,
            action=AuditAction.TOUR_PUBLISHED.value,
            resource="Tour",
            resource_id=tour.id,
            details={"tour_code": tour.tour_code},
            ip_address=ip_address,
        )

        tour = await self._repo.get_by_id(tour.id)
        logger.info("Tour published: {} ({})", tour.title, tour.tour_code)
        return TourResponse.model_validate(tour)

    # --------------- Cancel ---------------

    async def cancel_tour(
        self,
        tour_id: uuid.UUID,
        *,
        cancelled_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> TourResponse:
        """Cancel a tour — any status → CANCELLED."""
        tour = await self._get_tour_or_404(tour_id)

        if tour.status == TourStatus.CANCELLED.value:
            raise BadRequestError("Tour is already cancelled")

        tour.status = TourStatus.CANCELLED.value
        await self._repo.update(tour)
        await self._session.commit()

        # Audit
        await self._audit.log(
            user_id=cancelled_by,
            action=AuditAction.TOUR_DELETED.value,
            resource="Tour",
            resource_id=tour.id,
            details={"tour_code": tour.tour_code, "action": "CANCELLED"},
            ip_address=ip_address,
        )

        tour = await self._repo.get_by_id(tour.id)
        logger.info("Tour cancelled: {} ({})", tour.title, tour.tour_code)
        return TourResponse.model_validate(tour)
