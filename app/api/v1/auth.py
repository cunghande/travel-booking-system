# ============================================================
# Travel Booking System — API Router: Xác thực (Auth)
# ============================================================
# Các endpoints: Đăng ký, Đăng nhập, Làm mới token và Xem hồ sơ cá nhân.
# ============================================================

from fastapi import APIRouter, Request

from app.application.dto.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.application.dto.user import UserResponse
from app.application.services.auth_service import AuthService
from app.core.dependencies import CurrentUser, DBConn, get_client_ip

router = APIRouter(prefix="/auth", tags=["Xác thực & Tài khoản"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Đăng ký tài khoản mới",
    description="Tạo tài khoản khách hàng (CUSTOMER). Mật khẩu được mã hóa an toàn bằng bcrypt.",
)
async def register(
    data: RegisterRequest,
    conn: DBConn,
    request: Request,
) -> UserResponse:
    service = AuthService(conn)
    return await service.register(data, ip_address=get_client_ip(request))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
    description="Xác thực qua email và mật khẩu. Trả về cặp JWT Access Token và Refresh Token.",
)
async def login(
    data: LoginRequest,
    conn: DBConn,
    request: Request,
) -> TokenResponse:
    service = AuthService(conn)
    return await service.login(data, ip_address=get_client_ip(request))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Làm mới Access Token",
    description="Cấp Access Token mới khi token cũ hết hạn bằng Refresh Token hợp lệ.",
)
async def refresh_token(
    data: RefreshRequest,
    conn: DBConn,
) -> TokenResponse:
    service = AuthService(conn)
    return await service.refresh_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Xem thông tin tài khoản hiện tại",
    description="Lấy hồ sơ cá nhân của người dùng đang đăng nhập dựa trên JWT Bearer token.",
)
async def get_me(
    current_user: CurrentUser,
    conn: DBConn,
) -> UserResponse:
    service = AuthService(conn)
    return await service.get_current_user(current_user["id"])
