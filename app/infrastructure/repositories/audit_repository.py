# ============================================================
# Travel Booking System — Audit Log Repository
# ============================================================

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import AuditLog


class AuditRepository:
    """Repository for audit log data access."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=ip_address,
        )
        self._session.add(log)
        await self._session.flush()
        return log
