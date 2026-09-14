# ============================================================
# Travel Booking System — Auth API Routes
# ============================================================
# Thin API layer — delegates all logic to AuthService.
# ============================================================

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.application.dto.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    TokenResponse,
)
from app.application.dto.user import UserResponse
from app.application.services.auth_service import AuthService
from app.core.dependencies import CurrentUser, DBSession, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new user account with CUSTOMER role.",
)
async def register(
    data: RegisterRequest,
    session: DBSession,
    request: Request,
) -> UserResponse:
    service = AuthService(session)
    return await service.register(data, ip_address=get_client_ip(request))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password. Returns JWT tokens.",
)
async def login(
    data: LoginRequest,
    session: DBSession,
    request: Request,
) -> TokenResponse:
    service = AuthService(session)
    return await service.login(data, ip_address=get_client_ip(request))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(
    data: RefreshRequest,
    session: DBSession,
) -> TokenResponse:
    service = AuthService(session)
    return await service.refresh_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
)
async def get_me(
    current_user: CurrentUser,
    session: DBSession,
) -> UserResponse:
    service = AuthService(session)
    return await service.get_current_user(current_user.id)
