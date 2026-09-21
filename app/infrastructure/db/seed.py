# ============================================================
# Travel Booking System — Database Seeder
# ============================================================
# Seeds initial data: roles + admin user.
# Run after migration: python -m app.infrastructure.db.seed
# ============================================================

from __future__ import annotations

import asyncio
import sys

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.domain.entities.user import Role, User, user_roles
from app.domain.value_objects.enums import RoleName
from app.infrastructure.db.session import async_session_factory


async def seed_roles(session: AsyncSession) -> dict[str, Role]:
    """Ensure all roles exist."""
    roles = {}
    for role_name in RoleName:
        stmt = select(Role).where(Role.name == role_name.value)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_name.value, description=f"{role_name.value} role")
            session.add(role)
            logger.info("Created role: {}", role_name.value)
        roles[role_name.value] = role
    await session.flush()
    return roles


async def seed_admin(session: AsyncSession, roles: dict[str, Role]) -> None:
    """Ensure admin user exists."""
    stmt = select(User).where(User.email == settings.ADMIN_EMAIL)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        admin_role = roles.get(RoleName.ADMIN.value)
        admin = User(
            email=settings.ADMIN_EMAIL,
            full_name=settings.ADMIN_FULL_NAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            is_active=True,
        )
        if admin_role:
            admin.roles = [admin_role]
        session.add(admin)
        await session.flush()

        logger.info("Created admin user: {}", settings.ADMIN_EMAIL)
    else:
        logger.info("Admin user already exists: {}", settings.ADMIN_EMAIL)


async def run_seed() -> None:
    """Run all seeders."""
    logger.info("🌱 Starting database seeding...")
    async with async_session_factory() as session:
        try:
            roles = await seed_roles(session)
            await seed_admin(session, roles)
            await session.commit()
            logger.info("✅ Database seeding completed successfully")
        except Exception as e:
            await session.rollback()
            logger.error("❌ Seeding failed: {}", str(e))
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
