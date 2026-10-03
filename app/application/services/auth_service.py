# ============================================================
# Travel Booking System — Service: Xác thực (Auth Service)
# ============================================================
# Tầng nghiệp vụ xác thực người dùng: Đăng ký, Đăng nhập, Refresh Token.
# Sử dụng UserRepository qua asyncpg và Stored Procedures PostgreSQL.
# ============================================================

import uuid
from typing import Optional
import asyncpg
from jose import JWTError
from loguru import logger

from app.application.dto.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.application.dto.user import UserResponse
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.infrastructure.repositories.user_repository import UserRepository


def _to_user_response(data: dict) -> UserResponse:
    """Chuyển đổi record database sang UserResponse DTO."""
    return UserResponse(
        id=data.get("user_id") or data.get("id"),
        email=data["email"],
        full_name=data["full_name"],
        phone_number=data.get("phone_number"),
        is_active=data["is_active"],
        roles=list(data.get("role_names") or data.get("roles") or []),
        created_at=data["created_at"],
    )


class AuthService:
    """Nghiệp vụ xác thực người dùng."""

    def __init__(self, conn: asyncpg.Connection):
        """Khởi tạo service với connection asyncpg."""
        self._conn = conn
        self._user_repo = UserRepository(conn)

    async def register(
        self,
        data: RegisterRequest,
        ip_address: Optional[str] = None,
    ) -> UserResponse:
        """
        Đăng ký tài khoản người dùng mới với vai trò mặc định CUSTOMER.
        Mật khẩu được băm (hash) bằng bcrypt trước khi lưu qua Stored Procedure.
        """
        # Kiểm tra trước xem email đã tồn tại hay chưa
        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError(f"Email '{data.email}' đã được đăng ký trong hệ thống")

        hashed_pw = hash_password(data.password)

        try:
            user_data = await self._user_repo.create_user(
                email=data.email,
                hashed_password=hashed_pw,
                full_name=data.full_name,
                phone_number=getattr(data, "phone_number", None),
                ip_address=ip_address,
            )
        except asyncpg.UniqueViolationError:
            raise ConflictError(f"Email '{data.email}' đã được đăng ký trong hệ thống")

        logger.info("Đăng ký thành công tài khoản: {}", data.email)
        return _to_user_response(user_data)

    async def login(
        self,
        data: LoginRequest,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """
        Đăng nhập người dùng:
        1. Kiểm tra email có tồn tại không.
        2. Kiểm tra mật khẩu bcrypt.
        3. Kiểm tra trạng thái hoạt động (is_active).
        4. Ghi log đăng nhập.
        5. Sinh cặp JWT Access Token và Refresh Token.
        """
        user = await self._user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user["hashed_password"]):
            raise UnauthorizedError("Email hoặc mật khẩu không chính xác")

        if not user["is_active"]:
            raise UnauthorizedError("Tài khoản của bạn đã bị khóa hoặc ngừng kích hoạt")

        # Ghi nhật ký đăng nhập
        user_id = user["user_id"]
        await self._user_repo.log_login(user_id, ip_address)

        # Tạo token JWT
        role_list = list(user.get("role_names") or ["CUSTOMER"])
        access_token = create_access_token(subject=user_id, roles=role_list)
        refresh_token = create_refresh_token(subject=user_id)

        logger.info("Đăng nhập thành công: {} (vai trò: {})", data.email, role_list)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        """
        Làm mới Access Token bằng Refresh Token còn hạn.
        """
        try:
            payload = decode_token(refresh_token_str)
        except JWTError:
            raise UnauthorizedError("Refresh token không hợp lệ hoặc đã hết hạn")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Token không phải là refresh token hợp lệ")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedError("Dữ liệu trong token không hợp lệ")

        user = await self._user_repo.get_by_id(uuid.UUID(user_id_str))
        if not user or not user["is_active"]:
            raise UnauthorizedError("Người dùng không tồn tại hoặc tài khoản đã bị vô hiệu hóa")

        role_list = list(user.get("role_names") or ["CUSTOMER"])
        new_access = create_access_token(subject=user["user_id"], roles=role_list)
        new_refresh = create_refresh_token(subject=user["user_id"])

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
        )

    async def get_current_user(self, user_id: uuid.UUID) -> UserResponse:
        """Lấy thông tin người dùng hiện tại theo UUID."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("Không tìm thấy thông tin tài khoản")
        return _to_user_response(user)
