# ============================================================
# Travel Booking System — Test Configuration & Fixtures
# ============================================================

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import hash_password
from app.domain.entities.user import Role, User
from app.domain.value_objects.enums import RoleName
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import get_db_session
from app.main import app

# --------------- Test Database Engine ---------------

TEST_DB_URL = settings.DATABASE_URL

test_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool, echo=False)
test_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --------------- Fixtures ---------------


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables once for the test session if DB is reachable."""
    try:
        async with test_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

        # Seed roles
        async with test_session_factory() as session:
            for role_name in RoleName:
                role = Role(name=role_name.value, description=f"{role_name.value} role")
                session.add(role)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
        db_ready = True
    except Exception:
        db_ready = False

    yield db_ready

    if db_ready:
        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await test_engine.dispose()
        except Exception:
            pass


@pytest_asyncio.fixture
async def db_session(setup_database: bool) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    if not setup_database:
        pytest.skip("PostgreSQL test database not available. Start Docker/PostgreSQL to run integration tests.")
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with overridden DB session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# --------------- Factory Fixtures ---------------

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with CUSTOMER role."""
    from sqlalchemy import select

    stmt = select(Role).where(Role.name == RoleName.CUSTOMER.value)
    result = await db_session.execute(stmt)
    role = result.scalar_one_or_none()

    user = User(
        email=f"testuser_{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test User",
        hashed_password=hash_password("Test@12345"),
        is_active=True,
    )
    if role:
        user.roles = [role]
    db_session.add(user)
    await db_session.flush()

    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    from sqlalchemy import select

    stmt = select(Role).where(Role.name == RoleName.ADMIN.value)
    result = await db_session.execute(stmt)
    role = result.scalar_one_or_none()

    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        full_name="Admin User",
        hashed_password=hash_password("Admin@12345"),
        is_active=True,
    )
    if role:
        user.roles = [role]
    db_session.add(user)
    await db_session.flush()

    return user
