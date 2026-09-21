# ============================================================
# Travel Booking System — User Repository
# ============================================================
# Data access layer for users and roles.
# All DB logic isolated here — services never touch SQLAlchemy directly.
# ============================================================

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, func, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.user import Role, User, user_roles


class UserRepository:
    """Repository for User and Role data access."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # --------------- User CRUD ---------------

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get a user by ID with roles eagerly loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        """Get paginated list of users with total count."""
        stmt = select(User).options(selectinload(User.roles))

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        # Paginated results
        stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self._session.execute(stmt)
        users = list(result.scalars().all())

        return users, total

    async def create(self, user: User) -> User:
        """Create a new user."""
        self._session.add(user)
        await self._session.flush()
        return user

    async def update(self, user: User) -> User:
        """Update an existing user (session tracks changes)."""
        await self._session.flush()
        return user

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        stmt = select(func.count()).where(User.email == email)
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    # --------------- Role Operations ---------------

    async def get_role_by_name(self, name: str) -> Role | None:
        """Get a role by name."""
        stmt = select(Role).where(Role.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> Sequence[Role]:
        """Get all roles."""
        stmt = select(Role).order_by(Role.id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def assign_role(self, user: User, role: Role) -> None:
        """Assign a role to a user."""
        check = select(func.count()).select_from(user_roles).where(
            user_roles.c.user_id == user.id,
            user_roles.c.role_id == role.id,
        )
        exists = (await self._session.execute(check)).scalar() or 0
        if not exists:
            await self._session.execute(
                insert(user_roles).values(user_id=user.id, role_id=role.id)
            )
            await self._session.flush()

    async def remove_role(self, user: User, role: Role) -> None:
        """Remove a role from a user."""
        stmt = delete(user_roles).where(
            user_roles.c.user_id == user.id,
            user_roles.c.role_id == role.id,
        )
        await self._session.execute(stmt)
        await self._session.flush()
