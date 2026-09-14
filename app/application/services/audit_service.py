# ============================================================
# Travel Booking System — Audit Service
# ============================================================

from __future__ import annotations

import uuid
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.audit_repository import AuditRepository


class AuditService:
    """Service for recording audit trail entries."""

    def __init__(self, session: AsyncSession):
        self._repo = AuditRepository(session)

    async def log(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource: str | None = None,
        resource_id: Any = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """
        Record an audit log entry.

        This should be called for sensitive actions:
        - User registration / login
        - Role assignment / removal
        - Tour creation / update / deletion
        - Booking operations
        - Payment operations
        """
        try:
            await self._repo.create(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=str(resource_id) if resource_id else None,
                details=details,
                ip_address=ip_address,
            )
            logger.debug(
                "Audit log | action={} resource={} resource_id={}",
                action,
                resource,
                resource_id,
            )
        except Exception as e:
            # Audit logging should never break the main operation
            logger.error("Failed to create audit log: {}", str(e))
