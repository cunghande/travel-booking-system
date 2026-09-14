# ============================================================
# Travel Booking System — Dependency Injection
# ============================================================
# FastAPI dependencies for DB session, Redis, auth, RBAC.
# ============================================================

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.domain.entities.user import User
from app.infrastructure.db.session import get_db_session
from app.infrastructure.redis.client import get_redis
from app.infrastructure.repositories.user_repository import UserRepository

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Type aliases for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: DBSession,
) -> User:
    """
    Decode JWT token and return the authenticated user.

    Raises:
        UnauthorizedError: If token is invalid or user not found.
    """
    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    repo = UserRepository(session)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")

    return user


# Typed dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*role_names: str):
    """
    Dependency factory that enforces role-based access control.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles("ADMIN"))])
        async def admin_endpoint(): ...

        # Or inject the user:
        async def endpoint(user: AdminUser): ...
    """
    async def role_checker(current_user: CurrentUser) -> User:
        user_roles = {role.name for role in current_user.roles}
        required = set(role_names)

        if not user_roles.intersection(required):
            raise ForbiddenError(
                f"Requires one of roles: {', '.join(role_names)}"
            )
        return current_user

    return role_checker


AdminUser = Annotated[User, Depends(require_roles("ADMIN"))]
StaffUser = Annotated[User, Depends(require_roles("ADMIN", "STAFF"))]
CustomerUser = Annotated[User, Depends(require_roles("ADMIN", "STAFF", "CUSTOMER"))]

# Aliases for backwards compatibility
RequireAdmin = AdminUser
RequireStaff = StaffUser
RequireCustomer = CustomerUser


def get_client_ip(request: Request) -> str | None:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
