# ============================================================
# Travel Booking System — User Management Service
# ============================================================
# Admin-only operations: list users, update, deactivate, manage roles.
# ============================================================

from __future__ import annotations

import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.common import PaginatedResponse
from app.application.dto.user import (
    AssignRoleRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.application.services.audit_service import AuditService
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.domain.value_objects.enums import AuditAction
from app.infrastructure.repositories.user_repository import UserRepository


class UserService:
    """User management service (Admin operations)."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)
        self._audit = AuditService(session)

    async def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> PaginatedResponse[UserResponse]:
        """List all users with pagination (Admin only)."""
        skip = (page - 1) * page_size
        users, total = await self._user_repo.get_all(
            skip=skip,
            limit=page_size,
            is_active=is_active,
        )
        items = [UserResponse.model_validate(u) for u in users]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        """Get a single user by ID."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: uuid.UUID,
        data: UpdateUserRequest,
        *,
        admin_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> UserResponse:
        """Update user profile (Admin only)."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        # Check email conflict
        if data.email and data.email != user.email:
            if await self._user_repo.email_exists(data.email):
                raise ConflictError(f"Email '{data.email}' is already in use")
            user.email = data.email

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.is_active is not None:
            user.is_active = data.is_active

        await self._user_repo.update(user)

        # Audit
        action = AuditAction.USER_DEACTIVATED if data.is_active is False else AuditAction.USER_UPDATED
        await self._audit.log(
            user_id=admin_id,
            action=action.value,
            resource="users",
            resource_id=user_id,
            ip_address=ip_address,
        )

        logger.info("User updated | user_id={} by admin_id={}", user_id, admin_id)
        return UserResponse.model_validate(user)

    async def assign_role(
        self,
        user_id: uuid.UUID,
        data: AssignRoleRequest,
        *,
        admin_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> UserResponse:
        """Assign a role to a user (Admin only)."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        role = await self._user_repo.get_role_by_name(data.role_name.upper())
        if not role:
            raise BadRequestError(f"Role '{data.role_name}' does not exist")

        if user.has_role(role.name):
            raise ConflictError(f"User already has role '{role.name}'")

        await self._user_repo.assign_role(user, role)

        # Audit
        await self._audit.log(
            user_id=admin_id,
            action=AuditAction.ROLE_ASSIGNED.value,
            resource="users",
            resource_id=user_id,
            details={"role": role.name},
            ip_address=ip_address,
        )

        logger.info("Role '{}' assigned to user_id={}", role.name, user_id)
        return UserResponse.model_validate(user)

    async def remove_role(
        self,
        user_id: uuid.UUID,
        data: AssignRoleRequest,
        *,
        admin_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> UserResponse:
        """Remove a role from a user (Admin only)."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        role = await self._user_repo.get_role_by_name(data.role_name.upper())
        if not role:
            raise BadRequestError(f"Role '{data.role_name}' does not exist")

        if not user.has_role(role.name):
            raise BadRequestError(f"User does not have role '{role.name}'")

        await self._user_repo.remove_role(user, role)

        # Audit
        await self._audit.log(
            user_id=admin_id,
            action=AuditAction.ROLE_REMOVED.value,
            resource="users",
            resource_id=user_id,
            details={"role": role.name},
            ip_address=ip_address,
        )

        logger.info("Role '{}' removed from user_id={}", role.name, user_id)
        return UserResponse.model_validate(user)
