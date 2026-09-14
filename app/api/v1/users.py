# ============================================================
# Travel Booking System — User Management API Routes
# ============================================================
# Admin-only endpoints for managing users and roles.
# ============================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Request

from app.application.dto.common import MessageResponse, PaginatedResponse
from app.application.dto.user import (
    AssignRoleRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.application.services.user_service import UserService
from app.core.dependencies import (
    AdminUser,
    CurrentUser,
    DBSession,
    get_client_ip,
)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users",
    description="Admin only. Returns paginated list of users.",
)
async def list_users(
    session: DBSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
) -> PaginatedResponse[UserResponse]:
    service = UserService(session)
    return await service.list_users(
        page=page,
        page_size=page_size,
        is_active=is_active,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Admin only. Get a specific user's details.",
)
async def get_user(
    user_id: uuid.UUID,
    session: DBSession,
    admin: AdminUser,
) -> UserResponse:
    service = UserService(session)
    return await service.get_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Admin only. Update user profile or activation status.",
)
async def update_user(
    user_id: uuid.UUID,
    data: UpdateUserRequest,
    session: DBSession,
    request: Request,
    admin: AdminUser,
) -> UserResponse:
    service = UserService(session)
    return await service.update_user(
        user_id,
        data,
        admin_id=admin.id,
        ip_address=get_client_ip(request),
    )


@router.post(
    "/{user_id}/roles",
    response_model=UserResponse,
    summary="Assign role to user",
    description="Admin only. Assign a role (ADMIN, STAFF, CUSTOMER) to a user.",
)
async def assign_role(
    user_id: uuid.UUID,
    data: AssignRoleRequest,
    session: DBSession,
    request: Request,
    admin: AdminUser,
) -> UserResponse:
    service = UserService(session)
    return await service.assign_role(
        user_id,
        data,
        admin_id=admin.id,
        ip_address=get_client_ip(request),
    )


@router.delete(
    "/{user_id}/roles",
    response_model=UserResponse,
    summary="Remove role from user",
    description="Admin only. Remove a role from a user.",
)
async def remove_role(
    user_id: uuid.UUID,
    data: AssignRoleRequest,
    session: DBSession,
    request: Request,
    admin: AdminUser,
) -> UserResponse:
    service = UserService(session)
    return await service.remove_role(
        user_id,
        data,
        admin_id=admin.id,
        ip_address=get_client_ip(request),
    )
