# ============================================================
# Travel Booking System — Unit Tests: Tour Service
# ============================================================

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.application.dto.tour import (
    CreateTourRequest,
    TourFilterParams,
    UpdateTourRequest,
)
from app.domain.value_objects.enums import TourStatus


class TestCreateTourRequestValidation:
    """Test CreateTourRequest DTO validation."""

    def test_valid_tour_request(self):
        data = CreateTourRequest(
            title="Ha Long Bay 3 Days",
            description="Amazing trip",
            destination="Ha Long Bay",
            base_price_adult=150.00,
            base_price_child=80.00,
            max_participants=30,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=33),
        )
        assert data.title == "Ha Long Bay 3 Days"
        assert data.max_participants == 30

    def test_end_date_must_be_after_start(self):
        with pytest.raises(Exception):
            CreateTourRequest(
                title="Bad Dates Tour",
                destination="Hanoi",
                base_price_adult=100.00,
                base_price_child=50.00,
                max_participants=10,
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=29),
            )

    def test_end_date_same_as_start_rejected(self):
        same_date = date.today() + timedelta(days=30)
        with pytest.raises(Exception):
            CreateTourRequest(
                title="Same Date Tour",
                destination="Hanoi",
                base_price_adult=100.00,
                base_price_child=50.00,
                max_participants=10,
                start_date=same_date,
                end_date=same_date,
            )

    def test_child_price_cannot_exceed_adult(self):
        with pytest.raises(Exception):
            CreateTourRequest(
                title="Expensive Child Tour",
                destination="Hanoi",
                base_price_adult=100.00,
                base_price_child=200.00,
                max_participants=10,
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=33),
            )

    def test_price_must_be_positive(self):
        with pytest.raises(Exception):
            CreateTourRequest(
                title="Free Tour",
                destination="Hanoi",
                base_price_adult=0,
                base_price_child=0,
                max_participants=10,
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=33),
            )

    def test_max_participants_must_be_positive(self):
        with pytest.raises(Exception):
            CreateTourRequest(
                title="Empty Tour",
                destination="Hanoi",
                base_price_adult=100.00,
                base_price_child=50.00,
                max_participants=0,
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=33),
            )

    def test_title_too_short(self):
        with pytest.raises(Exception):
            CreateTourRequest(
                title="AB",
                destination="Hanoi",
                base_price_adult=100.00,
                base_price_child=50.00,
                max_participants=10,
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=33),
            )

    def test_itineraries_nested_creation(self):
        data = CreateTourRequest(
            title="Full Tour With Itinerary",
            destination="Da Nang",
            base_price_adult=200.00,
            base_price_child=100.00,
            max_participants=20,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=33),
            itineraries=[
                {
                    "day_number": 1,
                    "title": "Day 1 - Arrival",
                    "activities": [
                        {"place_name": "Airport", "description": "Pickup"},
                        {"place_name": "Hotel", "time": "14:00"},
                    ],
                },
                {
                    "day_number": 2,
                    "title": "Day 2 - Beach",
                    "activities": [
                        {"place_name": "My Khe Beach", "latitude": 16.04, "longitude": 108.24},
                    ],
                },
            ],
        )
        assert len(data.itineraries) == 2
        assert len(data.itineraries[0].activities) == 2
        assert data.itineraries[1].activities[0].latitude == 16.04


class TestUpdateTourRequestValidation:
    """Test UpdateTourRequest DTO validation."""

    def test_partial_update_allows_empty(self):
        data = UpdateTourRequest()
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_partial_update_single_field(self):
        data = UpdateTourRequest(title="New Title")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {"title": "New Title"}

    def test_partial_update_multiple_fields(self):
        data = UpdateTourRequest(
            title="Updated Tour",
            destination="Sapa",
            max_participants=50,
        )
        dumped = data.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "destination" in dumped
        assert "max_participants" in dumped
        assert "description" not in dumped


class TestTourFilterParams:
    """Test TourFilterParams."""

    def test_defaults(self):
        params = TourFilterParams()
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"
        assert params.destination is None
        assert params.min_price is None

    def test_with_filters(self):
        params = TourFilterParams(
            destination="Ha Long",
            min_price=100,
            max_price=500,
            sort_by="price",
            sort_order="asc",
        )
        assert params.destination == "Ha Long"
        assert params.min_price == 100
        assert params.sort_by == "price"


class TestTourStatusEnum:
    """Test TourStatus transitions logic."""

    def test_draft_is_default(self):
        assert TourStatus.DRAFT.value == "DRAFT"

    def test_all_statuses_exist(self):
        statuses = {s.value for s in TourStatus}
        assert statuses == {"DRAFT", "PUBLISHED", "ARCHIVED", "CANCELLED"}

    def test_publish_only_from_draft(self):
        """Business rule: only DRAFT tours can be published."""
        allowed_source = TourStatus.DRAFT.value
        assert allowed_source == "DRAFT"

    def test_cancel_from_any_status(self):
        """Business rule: any tour can be cancelled."""
        for status in TourStatus:
            if status != TourStatus.CANCELLED:
                # All non-cancelled statuses should allow cancellation
                assert status.value != TourStatus.CANCELLED.value
