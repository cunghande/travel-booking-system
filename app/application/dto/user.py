# ============================================================
# Travel Booking System — User DTOs
# ============================================================

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RoleResponse(BaseModel):
    """Role info response."""
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """User info response."""
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[RoleResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    """Update user profile request."""
    full_name: str | None = Field(None, min_length=2, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None


class AssignRoleRequest(BaseModel):
    """Assign/remove role request."""
    role_name: str = Field(..., description="Role name: ADMIN, STAFF, or CUSTOMER")
