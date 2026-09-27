# ============================================================
# Travel Booking System — Middleware Unit Tests
# ============================================================

from __future__ import annotations

import re
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI, Request

from app.core.middleware import register_middlewares
from app.core.config import settings


@pytest.fixture
def test_app():
    """Create a lightweight FastAPI app with registered middlewares for testing."""
    app = FastAPI()
    register_middlewares(app)

    @app.get("/ping")
    async def ping(request: Request):
        return {
            "message": "pong",
            "request_id": getattr(request.state, "request_id", None),
        }

    @app.get("/error")
    async def trigger_error():
        raise ValueError("Simulated server error")

    return app


@pytest.mark.asyncio
async def test_request_id_generated_automatically(test_app):
    """Test that X-Request-ID is generated and attached when not provided by client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    assert len(request_id) > 10
    # Also verify request.state had the same request_id
    assert response.json()["request_id"] == request_id


@pytest.mark.asyncio
async def test_request_id_preserved_from_client(test_app):
    """Test that incoming X-Request-ID is preserved and propagated."""
    custom_id = "custom-trace-id-12345"
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ping", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id
    assert response.json()["request_id"] == custom_id


@pytest.mark.asyncio
async def test_process_time_header(test_app):
    """Test that X-Process-Time is calculated and returned in response."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert "x-process-time" in response.headers
    # Should match format like '1.25ms'
    assert re.match(r"^\d+\.\d{2}ms$", response.headers["x-process-time"])


@pytest.mark.asyncio
async def test_security_headers_present(test_app):
    """Test standard OWASP security headers are present in response."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-xss-protection"] == "1; mode=block"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_hsts_header_in_production(monkeypatch):
    """Test Strict-Transport-Security header is included when APP_ENV is production."""
    monkeypatch.setattr(settings, "APP_ENV", "production")
    
    app = FastAPI()
    register_middlewares(app)

    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert "strict-transport-security" in response.headers
    assert "max-age=31536000" in response.headers["strict-transport-security"]
