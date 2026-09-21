# ============================================================
# Travel Booking System — Tour DTOs
# ============================================================
# Request/Response schemas for Tour CRUD + Search/Filter.
# ============================================================

import uuid
from datetime import date, datetime
from datetime import time as time_type
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --------------- Activity ---------------

class CreateActivityRequest(BaseModel):
    """Input for creating an itinerary activity."""
    time: Optional[time_type] = Field(None, description="Activity time (HH:MM)")
    place_name: str = Field(..., min_length=1, max_length=255, description="Name of the place")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = Field(None, max_length=2000)


class ActivityResponse(BaseModel):
    """Activity info response."""
    id: uuid.UUID
    time: Optional[time_type] = None
    place_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# --------------- Itinerary ---------------

class CreateItineraryRequest(BaseModel):
    """Input for creating an itinerary day."""
    day_number: int = Field(..., ge=1, description="Day number in the tour")
    title: str = Field(..., min_length=1, max_length=500, description="Day title")
    activities: list[CreateActivityRequest] = Field(
        default_factory=list, description="Activities for this day"
    )


class ItineraryResponse(BaseModel):
    """Itinerary day response."""
    id: uuid.UUID
    day_number: int
    title: str
    activities: list[ActivityResponse] = []

    model_config = {"from_attributes": True}


# --------------- Tour ---------------

class CreateTourRequest(BaseModel):
    """Input for creating a new tour."""
    title: str = Field(..., min_length=3, max_length=500, description="Tour title")
    description: Optional[str] = Field(None, max_length=5000, description="Tour description")
    category: Optional[str] = Field(None, max_length=100, description="Tour category")
    tags: Optional[list[str]] = Field(None, description="Tags for searching")
    destination: str = Field(..., min_length=1, max_length=255, description="Destination")
    base_price_adult: Decimal = Field(..., gt=0, description="Adult price")
    base_price_child: Decimal = Field(..., ge=0, description="Child price")
    max_participants: int = Field(..., gt=0, le=1000, description="Maximum participants")
    start_date: date = Field(..., description="Tour start date")
    end_date: date = Field(..., description="Tour end date")
    itineraries: list[CreateItineraryRequest] = Field(
        default_factory=list, description="Itinerary days"
    )

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator("base_price_child")
    @classmethod
    def child_price_not_exceed_adult(cls, v, info):
        adult = info.data.get("base_price_adult")
        if adult is not None and v > adult:
            raise ValueError("Child price cannot exceed adult price")
        return v


class UpdateTourRequest(BaseModel):
    """Input for updating a tour. All fields optional."""
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    destination: Optional[str] = Field(None, min_length=1, max_length=255)
    base_price_adult: Optional[Decimal] = Field(None, gt=0)
    base_price_child: Optional[Decimal] = Field(None, ge=0)
    max_participants: Optional[int] = Field(None, gt=0, le=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TourResponse(BaseModel):
    """Full tour detail response (with itineraries)."""
    id: uuid.UUID
    tour_code: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    destination: str
    base_price_adult: float
    base_price_child: float
    max_participants: int
    available_slots: int
    start_date: date
    end_date: date
    status: str
    created_by: Optional[uuid.UUID] = None
    itineraries: list[ItineraryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TourListResponse(BaseModel):
    """Compact tour response for list views (no itineraries)."""
    id: uuid.UUID
    tour_code: str
    title: str
    category: Optional[str] = None
    destination: str
    base_price_adult: float
    base_price_child: float
    max_participants: int
    available_slots: int
    start_date: date
    end_date: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------- Filter Params ---------------

class TourFilterParams(BaseModel):
    """Query parameters for filtering/searching tours."""
    destination: Optional[str] = Field(None, description="Filter by destination (partial match)")
    category: Optional[str] = Field(None, description="Filter by category")
    status: Optional[str] = Field(None, description="Filter by status")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum adult price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum adult price")
    start_date_from: Optional[date] = Field(None, description="Tours starting from this date")
    start_date_to: Optional[date] = Field(None, description="Tours starting before this date")
    search: Optional[str] = Field(None, description="Full-text search in title/description")
    sort_by: str = Field("created_at", description="Sort field: price, start_date, created_at")
    sort_order: str = Field("desc", description="Sort order: asc, desc")
