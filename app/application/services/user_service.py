# ============================================================
# Travel Booking System — Service: Quản lý người dùng (User Service)
# ============================================================
# Tầng nghiệp vụ quản trị người dùng: Danh sách, phân quyền, cập nhật profile.
# Dành cho Quản trị viên (Admin) hoặc cập nhật tài khoản cá nhân.
# ============================================================

import uuid
from typing import Optional
import asyncpg
from loguru import logger

from app.application.dto.common import PaginatedResponse
from app.application.dto.user import (
    AssignRoleRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.application.services.audit_service import AuditService
from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.user_repository import UserRepository


def _to_user_response(data: dict) -> UserResponse:
    return UserResponse(
        id=data.get("user_id") or data.get("id"),
        email=data["email"],
        full_name=data["full_name"],
        phone_number=data.get("phone_number"),
        is_active=data["is_active"],
        roles=list(data.get("role_names") or data.get("roles") or []),
        created_at=data["created_at"],
    )


class UserService:
    """Nghiệp vụ quản lý thông tin và phân quyền người dùng."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self._user_repo = UserRepository(conn)
        self._audit = AuditService(conn)

    async def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[UserResponse]:
        """Lấy danh sách người dùng phân trang (Admin)."""
        skip = (page - 1) * page_size
        users, total = await self._user_repo.get_all(
            skip=skip,
            limit=page_size,
            is_active=is_active,
        )
        items = [_to_user_response(u) for u in users]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        """Lấy thông tin một người dùng theo ID."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return _to_user_response(user)

    async def update_profile(
        self,
        user_id: uuid.UUID,
        data: UserUpdateRequest,
    ) -> UserResponse:
        """Cập nhật thông tin tài khoản cá nhân."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        updated = await self._user_repo.update_profile(
            user_id=user_id,
            full_name=data.full_name,
            phone_number=data.phone_number,
        )
        # Giữ nguyên roles từ user hiện tại
        if updated:
            updated["role_names"] = user.get("role_names", [])

        return _to_user_response(updated or user)

    async def assign_role(
        self,
        user_id: uuid.UUID,
        data: AssignRoleRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> UserResponse:
        """Gán vai trò mới cho người dùng (Chỉ dành cho Admin)."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        result = await self._user_repo.assign_role(
            user_id=user_id,
            role_name=data.role_name,
            admin_id=admin_id,
        )

        logger.info("Admin {} đã gán vai trò {} cho user {}", admin_id, data.role_name, user_id)
        # Lấy lại thông tin user mới nhất
        refreshed = await self._user_repo.get_by_id(user_id)
        return _to_user_response(refreshed or user)
