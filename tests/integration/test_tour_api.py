# ============================================================
# Travel Booking System — Integration Tests: Tour API
# ============================================================

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


class TestTourCRUD:
    """Test Tour CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_tour_as_admin(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        response = await client.post(
            "/api/v1/tours",
            json={
                "title": "Ha Long Bay 3 Days 2 Nights",
                "description": "Explore the UNESCO World Heritage site",
                "category": "Adventure",
                "tags": ["beach", "cruise", "nature"],
                "destination": "Ha Long Bay, Quang Ninh",
                "base_price_adult": 250.00,
                "base_price_child": 125.00,
                "max_participants": 30,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
                "itineraries": [
                    {
                        "day_number": 1,
                        "title": "Day 1 - Departure & Cruise",
                        "activities": [
                            {"place_name": "Hanoi Old Quarter", "time": "06:00", "description": "Pickup point"},
                            {"place_name": "Ha Long Bay Pier", "time": "12:00", "description": "Board cruise ship"},
                        ],
                    },
                    {
                        "day_number": 2,
                        "title": "Day 2 - Explore Caves",
                        "activities": [
                            {"place_name": "Sung Sot Cave", "time": "08:00", "latitude": 20.9, "longitude": 107.1},
                            {"place_name": "Ti Top Island", "time": "14:00"},
                        ],
                    },
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Ha Long Bay 3 Days 2 Nights"
        assert data["destination"] == "Ha Long Bay, Quang Ninh"
        assert data["status"] == "DRAFT"
        assert data["available_slots"] == 30
        assert data["tour_code"].startswith("TOUR-")
        assert len(data["itineraries"]) == 2
        assert len(data["itineraries"][0]["activities"]) == 2

    @pytest.mark.asyncio
    async def test_create_tour_as_customer_forbidden(self, client: AsyncClient, test_user):
        token = create_access_token(
            subject=test_user.id,
            roles=[r.name for r in test_user.roles],
        )
        response = await client.post(
            "/api/v1/tours",
            json={
                "title": "Unauthorized Tour",
                "destination": "Nowhere",
                "base_price_adult": 100.00,
                "base_price_child": 50.00,
                "max_participants": 10,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_tour_detail(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        # Create tour first
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Detail Test Tour",
                "destination": "Da Nang",
                "base_price_adult": 150.00,
                "base_price_child": 75.00,
                "max_participants": 20,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]

        # Get detail
        response = await client.get(f"/api/v1/tours/{tour_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tour_id
        assert data["title"] == "Detail Test Tour"

    @pytest.mark.asyncio
    async def test_get_nonexistent_tour_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/tours/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_tour(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        # Create
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Update Test Tour",
                "destination": "Hoi An",
                "base_price_adult": 100.00,
                "base_price_child": 50.00,
                "max_participants": 15,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]

        # Update
        response = await client.put(
            f"/api/v1/tours/{tour_id}",
            json={"title": "Updated Hoi An Tour", "destination": "Hoi An, Quang Nam"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Hoi An Tour"
        assert data["destination"] == "Hoi An, Quang Nam"


class TestTourStatusTransitions:
    """Test tour publish/cancel/archive status transitions."""

    @pytest.mark.asyncio
    async def test_publish_draft_tour(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        # Create
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Publish Test Tour",
                "destination": "Sapa",
                "base_price_adult": 200.00,
                "base_price_child": 100.00,
                "max_participants": 25,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=34)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "DRAFT"

        # Publish
        response = await client.post(
            f"/api/v1/tours/{tour_id}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "PUBLISHED"

    @pytest.mark.asyncio
    async def test_cannot_publish_non_draft_tour(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        # Create and publish
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Already Published Tour",
                "destination": "Nha Trang",
                "base_price_adult": 180.00,
                "base_price_child": 90.00,
                "max_participants": 20,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=34)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/tours/{tour_id}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Try publish again
        response = await client.post(
            f"/api/v1/tours/{tour_id}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cancel_tour(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Cancel Test Tour",
                "destination": "Phu Quoc",
                "base_price_adult": 300.00,
                "base_price_child": 150.00,
                "max_participants": 30,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=35)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/tours/{tour_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_delete_archives_tour(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Archive Test Tour",
                "destination": "Da Lat",
                "base_price_adult": 120.00,
                "base_price_child": 60.00,
                "max_participants": 15,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/tours/{tour_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Tour archived successfully"

        # Verify it's archived
        detail_resp = await client.get(f"/api/v1/tours/{tour_id}")
        assert detail_resp.json()["status"] == "ARCHIVED"


class TestTourListAndFilter:
    """Test tour list/search/filter functionality."""

    @pytest.mark.asyncio
    async def test_list_tours_public_shows_published(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        # Create and publish a tour
        create_resp = await client.post(
            "/api/v1/tours",
            json={
                "title": "Public Listing Tour",
                "destination": "Hue",
                "base_price_adult": 160.00,
                "base_price_child": 80.00,
                "max_participants": 20,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        tour_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/tours/{tour_id}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Public listing
        response = await client.get("/api/v1/tours")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        # All returned tours should be PUBLISHED
        for item in data["items"]:
            assert item["status"] == "PUBLISHED"

    @pytest.mark.asyncio
    async def test_list_tours_manage_shows_all(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        response = await client.get(
            "/api/v1/tours/manage",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_destination(self, client: AsyncClient, admin_user):
        token = create_access_token(
            subject=admin_user.id,
            roles=[r.name for r in admin_user.roles],
        )
        # Create a unique tour
        await client.post(
            "/api/v1/tours",
            json={
                "title": "Unique Destination Tour",
                "destination": "MuiNeFilterTest",
                "base_price_adult": 100.00,
                "base_price_child": 50.00,
                "max_participants": 10,
                "start_date": str(date.today() + timedelta(days=30)),
                "end_date": str(date.today() + timedelta(days=33)),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Filter (searching via manage to see DRAFT tours)
        response = await client.get(
            "/api/v1/tours/manage?destination=MuiNeFilterTest",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert "MuiNeFilterTest" in item["destination"]
