import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
import aiomysql
from common.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from services.auth_service.database import get_db
from services.auth_service.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

# Khởi tạo Router cho Auth Service
router = APIRouter(prefix="/auth", tags=["Xác thực & Tài khoản"])

# xây dựng api đăng ký tài khoản (POST /auth/register)
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới"
)
