# ============================================================
# Travel Booking System — Service: Nhật ký hệ thống (Audit Service)
# ============================================================
# Ghi nhật ký truy vết các hành động quan trọng để kiểm toán và bảo mật.
# ============================================================

import uuid
from typing import Any, Dict, Optional
import asyncpg
from loguru import logger

from app.infrastructure.repositories.audit_repository import AuditRepository


class AuditService:
    """Service ghi nhận audit trail cho toàn bộ hệ thống."""

    def __init__(self, conn: asyncpg.Connection):
        self._repo = AuditRepository(conn)

    async def log(
        self,
        *,
        user_id: Optional[uuid.UUID] = None,
        action: str,
        resource: Optional[str] = None,
        resource_id: Any = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Ghi một bản ghi nhật ký.
        Không bao giờ để lỗi audit log làm gián đoạn luồng nghiệp vụ chính.
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
                "Audit log: action={} resource={} resource_id={}",
                action,
                resource,
                resource_id,
            )
        except Exception as e:
            logger.error("Không thể ghi audit log: {}", str(e))
