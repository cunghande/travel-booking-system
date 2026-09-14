# ============================================================
# Travel Booking System — Unit Tests: Auth Service
# ============================================================

from __future__ import annotations

import pytest
import uuid

from unittest.mock import AsyncMock, MagicMock, patch

from app.application.dto.auth import LoginRequest, RegisterRequest
from app.application.services.auth_service import AuthService
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password_returns_hash(self):
        hashed = hash_password("MyPassword123")
        assert hashed != "MyPassword123"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        hashed = hash_password("MyPassword123")
        assert verify_password("MyPassword123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("MyPassword123")
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        hash1 = hash_password("MyPassword123")
        hash2 = hash_password("MyPassword123")
        # bcrypt produces different salts each time
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password("MyPassword123", hash1)
        assert verify_password("MyPassword123", hash2)


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        from app.core.security import create_access_token, decode_token

        user_id = uuid.uuid4()
        token = create_access_token(subject=user_id, roles=["CUSTOMER"])
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert payload["roles"] == ["CUSTOMER"]

    def test_create_refresh_token(self):
        from app.core.security import create_refresh_token, decode_token

        user_id = uuid.uuid4()
        token = create_refresh_token(subject=user_id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        from jose import JWTError
        from app.core.security import decode_token

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_access_token_contains_roles(self):
        from app.core.security import create_access_token, decode_token

        token = create_access_token(
            subject=uuid.uuid4(),
            roles=["ADMIN", "STAFF"],
        )
        payload = decode_token(token)
        assert set(payload["roles"]) == {"ADMIN", "STAFF"}


class TestAuthServiceRegister:
    """Test AuthService.register()."""

    @pytest.mark.asyncio
    async def test_register_success(self, db_session):
        service = AuthService(db_session)
        data = RegisterRequest(
            email=f"newuser_{uuid.uuid4().hex[:8]}@test.com",
            full_name="New User",
            password="SecurePass123",
        )
        result = await service.register(data)

        assert result.email == data.email
        assert result.full_name == data.full_name
        assert result.is_active is True
        assert any(r.name == "CUSTOMER" for r in result.roles)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db_session, test_user):
        service = AuthService(db_session)
        data = RegisterRequest(
            email=test_user.email,
            full_name="Another User",
            password="SecurePass123",
        )
        with pytest.raises(ConflictError):
            await service.register(data)


class TestAuthServiceLogin:
    """Test AuthService.login()."""

    @pytest.mark.asyncio
    async def test_login_success(self, db_session):
        # First register
        service = AuthService(db_session)
        email = f"login_{uuid.uuid4().hex[:8]}@test.com"
        reg_data = RegisterRequest(
            email=email,
            full_name="Login User",
            password="SecurePass123",
        )
        await service.register(reg_data)

        # Then login
        login_data = LoginRequest(email=email, password="SecurePass123")
        result = await service.login(login_data)

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session, test_user):
        service = AuthService(db_session)
        login_data = LoginRequest(email=test_user.email, password="WrongPassword")
        with pytest.raises(UnauthorizedError):
            await service.login(login_data)

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, db_session):
        service = AuthService(db_session)
        login_data = LoginRequest(email="nonexistent@test.com", password="Whatever123")
        with pytest.raises(UnauthorizedError):
            await service.login(login_data)


class TestAuthServiceRefresh:
    """Test AuthService.refresh_token()."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, db_session):
        service = AuthService(db_session)
        email = f"refresh_{uuid.uuid4().hex[:8]}@test.com"
        # Register + Login
        await service.register(
            RegisterRequest(email=email, full_name="Refresh User", password="SecurePass123")
        )
        tokens = await service.login(LoginRequest(email=email, password="SecurePass123"))

        # Refresh
        new_tokens = await service.refresh_token(tokens.refresh_token)
        assert new_tokens.access_token
        assert new_tokens.refresh_token
        assert new_tokens.access_token != tokens.access_token

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, db_session):
        service = AuthService(db_session)
        with pytest.raises(UnauthorizedError):
            await service.refresh_token("invalid.refresh.token")

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, db_session):
        service = AuthService(db_session)
        email = f"refresh_fail_{uuid.uuid4().hex[:8]}@test.com"
        await service.register(
            RegisterRequest(email=email, full_name="Fail User", password="SecurePass123")
        )
        tokens = await service.login(LoginRequest(email=email, password="SecurePass123"))

        # Using access token as refresh should fail
        with pytest.raises(UnauthorizedError):
            await service.refresh_token(tokens.access_token)
