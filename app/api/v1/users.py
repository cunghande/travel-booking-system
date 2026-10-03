# ============================================================
# Travel Booking System — API Router: Quản trị người dùng (Users)
# ============================================================
# Các endpoints dành cho Quản trị viên (Admin) và Cập nhật hồ sơ cá nhân.
# ============================================================

import uuid
from typing import Optional
from fastapi import APIRouter, Query, Request

from app.application.dto.common import PaginatedResponse
from app.application.dto.user import (
    AssignRoleRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.application.services.user_service import UserService
from app.core.dependencies import AdminUser, CurrentUser, DBConn, get_client_ip

router = APIRouter(prefix="/users", tags=["Quản trị người dùng"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="Danh sách người dùng (Admin)",
    description="Lấy danh sách tài khoản phân trang, lọc theo trạng thái kích hoạt.",
)
async def list_users(
    conn: DBConn,
    admin: AdminUser,
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
) -> PaginatedResponse[UserResponse]:
    service = UserService(conn)
    return await service.list_users(
        page=page,
        page_size=page_size,
        is_active=is_active,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Xem chi tiết người dùng (Admin)",
    description="Tra cứu chi tiết một tài khoản bằng UUID.",
)
async def get_user(
    user_id: uuid.UUID,
    conn: DBConn,
    admin: AdminUser,
) -> UserResponse:
    service = UserService(conn)
    return await service.get_user(user_id)


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Cập nhật hồ sơ cá nhân",
    description="Người dùng tự cập nhật họ tên, số điện thoại của mình.",
)
async def update_my_profile(
    data: UserUpdateRequest,
    conn: DBConn,
    current_user: CurrentUser,
) -> UserResponse:
    service = UserService(conn)
    return await service.update_profile(current_user["id"], data)


@router.post(
    "/{user_id}/roles",
    response_model=UserResponse,
    summary="Gán vai trò cho người dùng (Admin)",
    description="Quản trị viên gán thêm quyền (ADMIN, STAFF, CUSTOMER) cho tài khoản.",
)
async def assign_role(
    user_id: uuid.UUID,
    data: AssignRoleRequest,
    conn: DBConn,
    request: Request,
    admin: AdminUser,
) -> UserResponse:
    service = UserService(conn)
    return await service.assign_role(
        user_id,
        data,
        admin_id=admin["id"],
        ip_address=get_client_ip(request),
    )
