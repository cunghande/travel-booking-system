# ============================================================
# Travel Booking System — Integration Tests: Auth API
# ============================================================

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRegisterEndpoint:
    """Test POST /api/v1/auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"api_test_{uuid.uuid4().hex[:8]}@test.com",
                "full_name": "API Test User",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"].endswith("@test.com")
        assert data["full_name"] == "API Test User"
        assert data["is_active"] is True
        assert any(r["name"] == "CUSTOMER" for r in data["roles"])

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        email = f"dup_{uuid.uuid4().hex[:8]}@test.com"
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "First User",
                "password": "SecurePass123",
            },
        )
        # Duplicate
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Second User",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "full_name": "Bad Email User",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"short_{uuid.uuid4().hex[:8]}@test.com",
                "full_name": "Short Pass User",
                "password": "123",
            },
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    """Test POST /api/v1/auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        email = f"login_{uuid.uuid4().hex[:8]}@test.com"
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Login User",
                "password": "SecurePass123",
            },
        )
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        email = f"wrong_{uuid.uuid4().hex[:8]}@test.com"
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Wrong Pass User",
                "password": "SecurePass123",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword"},
        )
        assert response.status_code == 401


class TestMeEndpoint:
    """Test GET /api/v1/auth/me."""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient):
        email = f"me_{uuid.uuid4().hex[:8]}@test.com"
        # Register + Login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Me User",
                "password": "SecurePass123",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        # Get me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


class TestRefreshEndpoint:
    """Test POST /api/v1/auth/refresh."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient):
        email = f"refresh_{uuid.uuid4().hex[:8]}@test.com"
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Refresh User",
                "password": "SecurePass123",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestRBACEnforcement:
    """Test that RBAC restrictions work correctly."""

    @pytest.mark.asyncio
    async def test_customer_cannot_list_users(self, client: AsyncClient):
        email = f"cust_{uuid.uuid4().hex[:8]}@test.com"
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Customer",
                "password": "SecurePass123",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass123"},
        )
        token = login_resp.json()["access_token"]

        # Try to list users — should be forbidden (CUSTOMER role)
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_list_users(self, client: AsyncClient):
        response = await client.get("/api/v1/users")
        assert response.status_code == 401
