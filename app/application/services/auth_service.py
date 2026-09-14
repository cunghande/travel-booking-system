# ============================================================
# Travel Booking System — Auth Service
# ============================================================
# Business logic for authentication (register, login, refresh).
# No DB logic here — delegated to repository.
# ============================================================

from __future__ import annotations

import uuid

from jose import JWTError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.application.dto.user import UserResponse
from app.application.services.audit_service import AuditService
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.entities.user import User
from app.domain.value_objects.enums import AuditAction, RoleName
from app.infrastructure.repositories.user_repository import UserRepository


class AuthService:
    """Authentication service — register, login, refresh tokens."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)
        self._audit = AuditService(session)

    async def register(
        self,
        data: RegisterRequest,
        ip_address: str | None = None,
    ) -> UserResponse:
        """
        Register a new user with CUSTOMER role.

        Raises:
            ConflictError: If email is already registered.
        """
        # Check duplicate email
        if await self._user_repo.email_exists(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered")

        # Create user
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_active=True,
        )
        user = await self._user_repo.create(user)

        # Assign default CUSTOMER role
        customer_role = await self._user_repo.get_role_by_name(RoleName.CUSTOMER.value)
        if customer_role:
            await self._user_repo.assign_role(user, customer_role)

        # Audit log
        await self._audit.log(
            user_id=user.id,
            action=AuditAction.USER_REGISTERED.value,
            resource="users",
            resource_id=user.id,
            ip_address=ip_address,
        )

        logger.info("New user registered | email={}", data.email)
        return UserResponse.model_validate(user)

    async def login(
        self,
        data: LoginRequest,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """
        Authenticate a user and return JWT tokens.

        Raises:
            UnauthorizedError: If credentials are invalid.
        """
        # Find user
        user = await self._user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        # Create tokens
        roles = user.role_names
        access_token = create_access_token(subject=user.id, roles=roles)
        refresh_token = create_refresh_token(subject=user.id)

        # Audit log
        await self._audit.log(
            user_id=user.id,
            action=AuditAction.USER_LOGIN.value,
            resource="users",
            resource_id=user.id,
            ip_address=ip_address,
        )

        logger.info("User logged in | email={}", data.email)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh an access token using a valid refresh token.

        Raises:
            UnauthorizedError: If refresh token is invalid or expired.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token payload")

        user = await self._user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or deactivated")

        # Create new tokens
        roles = user.role_names
        new_access = create_access_token(subject=user.id, roles=roles)
        new_refresh = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
        )

    async def get_current_user(self, user_id: uuid.UUID) -> UserResponse:
        """Get current user profile."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("User not found")
        return UserResponse.model_validate(user)
