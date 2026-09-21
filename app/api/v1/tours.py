# ============================================================
# Travel Booking System — Tour API Routes
# ============================================================
# CRUD + Search/Filter + Status transitions for Tours.
# ============================================================

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request

from app.application.dto.common import MessageResponse, PaginatedResponse
from app.application.dto.tour import (
    CreateTourRequest,
    TourFilterParams,
    TourListResponse,
    TourResponse,
    UpdateTourRequest,
)
from app.application.services.tour_service import TourService
from app.core.dependencies import (
    AdminUser,
    CurrentUser,
    DBSession,
    StaffUser,
    get_client_ip,
)

router = APIRouter(prefix="/tours", tags=["Tour Management"])


# --------------- Create ---------------

@router.post(
    "",
    response_model=TourResponse,
    status_code=201,
    summary="Create a new tour",
    description="Staff/Admin only. Create a tour with itineraries and activities.",
)
async def create_tour(
    data: CreateTourRequest,
    session: DBSession,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(session)
    return await service.create_tour(
        data,
        created_by=staff.id,
        ip_address=get_client_ip(request),
    )


# --------------- List / Search ---------------

@router.get(
    "",
    response_model=PaginatedResponse[TourListResponse],
    summary="List tours with search and filters",
    description="Public: shows PUBLISHED tours. Staff/Admin: shows all statuses.",
)
async def list_tours(
    session: DBSession,
    destination: str | None = Query(None, description="Filter by destination"),
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status"),
    min_price: float | None = Query(None, ge=0, description="Min adult price"),
    max_price: float | None = Query(None, ge=0, description="Max adult price"),
    start_date_from: date | None = Query(None, description="Tours starting from"),
    start_date_to: date | None = Query(None, description="Tours starting before"),
    search: str | None = Query(None, description="Search in title/description"),
    sort_by: str = Query("created_at", description="Sort: price, start_date, created_at"),
    sort_order: str = Query("desc", description="Order: asc, desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TourListResponse]:
    # For now, public endpoint — filter by PUBLISHED by default if no status given
    filters = TourFilterParams(
        destination=destination,
        category=category,
        status=status or "PUBLISHED",
        min_price=min_price,
        max_price=max_price,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    service = TourService(session)
    return await service.list_tours(filters, page=page, page_size=page_size)


@router.get(
    "/manage",
    response_model=PaginatedResponse[TourListResponse],
    summary="List all tours (all statuses)",
    description="Staff/Admin only. Shows tours in all statuses for management.",
)
async def list_tours_manage(
    session: DBSession,
    staff: StaffUser,
    destination: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    start_date_from: date | None = Query(None),
    start_date_to: date | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TourListResponse]:
    filters = TourFilterParams(
        destination=destination,
        category=category,
        status=status,  # None = all statuses
        min_price=min_price,
        max_price=max_price,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    service = TourService(session)
    return await service.list_tours(filters, page=page, page_size=page_size)


# --------------- Detail ---------------

@router.get(
    "/{tour_id}",
    response_model=TourResponse,
    summary="Get tour details",
    description="Get full tour information including itineraries and activities.",
)
async def get_tour(
    tour_id: uuid.UUID,
    session: DBSession,
) -> TourResponse:
    service = TourService(session)
    return await service.get_tour(tour_id)


# --------------- Update ---------------

@router.put(
    "/{tour_id}",
    response_model=TourResponse,
    summary="Update a tour",
    description="Staff/Admin only. Update tour details.",
)
async def update_tour(
    tour_id: uuid.UUID,
    data: UpdateTourRequest,
    session: DBSession,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(session)
    return await service.update_tour(
        tour_id,
        data,
        updated_by=staff.id,
        ip_address=get_client_ip(request),
    )


# --------------- Delete (Archive) ---------------

@router.delete(
    "/{tour_id}",
    response_model=MessageResponse,
    summary="Archive a tour",
    description="Admin only. Soft-delete (archive) a tour.",
)
async def delete_tour(
    tour_id: uuid.UUID,
    session: DBSession,
    request: Request,
    admin: AdminUser,
) -> MessageResponse:
    service = TourService(session)
    await service.delete_tour(
        tour_id,
        deleted_by=admin.id,
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="Tour archived successfully")


# --------------- Publish ---------------

@router.post(
    "/{tour_id}/publish",
    response_model=TourResponse,
    summary="Publish a tour",
    description="Staff/Admin only. Transition DRAFT -> PUBLISHED.",
)
async def publish_tour(
    tour_id: uuid.UUID,
    session: DBSession,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(session)
    return await service.publish_tour(
        tour_id,
        published_by=staff.id,
        ip_address=get_client_ip(request),
    )


# --------------- Cancel ---------------

@router.post(
    "/{tour_id}/cancel",
    response_model=TourResponse,
    summary="Cancel a tour",
    description="Admin only. Cancel a tour.",
)
async def cancel_tour(
    tour_id: uuid.UUID,
    session: DBSession,
    request: Request,
    admin: AdminUser,
) -> TourResponse:
    service = TourService(session)
    return await service.cancel_tour(
        tour_id,
        cancelled_by=admin.id,
        ip_address=get_client_ip(request),
    )
